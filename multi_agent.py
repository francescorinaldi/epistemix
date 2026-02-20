"""
EPISTEMIX v2 — Multi-Agent Audit Module

Two agents examine the same research domain but with
deliberately different axiom priorities:

  AGENT α (Institutional):
    Prioritizes institutional structure, academic lineages,
    geographic-linguistic completeness. Asks: "which
    institutions and traditions are missing?"

  AGENT β (Theoretical):
    Prioritizes theory completeness, evidential support,
    logical consistency. Asks: "which arguments and
    evidence types are missing?"

The ARBITER compares their reports. Discrepancies —
anomalies found by one but not the other — are
candidates for unknown unknowns promoted to known
unknowns.

This implements the insight from the original conversation:
a single perspective (even a formal one) has structural
blind spots. Two perspectives with different axioms can
catch each other's gaps.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from core import (
    Finding, DynamicPostulates, Anomaly,
    Severity, GapType, Expectation,
)


# ============================================================
# AGENT BASE
# ============================================================

@dataclass
class AgentReport:
    """Output of a single agent's audit."""
    agent_name: str
    agent_focus: str
    expectations: list[Expectation] = field(default_factory=list)
    anomalies: list[Anomaly] = field(default_factory=list)
    coverage_score: float = 0.0

    @property
    def anomaly_signatures(self) -> set[str]:
        """Simplified anomaly identifiers for comparison."""
        sigs = set()
        for a in self.anomalies:
            # Normalize to comparable signature
            sig = f"{a.gap_type.value}:{a.severity.name}:{a.description[:80]}"
            sigs.add(sig)
        return sigs


# ============================================================
# AGENT α — Institutional Focus
# ============================================================

