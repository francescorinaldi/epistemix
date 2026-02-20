"""Dual-agent epistemic audit system.

Two agents with different axiom weightings independently audit the same topic:
- Agent α (institutional): weights languages, institutions, schools, publications
- Agent β (theoretical): weights theories, disciplines, temporal evolution

An Arbiter compares their reports, identifies agreements and discrepancies,
and promotes disagreements to "known unknowns" — areas where our epistemic
coverage is provably incomplete.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from epistemix.connector import BaseConnector
from epistemix.core import EpistemicEngine
from epistemix.meta_axioms import META_AXIOMS
from epistemix.models import (
    Anomaly,
    AnomalyType,
    CoverageScore,
    Finding,
    Postulate,
    PostulateStatus,
    ResearchState,
    Severity,
)


@dataclass(frozen=True)
class AgentPerspective:
    """Axiom weighting configuration for an agent."""
    name: str
    description: str
    # meta_axiom_id → weight (0.0 to 2.0, default 1.0)
    weights: dict[str, float] = field(default_factory=dict)

    def weight_for(self, axiom_id: str) -> float:
        return self.weights.get(axiom_id, 1.0)


# Pre-defined perspectives
ALPHA_PERSPECTIVE = AgentPerspective(
    name="alpha",
    description="Institutional focus: languages, institutions, schools, publications",
    weights={
        "MA-01": 1.5,  # Language — high weight
        "MA-02": 1.5,  # Institution — high weight
        "MA-03": 0.7,  # Theory — lower
        "MA-04": 1.5,  # School — high weight
        "MA-05": 0.7,  # Discipline — lower
        "MA-06": 1.5,  # Publication — high weight
        "MA-07": 0.7,  # Temporal — lower
    },
)

BETA_PERSPECTIVE = AgentPerspective(
    name="beta",
    description="Theoretical focus: theories, disciplines, temporal evolution",
    weights={
        "MA-01": 0.7,  # Language — lower
        "MA-02": 0.7,  # Institution — lower
        "MA-03": 1.5,  # Theory — high weight
        "MA-04": 0.7,  # School — lower
        "MA-05": 1.5,  # Discipline — high weight
        "MA-06": 0.7,  # Publication — lower
        "MA-07": 1.5,  # Temporal — high weight
    },
)


@dataclass
class AgentReport:
    """Report from a single agent's audit."""
    agent_name: str
    perspective: AgentPerspective
    coverage: CoverageScore
    findings: list[Finding] = field(default_factory=list)
    postulates: list[Postulate] = field(default_factory=list)
    anomalies: list[Anomaly] = field(default_factory=list)
    coverage_history: list[CoverageScore] = field(default_factory=list)


@dataclass
class EpistemicAgent:
    """An agent that runs the audit with a specific perspective weighting."""

    perspective: AgentPerspective
    engine: EpistemicEngine

    @classmethod
    def create(
        cls,
        perspective: AgentPerspective,
        connector: BaseConnector,
        topic: str,
        country: str,
        discipline: str,
    ) -> EpistemicAgent:
        state = ResearchState(topic=topic, country=country, discipline=discipline)
        engine = EpistemicEngine(connector=connector, state=state)
        return cls(perspective=perspective, engine=engine)

    def run(self, max_cycles: int = 4) -> AgentReport:
        """Run the full audit and return a report."""
        coverage_history = self.engine.run_all_cycles(max_cycles=max_cycles)

        # Apply perspective weighting to anomaly severity
        self._weight_anomalies()

        return AgentReport(
            agent_name=self.perspective.name,
            perspective=self.perspective,
            coverage=self.engine.state.current_coverage(),
            findings=list(self.engine.state.findings),
            postulates=list(self.engine.state.postulates),
            anomalies=list(self.engine.state.anomalies),
            coverage_history=coverage_history,
        )

    def _weight_anomalies(self) -> None:
        """Adjust anomaly significance based on perspective weights.

        Anomalies from highly weighted axioms get promoted in severity.
        Anomalies from low-weighted axioms remain but aren't promoted.
        """
        axiom_type_map: dict[AnomalyType, str] = {
            AnomalyType.LANGUAGE_GAP: "MA-01",
            AnomalyType.INSTITUTION_GAP: "MA-02",
            AnomalyType.THEORY_GAP: "MA-03",
            AnomalyType.SCHOOL_GAP: "MA-04",
            AnomalyType.DISCIPLINE_GAP: "MA-05",
            AnomalyType.PUBLICATION_GAP: "MA-06",
            AnomalyType.TEMPORAL_GAP: "MA-07",
        }

        for anomaly in self.engine.state.anomalies:
            axiom_id = axiom_type_map.get(anomaly.anomaly_type)
            if axiom_id:
                weight = self.perspective.weight_for(axiom_id)
                if weight >= 1.5 and anomaly.severity == Severity.MEDIUM:
                    anomaly.severity = Severity.HIGH


@dataclass
class ArbiterResult:
    """Result of the arbiter's comparison of two agent reports."""
    agreements: list[str] = field(default_factory=list)
    discrepancies: list[str] = field(default_factory=list)
    known_unknowns: list[Anomaly] = field(default_factory=list)
    combined_coverage: CoverageScore | None = None
    blindness_gap: float = 0.0


