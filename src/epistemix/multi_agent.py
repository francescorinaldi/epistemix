"""Dual-agent epistemic audit system.

Based on the founder's v2 design with separate agent classes:
  - AgentInstitutional (Alpha): institutions, traditions, geographic coverage
  - AgentTheoretical (Beta): theories, evidence, argumentation
  - Arbiter: compares reports, finds discrepancies (known unknowns)

Each agent independently derives expectations, satisfies them from findings,
detects anomalies, and produces a coverage score. The Arbiter then compares
the two reports: where they DISAGREE reveals blind spots that no single
perspective would catch.
"""

from __future__ import annotations

from typing import Any

from epistemix.models import (
    AgentReport,
    Anomaly,
    Discrepancy,
    Expectation,
    Finding,
    GapType,
    Severity,
)
from epistemix.core import DynamicPostulates
from epistemix.knowledge import GEOGRAPHIC_LINGUISTIC


# ============================================================
# AGENT ALPHA — INSTITUTIONAL
# ============================================================

class AgentInstitutional:
    """Agent Alpha: focuses on institutions, traditions, geographic coverage.

    Blind spots by design: cannot detect theories with weak evidence
    or single advocates.
    """

    NAME = "Agent \u03b1 (Institutional)"
    FOCUS = "institutions, traditions, geographic coverage"

    def __init__(self, postulates: DynamicPostulates) -> None:
        self.postulates = postulates

    def audit(self, findings: list[Finding]) -> AgentReport:
        """Run the institutional audit."""
        report = AgentReport(
            agent_name=self.NAME,
            agent_focus=self.FOCUS,
        )

        report.expectations = self._derive_expectations(findings)
        self._satisfy(report.expectations, findings)
        report.anomalies = self._find_anomalies(findings)
        report.coverage_score = self._score(report)
        return report

    def _derive_expectations(self, findings: list[Finding]) -> list[Expectation]:
        """Derive institutional expectations."""
        expectations: list[Expectation] = []

        # One expectation per institution found
        institutions: set[str] = set()
        for f in findings:
            if f.institution:
                institutions.add(f.institution)
            for entity in f.entities_mentioned:
                lower = entity.lower()
                for kw in ("university", "museum", "ministry", "institute", "school"):
                    if kw in lower:
                        institutions.add(entity)
                        break

        for inst in institutions:
            expectations.append(Expectation(
                description=f"Publications from '{inst}' reviewed",
                gap_type=GapType.INSTITUTIONAL,
                severity_if_unmet=Severity.MEDIUM,
            ))

        # Geographic-linguistic completeness
        geo = GEOGRAPHIC_LINGUISTIC.get(self.postulates.country, {})
        for lang in geo.get("primary_languages", []):
            expectations.append(Expectation(
                description=f"Sources in '{lang}' language found",
                gap_type=GapType.LINGUISTIC,
                severity_if_unmet=Severity.HIGH,
            ))
        for lang, tradition in geo.get("foreign_traditions", {}).items():
            expectations.append(Expectation(
                description=f"Sources from {tradition} ({lang}) checked",
                gap_type=GapType.INSTITUTIONAL,
                severity_if_unmet=Severity.MEDIUM,
            ))

        # Diversity expectations
        expectations.append(Expectation(
            description="Scholars from at least 2 different institutions",
            gap_type=GapType.INSTITUTIONAL,
            severity_if_unmet=Severity.MEDIUM,
        ))
        expectations.append(Expectation(
            description="At least 3 distinct institutions represented",
            gap_type=GapType.INSTITUTIONAL,
            severity_if_unmet=Severity.MEDIUM,
        ))

        return expectations

    def _satisfy(
        self, expectations: list[Expectation], findings: list[Finding]
    ) -> None:
        """Check which expectations are met."""
        langs = set(f.language for f in findings)
        institutions = set(
            f.institution.lower() for f in findings if f.institution
        )

        for exp in expectations:
            desc_lower = exp.description.lower()

            # Language match
            for lang in langs:
                if f"'{lang}'" in desc_lower:
                    exp.satisfy(f"Found sources in {lang}")
                    break

            if exp.met:
                continue

            # Institution match
            for inst in institutions:
                if inst in desc_lower:
                    exp.satisfy(f"Found publications from {inst}")
                    break

            if exp.met:
                continue

            # Diversity: "3 distinct"
            if "3 distinct" in desc_lower and len(institutions) >= 3:
                exp.satisfy(f"{len(institutions)} institutions found")

            # Diversity: "2 different"
            if "2 different" in desc_lower and len(institutions) >= 2:
                exp.satisfy(f"{len(institutions)} institutions found")

    def _find_anomalies(self, findings: list[Finding]) -> list[Anomaly]:
        """Detect institutional anomalies."""
        anomalies: list[Anomaly] = []

        # Institutional concentration
        if len(findings) >= 4:
            inst_counts: dict[str, int] = {}
            for f in findings:
                if f.institution:
                    key = f.institution.lower()
                    inst_counts[key] = inst_counts.get(key, 0) + 1

            for inst, count in inst_counts.items():
                if count / len(findings) > 0.5:
                    anomalies.append(Anomaly(
                        description=(
                            f"Institutional concentration: '{inst}' "
                            f"accounts for {count}/{len(findings)} findings"
                        ),
                        gap_type=GapType.INSTITUTIONAL,
                        severity=Severity.MEDIUM,
                        recommendation="Search for findings from other institutions",
                    ))

        # Geographic clustering
        if len(findings) >= 5:
            countries: set[str] = set()
            for f in findings:
                inst_lower = (f.institution or "").lower()
                if any(kw in inst_lower for kw in ("greece", "greek", "hellenic")):
                    countries.add("Greece")
                elif any(kw in inst_lower for kw in ("british", "oxford", "cambridge", "london")):
                    countries.add("Anglophone")
                elif any(kw in inst_lower for kw in ("french", "france", "paris")):
                    countries.add("France")
                elif any(kw in inst_lower for kw in ("german", "deutsch")):
                    countries.add("Germany")
                elif any(kw in inst_lower for kw in ("italian", "italia", "rome", "roma")):
                    countries.add("Italy")
                elif f.institution:
                    countries.add("Other")

            if len(countries) <= 1 and countries:
                anomalies.append(Anomaly(
                    description=(
                        f"Geographic clustering: all findings from "
                        f"{next(iter(countries))} academic tradition"
                    ),
                    gap_type=GapType.GEOGRAPHIC,
                    severity=Severity.HIGH,
                    recommendation="Search for findings from other academic traditions",
                ))

        return anomalies

    def _score(self, report: AgentReport) -> float:
        """Calculate coverage score."""
        total = len(report.expectations)
        if total == 0:
            return 0.0
        met = sum(1 for e in report.expectations if e.met)
        score = (met / total) * 100 - (len(report.anomalies) * 5)
        return max(score, 0.0)