class AgentInstitutional:
    """
    Focuses on WHO is speaking and WHERE they come from.
    Priorities:
      - Geographic-linguistic completeness
      - Institutional diversity
      - Scholar investigation ratio
      - Academic tradition coverage
    """

    NAME = "Agent α (Institutional)"
    FOCUS = "institutions, traditions, geographic coverage"

    def __init__(self, postulates: DynamicPostulates):
        self.postulates = postulates

    def audit(self, findings: list[Finding]) -> AgentReport:
        report = AgentReport(
            agent_name=self.NAME,
            agent_focus=self.FOCUS,
        )

        report.expectations = self._derive_expectations(findings)
        self._satisfy(report.expectations, findings)
        report.anomalies = self._find_anomalies(findings)
        report.coverage_score = self._score(report)

        return report

    def _derive_expectations(
        self, findings: list[Finding]
    ) -> list[Expectation]:
        exps = []

        # 1. Every known institution should have been checked
        institutions = set()
        for f in findings:
            if f.institution:
                institutions.add(f.institution)
            for e in f.entities_mentioned:
                lower = e.lower()
                if any(w in lower for w in [
                    "university", "museum", "ministry",
                    "institute", "school",
                ]):
                    institutions.add(e)

        for inst in institutions:
            exps.append(Expectation(
                description=(
                    f"Direct publications from '{inst}' found"
                ),
                gap_type=GapType.INSTITUTIONAL,
                severity_if_unmet=Severity.MEDIUM,
            ))

        # 2. Country of origin should have local-language sources
        from core import GEOGRAPHIC_LINGUISTIC
        country = self.postulates.country
        geo = GEOGRAPHIC_LINGUISTIC.get(country, {})

        for lang in geo.get("primary_languages", []):
            exps.append(Expectation(
                description=(
                    f"Sources in primary language '{lang}'"
                ),
                gap_type=GapType.LINGUISTIC,
                severity_if_unmet=Severity.HIGH,
            ))

        for lang, inst in geo.get(
            "foreign_traditions", {}
        ).items():
            exps.append(Expectation(
                description=(
                    f"Foreign tradition '{inst}' ({lang}) "
                    f"checked"
                ),
                gap_type=GapType.INSTITUTIONAL,
                severity_if_unmet=Severity.MEDIUM,
            ))

        # 3. Scholar nationality diversity
        # If all scholars are from one country, flag it
        exps.append(Expectation(
            description=(
                "Scholars from at least 2 different "
                "institutions/countries"
            ),
            gap_type=GapType.INSTITUTIONAL,
            severity_if_unmet=Severity.MEDIUM,
        ))

        # 4. High scholar-to-institution ratio
        exps.append(Expectation(
            description=(
                "At least 3 distinct institutions represented"
            ),
            gap_type=GapType.INSTITUTIONAL,
            severity_if_unmet=Severity.MEDIUM,
        ))

        return exps

    def _satisfy(
        self, expectations: list[Expectation],
        findings: list[Finding]
    ):
        langs = set(f.language for f in findings)
        institutions = set(
            f.institution.lower() for f in findings
            if f.institution
        )

        for exp in expectations:
            desc = exp.description.lower()

            # Language check
            for lang in langs:
                if f"'{lang}'" in desc:
                    exp.satisfy(f"Found in {lang}")

            # Institution check
            for inst in institutions:
                if inst in desc:
                    exp.satisfy(f"Found: {inst}")

            # Multi-institution check
            if "3 distinct" in desc and len(institutions) >= 3:
                exp.satisfy(
                    f"{len(institutions)} institutions"
                )

            if "2 different" in desc and len(institutions) >= 2:
                exp.satisfy(
                    f"{len(institutions)} institutions"
                )

    def _find_anomalies(
        self, findings: list[Finding]
    ) -> list[Anomaly]:
        anomalies = []

        # Scholar concentration: if >50% of findings come
        # from same institution
        inst_counts: dict[str, int] = {}
        for f in findings:
            if f.institution:
                key = f.institution.lower()
                inst_counts[key] = inst_counts.get(key, 0) + 1

        total = len(findings)
        for inst, count in inst_counts.items():
            if total >= 4 and count / total > 0.5:
                anomalies.append(Anomaly(
                    description=(
                        f"Institutional concentration: "
                        f"'{inst}' accounts for "
                        f"{count}/{total} findings "
                        f"({count/total:.0%})"
                    ),
                    gap_type=GapType.INSTITUTIONAL,
                    severity=Severity.MEDIUM,
                    recommendation=(
                        "Seek sources from other institutions"
                    ),
                ))

        # Geographic clustering: all authors from same region?
        countries_seen = set()
        # Heuristic: use institution names to guess country
        for f in findings:
            inst = f.institution.lower()
            if "greece" in inst or "greek" in inst or "thessaloniki" in inst or "athens" in inst:
                countries_seen.add("Greece")
            elif "cyprus" in inst:
                countries_seen.add("Cyprus")
            elif "macquarie" in inst or "oxford" in inst or "cambridge" in inst:
                countries_seen.add("Anglophone")
            elif inst:
                countries_seen.add("Other")

        if len(countries_seen) <= 1 and len(findings) >= 5:
            anomalies.append(Anomaly(
                description=(
                    "All sources appear to come from a "
                    "single geographic/academic tradition"
                ),
                gap_type=GapType.GEOGRAPHIC,
                severity=Severity.HIGH,
                recommendation=(
                    "Search for perspectives from other "
                    "national academic traditions"
                ),
            ))

        return anomalies

    def _score(self, report: AgentReport) -> float:
        if not report.expectations:
            return 0.0
        met = sum(1 for e in report.expectations if e.met)
        base = (met / len(report.expectations)) * 100
        penalty = len(report.anomalies) * 5
        return max(base - penalty, 0)


# ============================================================
# AGENT β — Theoretical Focus
# ============================================================