class Arbiter:
    """Compares two agent reports and identifies epistemic blind spots.

    The arbiter's job is to find where the agents disagree — those
    disagreements represent genuine epistemic uncertainty, not just
    missing data.
    """

    def compare(self, alpha: AgentReport, beta: AgentReport) -> ArbiterResult:
        result = ArbiterResult()

        # Compare findings
        alpha_findings = set(alpha.findings)
        beta_findings = set(beta.findings)
        shared = alpha_findings & beta_findings
        alpha_only = alpha_findings - beta_findings
        beta_only = beta_findings - alpha_findings

        result.agreements.append(
            f"{len(shared)} findings agreed upon by both agents"
        )
        if alpha_only:
            result.discrepancies.append(
                f"Agent α found {len(alpha_only)} entities not found by β: "
                f"{', '.join(f.name for f in sorted(alpha_only, key=lambda x: x.name)[:5])}"
            )
        if beta_only:
            result.discrepancies.append(
                f"Agent β found {len(beta_only)} entities not found by α: "
                f"{', '.join(f.name for f in sorted(beta_only, key=lambda x: x.name)[:5])}"
            )

        # Compare anomalies
        alpha_anomaly_types = {a.anomaly_type for a in alpha.anomalies}
        beta_anomaly_types = {a.anomaly_type for a in beta.anomalies}
        shared_types = alpha_anomaly_types & beta_anomaly_types
        alpha_only_types = alpha_anomaly_types - beta_anomaly_types
        beta_only_types = beta_anomaly_types - alpha_anomaly_types

        if shared_types:
            result.agreements.append(
                f"Both agents flagged: {', '.join(t.value for t in shared_types)}"
            )

        # Discrepancies in anomaly detection become known unknowns
        for anomaly in beta.anomalies:
            if anomaly.anomaly_type in beta_only_types:
                known_unknown = Anomaly(
                    id=f"A-KU-{anomaly.id}",
                    anomaly_type=anomaly.anomaly_type,
                    severity=Severity.HIGH,
                    description=(
                        f"[Known Unknown] Agent β detected but α missed: "
                        f"{anomaly.description}"
                    ),
                    suggested_queries=anomaly.suggested_queries,
                )
                result.known_unknowns.append(known_unknown)

        for anomaly in alpha.anomalies:
            if anomaly.anomaly_type in alpha_only_types:
                known_unknown = Anomaly(
                    id=f"A-KU-{anomaly.id}",
                    anomaly_type=anomaly.anomaly_type,
                    severity=Severity.HIGH,
                    description=(
                        f"[Known Unknown] Agent α detected but β missed: "
                        f"{anomaly.description}"
                    ),
                    suggested_queries=anomaly.suggested_queries,
                )
                result.known_unknowns.append(known_unknown)

        # Combined coverage = min(α, β)
        alpha_pct = alpha.coverage.percentage
        beta_pct = beta.coverage.percentage
        min_pct = min(alpha_pct, beta_pct)

        combined_total = max(alpha.coverage.total, beta.coverage.total)
        combined_confirmed = int(combined_total * min_pct / 100) if combined_total > 0 else 0
        total_anomalies = len(set(alpha.anomalies) | set(beta.anomalies))

        result.combined_coverage = CoverageScore(
            confirmed=combined_confirmed,
            total=combined_total,
            anomaly_count=total_anomalies,
        )

        # Blindness gap = difference between best single-agent and combined
        max_single = max(alpha_pct, beta_pct)
        result.blindness_gap = round(max_single - min_pct, 1)

        return result


@dataclass
class MultiAgentSystem:
    """Orchestrates the full dual-agent audit."""

    connector: BaseConnector
    topic: str
    country: str
    discipline: str
    max_cycles: int = 4

    def run(self) -> dict:
        """Run both agents and the arbiter, returning the complete result."""
        # Create and run Agent α
        agent_alpha = EpistemicAgent.create(
            perspective=ALPHA_PERSPECTIVE,
            connector=self.connector,
            topic=self.topic,
            country=self.country,
            discipline=self.discipline,
        )
        alpha_report = agent_alpha.run(max_cycles=self.max_cycles)

        # Create and run Agent β
        agent_beta = EpistemicAgent.create(
            perspective=BETA_PERSPECTIVE,
            connector=self.connector,
            topic=self.topic,
            country=self.country,
            discipline=self.discipline,
        )
        beta_report = agent_beta.run(max_cycles=self.max_cycles)

        # Arbiter comparison
        arbiter = Arbiter()
        arbiter_result = arbiter.compare(alpha_report, beta_report)

        return {
            "alpha": {
                "coverage": alpha_report.coverage.percentage,
                "findings": len(alpha_report.findings),
                "anomalies": len(alpha_report.anomalies),
                "coverage_history": [
                    {"cycle": c.cycle, "percentage": c.percentage}
                    for c in alpha_report.coverage_history
                ],
            },
            "beta": {
                "coverage": beta_report.coverage.percentage,
                "findings": len(beta_report.findings),
                "anomalies": len(beta_report.anomalies),
                "coverage_history": [
                    {"cycle": c.cycle, "percentage": c.percentage}
                    for c in beta_report.coverage_history
                ],
            },
            "combined": {
                "coverage": arbiter_result.combined_coverage.percentage
                if arbiter_result.combined_coverage
                else 0,
                "blindness_gap": arbiter_result.blindness_gap,
                "total_anomalies": arbiter_result.combined_coverage.anomaly_count
                if arbiter_result.combined_coverage
                else 0,
                "known_unknowns": len(arbiter_result.known_unknowns),
            },
            "agreements": arbiter_result.agreements,
            "discrepancies": arbiter_result.discrepancies,
            "known_unknowns": [
                {
                    "type": ku.anomaly_type.value,
                    "severity": ku.severity.value,
                    "description": ku.description,
                }
                for ku in arbiter_result.known_unknowns
            ],
        }