# ============================================================
# AGENT BETA — THEORETICAL
# ============================================================

class AgentTheoretical:
    """Agent Beta: focuses on theories, evidence, argumentation.

    Blind spots by design: cannot detect institutional monoculture
    or geographic bias.
    """

    NAME = "Agent \u03b2 (Theoretical)"
    FOCUS = "theories, evidence, argumentation"

    def __init__(self, postulates: DynamicPostulates) -> None:
        self.postulates = postulates

    def audit(self, findings: list[Finding]) -> AgentReport:
        """Run the theoretical audit."""
        report = AgentReport(
            agent_name=self.NAME,
            agent_focus=self.FOCUS,
        )

        report.expectations = self._derive_expectations(findings)
        self._satisfy(report.expectations, findings)
        report.anomalies = self._find_anomalies(findings)
        report.coverage_score = self._score(report)
        return report

    def _derive_expectations(self, findings: list[Finding]) -> list[Expectation]:
        """Derive theoretical expectations."""
        expectations: list[Expectation] = []

        # Peer-reviewed source per theory
        theories: set[str] = set()
        for f in findings:
            if f.theory_supported:
                theories.add(f.theory_supported)

        for theory in theories:
            expectations.append(Expectation(
                description=f"Peer-reviewed source for theory: {theory}",
                gap_type=GapType.THEORY_UNSOURCED,
                severity_if_unmet=Severity.HIGH,
            ))
            # Counter-argument for each theory
            expectations.append(Expectation(
                description=f"Counter-argument or critique for theory: {theory}",
                gap_type=GapType.VOICE,
                severity_if_unmet=Severity.MEDIUM,
            ))

        # Evidence type diversity
        expectations.append(Expectation(
            description="Archaeological evidence sources found",
            gap_type=GapType.SOURCE_TYPE,
            severity_if_unmet=Severity.MEDIUM,
        ))
        expectations.append(Expectation(
            description="Historical/literary evidence sources found",
            gap_type=GapType.SOURCE_TYPE,
            severity_if_unmet=Severity.MEDIUM,
        ))
        expectations.append(Expectation(
            description="Scientific/technical evidence sources found",
            gap_type=GapType.SOURCE_TYPE,
            severity_if_unmet=Severity.MEDIUM,
        ))

        # Comparative study
        if len(theories) >= 2:
            expectations.append(Expectation(
                description="Comparative study reviewing multiple theories",
                gap_type=GapType.SOURCE_TYPE,
                severity_if_unmet=Severity.MEDIUM,
            ))

        return expectations

    def _satisfy(
        self, expectations: list[Expectation], findings: list[Finding]
    ) -> None:
        """Check which expectations are met."""
        # Build lookup structures
        peer_reviewed_theories: set[str] = set()
        has_archaeological = False
        has_historical = False
        has_scientific = False
        has_comparative = False

        for f in findings:
            text = f"{f.source} {f.theory_supported}".lower()
            if f.theory_supported and f.source_type in (
                "peer_reviewed", "peer-reviewed"
            ):
                peer_reviewed_theories.add(f.theory_supported.lower())

            if any(kw in text for kw in (
                "excavation", "artifact", "archaeological", "stratigraphy"
            )):
                has_archaeological = True
            if any(kw in text for kw in (
                "historical", "literary", "ancient source", "chronicle"
            )):
                has_historical = True
            if any(kw in text for kw in (
                "dna", "scientific", "laboratory", "isotope", "radiocarbon"
            )):
                has_scientific = True
            if any(kw in text for kw in (
                "comparative", "review", "synthesis", "meta-analysis"
            )):
                has_comparative = True

        theories = set(
            f.theory_supported.lower()
            for f in findings if f.theory_supported
        )

        for exp in expectations:
            if exp.met:
                continue

            desc_lower = exp.description.lower()

            # Peer-reviewed match
            if exp.gap_type == GapType.THEORY_UNSOURCED:
                for theory in peer_reviewed_theories:
                    theory_words = {w for w in theory.split() if len(w) > 4}
                    desc_words = {w for w in desc_lower.split() if len(w) > 4}
                    if theory_words & desc_words:
                        exp.satisfy(f"Peer-reviewed source: {theory}")
                        break

            # Counter-argument: if a different theory exists, count it
            elif exp.gap_type == GapType.VOICE and "counter-argument" in desc_lower:
                for theory in theories:
                    if theory not in desc_lower:
                        exp.satisfy(
                            f"Alternative theory exists: {theory}"
                        )
                        break

            # Evidence types
            elif exp.gap_type == GapType.SOURCE_TYPE:
                if "archaeological" in desc_lower and has_archaeological:
                    exp.satisfy("Archaeological evidence found")
                elif "historical" in desc_lower and has_historical:
                    exp.satisfy("Historical/literary evidence found")
                elif "scientific" in desc_lower and has_scientific:
                    exp.satisfy("Scientific/technical evidence found")
                elif "comparative" in desc_lower and has_comparative:
                    exp.satisfy("Comparative study found")

    def _find_anomalies(self, findings: list[Finding]) -> list[Anomaly]:
        """Detect theoretical anomalies."""
        anomalies: list[Anomaly] = []

        # Single-evidence theories
        theory_types: dict[str, set[str]] = {}
        for f in findings:
            if f.theory_supported:
                key = f.theory_supported.lower()
                theory_types.setdefault(key, set())
                if f.source_type:
                    theory_types[key].add(f.source_type)

        for theory, types in theory_types.items():
            if len(types) == 1:
                anomalies.append(Anomaly(
                    description=(
                        f"Single-evidence theory: '{theory}' supported "
                        f"only by {next(iter(types))} sources"
                    ),
                    gap_type=GapType.SOURCE_TYPE,
                    severity=Severity.MEDIUM,
                    recommendation=(
                        "Find additional evidence types for this theory"
                    ),
                ))

        # Single-advocate theories
        theory_authors: dict[str, set[str]] = {}
        for f in findings:
            if f.theory_supported and f.author:
                key = f.theory_supported.lower()
                theory_authors.setdefault(key, set()).add(f.author.lower())

        for theory, authors in theory_authors.items():
            if len(authors) == 1:
                anomalies.append(Anomaly(
                    description=(
                        f"Single-advocate theory: '{theory}' supported "
                        f"only by {next(iter(authors))}"
                    ),
                    gap_type=GapType.VOICE,
                    severity=Severity.MEDIUM,
                    recommendation="Find additional scholars supporting this theory",
                ))

        return anomalies

    def _score(self, report: AgentReport) -> float:
        """Calculate coverage score."""
        total = len(report.expectations)
        if total == 0:
            return 0.0
        met = sum(1 for e in report.expectations if e.met)
        score = (met / total) * 100 - (len(report.anomalies) * 5)
        return max(score, 0.0)