class AgentTheoretical:
    """
    Focuses on WHAT is being argued and HOW well.
    Priorities:
      - Theory completeness (all major positions found?)
      - Evidence type coverage per theory
      - Internal consistency of arguments
      - Missing counter-arguments
    """

    NAME = "Agent β (Theoretical)"
    FOCUS = "theories, evidence, argumentation"

    def __init__(self, postulates: DynamicPostulates):
        self.postulates = postulates

    def audit(self, findings: list[Finding]) -> AgentReport:
        report = AgentReport(
            agent_name=self.NAME,
            agent_focus=self.FOCUS,
        )

        report.expectations = self._derive_expectations(findings)
        self._satisfy(report.expectations, findings)
        report.anomalies = self._find_anomalies(findings)
        report.coverage_score = self._score(report)

        return report

    def _derive_expectations(
        self, findings: list[Finding]
    ) -> list[Expectation]:
        exps = []

        # 1. Each theory should have a primary source
        theories = set()
        for f in findings:
            if f.theory_supported:
                theories.add(f.theory_supported)

        for theory in theories:
            exps.append(Expectation(
                description=(
                    f"Peer-reviewed source for: '{theory}'"
                ),
                gap_type=GapType.THEORY_UNSOURCED,
                severity_if_unmet=Severity.HIGH,
            ))

        # 2. Each theory should have a counter-argument
        for theory in theories:
            exps.append(Expectation(
                description=(
                    f"Counter-argument or critique of: "
                    f"'{theory}' found"
                ),
                gap_type=GapType.VOICE,
                severity_if_unmet=Severity.MEDIUM,
            ))

        # 3. Evidence diversity: each theory should cite
        #    multiple types of evidence
        evidence_types = [
            "archaeological", "historical/literary",
            "scientific/technical",
        ]
        for ev_type in evidence_types:
            exps.append(Expectation(
                description=(
                    f"At least one {ev_type} evidence "
                    f"source found"
                ),
                gap_type=GapType.SOURCE_TYPE,
                severity_if_unmet=Severity.MEDIUM,
            ))

        # 4. Comparative / review article
        if len(theories) >= 2:
            exps.append(Expectation(
                description=(
                    "Comparative study reviewing multiple "
                    "theories found"
                ),
                gap_type=GapType.SOURCE_TYPE,
                severity_if_unmet=Severity.MEDIUM,
            ))

        return exps

    def _satisfy(
        self, expectations: list[Expectation],
        findings: list[Finding]
    ):
        # Build lookup structures
        peer_reviewed_theories = set()
        all_theories = set()
        has_archaeological = False
        has_historical = False
        has_scientific = False
        has_comparative = False

        for f in findings:
            if f.theory_supported:
                all_theories.add(f.theory_supported.lower())
                if f.source_type in ("peer_reviewed", "peer-reviewed"):
                    peer_reviewed_theories.add(
                        f.theory_supported.lower()
                    )

            source_lower = f.source.lower()
            theory_lower = f.theory_supported.lower()
            combined = source_lower + " " + theory_lower

            if any(w in combined for w in [
                "excavat", "archaeolog", "finds", "artifact",
            ]):
                has_archaeological = True
            if any(w in combined for w in [
                "histor", "literary", "ancient source",
                "diodorus", "plutarch",
            ]):
                has_historical = True
            if any(w in combined for w in [
                "solar", "DNA", "osteolog", "scientific",
                "alignment", "radiocarbon",
            ]):
                has_scientific = True
            if any(w in combined for w in [
                "review", "comparative", "survey",
                "overview",
            ]):
                has_comparative = True

        for exp in expectations:
            desc = exp.description.lower()

            # Peer-reviewed source per theory
            if "peer-reviewed" in desc:
                for theory in peer_reviewed_theories:
                    if any(
                        w in desc
                        for w in theory.split()
                        if len(w) > 4
                    ):
                        exp.satisfy(f"Found for {theory}")

            # Counter-argument: theory X is critiqued if
            # another finding argues against it
            if "counter-argument" in desc:
                # Extract the theory name
                for theory_a in all_theories:
                    if any(
                        w in desc
                        for w in theory_a.split()
                        if len(w) > 4
                    ):
                        # Check if another theory contradicts
                        for theory_b in all_theories:
                            if theory_b != theory_a:
                                exp.satisfy(
                                    f"{theory_b} contradicts"
                                )
                                break

            # Evidence types
            if "archaeological" in desc and has_archaeological:
                exp.satisfy("Archaeological evidence found")
            if "historical" in desc and has_historical:
                exp.satisfy("Historical evidence found")
            if "scientific" in desc and has_scientific:
                exp.satisfy("Scientific evidence found")

            # Comparative study
            if "comparative" in desc and has_comparative:
                exp.satisfy("Comparative study found")

    def _find_anomalies(
        self, findings: list[Finding]
    ) -> list[Anomaly]:
        anomalies = []

        # Single-evidence theories: a theory supported by
        # only one type of evidence is weak
        theory_evidence: dict[str, set] = {}
        for f in findings:
            if not f.theory_supported:
                continue
            key = f.theory_supported.lower()
            if key not in theory_evidence:
                theory_evidence[key] = set()
            theory_evidence[key].add(f.source_type)

        for theory, types in theory_evidence.items():
            if len(types) <= 1 and types != {"peer_reviewed", "peer-reviewed"}:
                anomalies.append(Anomaly(
                    description=(
                        f"Theory '{theory}' supported by "
                        f"only one source type: "
                        f"{', '.join(types)}"
                    ),
                    gap_type=GapType.SOURCE_TYPE,
                    severity=Severity.MEDIUM,
                    recommendation=(
                        f"Search for additional evidence "
                        f"types supporting or refuting "
                        f"'{theory}'"
                    ),
                ))

        # Theory with single advocate
        theory_authors: dict[str, set] = {}
        for f in findings:
            if f.theory_supported and f.author:
                key = f.theory_supported.lower()
                if key not in theory_authors:
                    theory_authors[key] = set()
                theory_authors[key].add(f.author)

        for theory, authors in theory_authors.items():
            if len(authors) == 1:
                anomalies.append(Anomaly(
                    description=(
                        f"Theory '{theory}' has single "
                        f"advocate: {', '.join(authors)}"
                    ),
                    gap_type=GapType.VOICE,
                    severity=Severity.MEDIUM,
                    recommendation=(
                        f"Search for other scholars who "
                        f"support or engage with this theory"
                    ),
                ))

        return anomalies

    def _score(self, report: AgentReport) -> float:
        if not report.expectations:
            return 0.0
        met = sum(1 for e in report.expectations if e.met)
        base = (met / len(report.expectations)) * 100
        penalty = len(report.anomalies) * 5
        return max(base - penalty, 0)