# ============================================================
# ARBITER
# ============================================================

class Arbiter:
    """Compares two agent reports and identifies discrepancies.

    Discrepancies = gaps found by one agent but missed by the other.
    These are the most valuable output: proven blind spots.
    """

    def __init__(
        self, report_alpha: AgentReport, report_beta: AgentReport
    ) -> None:
        self.alpha = report_alpha
        self.beta = report_beta
        self.discrepancies: list[Discrepancy] = []
        self.combined_anomalies: list[Anomaly] = []

    def compare(self) -> list[Discrepancy]:
        """Compare reports and find discrepancies."""
        self.discrepancies = []

        # Alpha's anomalies not found by Beta
        for anomaly in self.alpha.anomalies:
            if not self._has_similar(anomaly, self.beta.anomalies):
                self.discrepancies.append(Discrepancy(
                    anomaly=anomaly,
                    found_by=self.alpha.agent_name,
                    missed_by=self.beta.agent_name,
                    significance=(
                        "Agent Beta's theoretical focus missed this "
                        "institutional gap"
                    ),
                ))

        # Beta's anomalies not found by Alpha
        for anomaly in self.beta.anomalies:
            if not self._has_similar(anomaly, self.alpha.anomalies):
                self.discrepancies.append(Discrepancy(
                    anomaly=anomaly,
                    found_by=self.beta.agent_name,
                    missed_by=self.alpha.agent_name,
                    significance=(
                        "Agent Alpha's institutional focus missed this "
                        "theoretical gap"
                    ),
                ))

        # Combined anomalies (deduplicated union)
        seen: set[str] = set()
        for anomaly in self.alpha.anomalies + self.beta.anomalies:
            key = f"{anomaly.gap_type.value}:{anomaly.description[:60]}"
            if key not in seen:
                seen.add(key)
                self.combined_anomalies.append(anomaly)

        return self.discrepancies

    def _has_similar(
        self, anomaly: Anomaly, others: list[Anomaly]
    ) -> bool:
        """Check if a similar anomaly exists in the other list.

        Two anomalies are similar if:
        1. Same gap_type
        2. Description shares >= 2 significant words (len > 4)
        """
        for other in others:
            if anomaly.gap_type != other.gap_type:
                continue
            words_a = {
                w for w in anomaly.description.lower().split()
                if len(w) > 4
            }
            words_b = {
                w for w in other.description.lower().split()
                if len(w) > 4
            }
            if len(words_a & words_b) >= 2:
                return True
        return False

    def combined_score(self) -> float:
        """Combined coverage score with discrepancy penalty."""
        avg = (self.alpha.coverage_score + self.beta.coverage_score) / 2
        penalty = len(self.discrepancies) * 3
        return max(avg - penalty, 0.0)

    def report(self) -> str:
        """Generate human-readable arbiter report."""
        lines: list[str] = []
        lines.append("=" * 60)
        lines.append("MULTI-AGENT ARBITER REPORT")
        lines.append("=" * 60)

        # Per-agent summary
        for agent in (self.alpha, self.beta):
            met = sum(1 for e in agent.expectations if e.met)
            total = len(agent.expectations)
            lines.append(f"\n{agent.agent_name}")
            lines.append(f"  Focus: {agent.agent_focus}")
            lines.append(f"  Expectations: {met}/{total}")
            lines.append(f"  Anomalies: {len(agent.anomalies)}")
            lines.append(f"  Coverage: {agent.coverage_score:.1f}%")

        # Discrepancies
        lines.append(f"\n--- Discrepancies: {len(self.discrepancies)} ---")
        if not self.discrepancies:
            lines.append(
                "  No discrepancies — either coverage is good or both "
                "agents share the same blind spots."
            )
        else:
            for d in self.discrepancies:
                lines.append(
                    f"  [{d.anomaly.severity.value.upper()}] "
                    f"Found by {d.found_by}, missed by {d.missed_by}"
                )
                lines.append(f"    {d.anomaly.description[:80]}")
                lines.append(f"    Significance: {d.significance}")

        # Combined
        lines.append(f"\n--- Combined Assessment ---")
        lines.append(f"  Combined score: {self.combined_score():.1f}%")
        lines.append(
            f"  Total unique anomalies: {len(self.combined_anomalies)}"
        )
        lines.append(f"  Discrepancies: {len(self.discrepancies)}")

        if self.discrepancies:
            lines.append(
                "\n  Discrepancies represent potential UNKNOWN UNKNOWNS "
                "\u2014 gaps that neither agent alone would have fully "
                "identified."
            )

        lines.append("=" * 60)
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for web API / database."""
        return {
            "alpha": self.alpha.to_dict(),
            "beta": self.beta.to_dict(),
            "combined": {
                "coverage": self.combined_score(),
                "blindness_gap": abs(
                    self.alpha.coverage_score - self.beta.coverage_score
                ),
                "total_anomalies": len(self.combined_anomalies),
                "known_unknowns": len(self.discrepancies),
            },
            "discrepancies": [d.to_dict() for d in self.discrepancies],
            "combined_anomalies": [
                a.to_dict() for a in self.combined_anomalies
            ],
        }


# ============================================================
# MULTI-AGENT SYSTEM
# ============================================================

class MultiAgentSystem:
    """Orchestrates the full dual-agent audit."""

    def __init__(self, postulates: DynamicPostulates) -> None:
        self.postulates = postulates

    def run(self, findings: list[Finding]) -> dict[str, Any]:
        """Run both agents and the arbiter.

        Returns the full arbiter result dict.
        """
        alpha = AgentInstitutional(self.postulates)
        beta = AgentTheoretical(self.postulates)

        report_alpha = alpha.audit(findings)
        report_beta = beta.audit(findings)

        arbiter = Arbiter(report_alpha, report_beta)
        arbiter.compare()

        return arbiter.to_dict()