# ============================================================
# ARBITER — Cross-compares agent reports
# ============================================================

@dataclass
class Discrepancy:
    """An anomaly found by one agent but not the other."""
    anomaly: Anomaly
    found_by: str
    missed_by: str
    significance: str

    def __repr__(self):
        return (
            f"⚡ [{self.anomaly.severity.name}] "
            f"Found by {self.found_by}, "
            f"missed by {self.missed_by}: "
            f"{self.anomaly.description[:80]}"
        )


class Arbiter:
    """
    Compares reports from Agent α and Agent β.
    Discrepancies between them are promoted as
    potential unknown unknowns.
    """

    def __init__(
        self,
        report_alpha: AgentReport,
        report_beta: AgentReport,
    ):
        self.alpha = report_alpha
        self.beta = report_beta
        self.discrepancies: list[Discrepancy] = []
        self.combined_anomalies: list[Anomaly] = []

    def compare(self) -> list[Discrepancy]:
        """
        Find anomalies unique to each agent.
        These represent blind spots of the other agent.
        """
        self.discrepancies = []

        # Anomalies in α but not β
        alpha_types = {
            a.gap_type for a in self.alpha.anomalies
        }
        beta_types = {
            a.gap_type for a in self.beta.anomalies
        }

        for a in self.alpha.anomalies:
            # Check if β has any anomaly of the same type
            # with similar description
            if not self._has_similar(a, self.beta.anomalies):
                self.discrepancies.append(Discrepancy(
                    anomaly=a,
                    found_by=self.alpha.agent_name,
                    missed_by=self.beta.agent_name,
                    significance=(
                        f"{self.beta.agent_name}'s theoretical "
                        f"focus missed this institutional gap"
                    ),
                ))

        for a in self.beta.anomalies:
            if not self._has_similar(a, self.alpha.anomalies):
                self.discrepancies.append(Discrepancy(
                    anomaly=a,
                    found_by=self.beta.agent_name,
                    missed_by=self.alpha.agent_name,
                    significance=(
                        f"{self.alpha.agent_name}'s institutional "
                        f"focus missed this theoretical gap"
                    ),
                ))

        # Combined: merge all unique anomalies
        seen = set()
        for a in self.alpha.anomalies + self.beta.anomalies:
            key = f"{a.gap_type.value}:{a.description[:60]}"
            if key not in seen:
                seen.add(key)
                self.combined_anomalies.append(a)

        return self.discrepancies

    def _has_similar(
        self, anomaly: Anomaly, others: list[Anomaly]
    ) -> bool:
        """Check if a similar anomaly exists in the other list."""
        for other in others:
            if anomaly.gap_type == other.gap_type:
                # Check word overlap in descriptions
                words_a = set(
                    w.lower() for w in anomaly.description.split()
                    if len(w) > 4
                )
                words_b = set(
                    w.lower() for w in other.description.split()
                    if len(w) > 4
                )
                overlap = len(words_a & words_b)
                if overlap >= 2:
                    return True
        return False

    def combined_score(self) -> float:
        """
        Weighted average of both agents' scores,
        penalized by discrepancies.
        """
        avg = (
            self.alpha.coverage_score +
            self.beta.coverage_score
        ) / 2

        # Each discrepancy reduces confidence
        penalty = len(self.discrepancies) * 3
        return max(avg - penalty, 0)

    def report(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("  MULTI-AGENT ARBITER REPORT")
        lines.append("=" * 60)

        # Agent summaries
        lines.append(
            f"\n  {self.alpha.agent_name}"
        )
        lines.append(f"  Focus: {self.alpha.agent_focus}")
        met_a = sum(
            1 for e in self.alpha.expectations if e.met
        )
        lines.append(
            f"  Expectations: {met_a}/"
            f"{len(self.alpha.expectations)}"
        )
        lines.append(
            f"  Anomalies: {len(self.alpha.anomalies)}"
        )
        lines.append(
            f"  Coverage: {self.alpha.coverage_score:.0f}%"
        )

        lines.append(
            f"\n  {self.beta.agent_name}"
        )
        lines.append(f"  Focus: {self.beta.agent_focus}")
        met_b = sum(
            1 for e in self.beta.expectations if e.met
        )
        lines.append(
            f"  Expectations: {met_b}/"
            f"{len(self.beta.expectations)}"
        )
        lines.append(
            f"  Anomalies: {len(self.beta.anomalies)}"
        )
        lines.append(
            f"  Coverage: {self.beta.coverage_score:.0f}%"
        )

        # Discrepancies — the core value
        lines.append(
            f"\n⚡ DISCREPANCIES: {len(self.discrepancies)}"
        )
        lines.append("-" * 50)

        if not self.discrepancies:
            lines.append(
                "  No discrepancies. Both agents agree."
            )
            lines.append(
                "  (This could mean good coverage OR"
            )
            lines.append(
                "   shared blind spots.)"
            )
        else:
            for d in self.discrepancies:
                lines.append(f"\n  {d}")
                lines.append(f"    Why: {d.significance}")
                lines.append(
                    f"    Fix: {d.anomaly.recommendation}"
                )

        # Combined assessment
        combined = self.combined_score()
        lines.append(f"\n📊 COMBINED COVERAGE: {combined:.0f}%")
        lines.append("-" * 50)

        total_unique = len(self.combined_anomalies)
        lines.append(
            f"  Total unique anomalies: {total_unique}"
        )
        lines.append(
            f"  Cross-agent discrepancies: "
            f"{len(self.discrepancies)}"
        )

        if self.discrepancies:
            lines.append(
                "\n  Discrepancies represent potential"
            )
            lines.append(
                "  UNKNOWN UNKNOWNS — gaps that neither"
            )
            lines.append(
                "  agent alone would have fully identified."
            )

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
