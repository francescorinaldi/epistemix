"""Content analysis — structural absences, convergence, and empty query patterns.

Based on the founder's v2 design with:
  - StructuralFact with explicit item tracking
  - TheoryPosition with question/answer/evidence structure
  - Per-entity reachability analysis across languages
  - Shannon-like diversity scoring for convergence

Three analyzers + a facade (ContentAnalysisEngine).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from epistemix.models import Anomaly, Finding, GapType, Severity


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class StructuralFact:
    """A known structural fact that theories must address.

    Example: "5 individuals found in tomb" with items
    ["woman ~60", "man 35-45 #1", "man 35-45 #2", "newborn", "cremated remains"]
    """
    description: str
    items: list[str] = field(default_factory=list)
    addressed_by: dict[str, list[str]] = field(default_factory=dict)

    def register_addressing(self, theory: str, items_addressed: list[str]) -> None:
        """Record which items a theory addresses."""
        self.addressed_by.setdefault(theory, []).extend(items_addressed)

    @property
    def unaddressed_items(self) -> list[str]:
        """Items not addressed by any theory."""
        all_addressed = set()
        for items in self.addressed_by.values():
            all_addressed.update(i.lower() for i in items)
        return [
            item for item in self.items
            if item.lower() not in all_addressed
        ]


@dataclass
class TheoryPosition:
    """A theory's position on a question, with evidence."""
    question: str
    theory: str
    answer: str
    evidence: str = ""
    source_type: str = ""


@dataclass
class QueryResult:
    """Result tracking for a query execution."""
    query: str
    language: str
    findings_count: int = 0
    empty: bool = False


# ============================================================
# STRUCTURAL ABSENCE DETECTOR
# ============================================================

class StructuralAbsenceDetector:
    """Detects when known facts are not addressed by theories."""

    def __init__(self) -> None:
        self.facts: list[StructuralFact] = []

    def register_fact(self, fact: StructuralFact) -> None:
        """Register a structural fact."""
        self.facts.append(fact)

    def generate_anomalies(self) -> list[Anomaly]:
        """Generate anomalies for unaddressed facts."""
        anomalies: list[Anomaly] = []

        for fact in self.facts:
            unaddressed = fact.unaddressed_items
            if unaddressed and fact.items:
                ratio = len(unaddressed) / len(fact.items)
                severity = (
                    Severity.CRITICAL if ratio > 0.5
                    else Severity.HIGH if ratio > 0.3
                    else Severity.MEDIUM
                )
                anomalies.append(Anomaly(
                    description=(
                        f"{len(unaddressed)}/{len(fact.items)} items "
                        f"unaddressed in '{fact.description}': "
                        f"{', '.join(unaddressed[:3])}"
                    ),
                    gap_type=GapType.STRUCTURAL_ABSENCE,
                    severity=severity,
                    recommendation="Investigate theories covering these items",
                ))

        return anomalies


# ============================================================
# CONVERGENCE ANALYZER
# ============================================================

class ConvergenceAnalyzer:
    """Detects excess convergence (echo chamber) or divergence (fragmentation).

    Tracks theory positions per question and measures consensus.
    """

    def __init__(self) -> None:
        self.positions: list[TheoryPosition] = []

    def register_position(self, position: TheoryPosition) -> None:
        """Register a theory's position on a question."""
        self.positions.append(position)

    def uniformity_score(self) -> float:
        """0.0 = completely diverse, 1.0 = complete agreement.

        Calculated as 1 - (unique_answers / total_positions).
        """
        if not self.positions:
            return 0.0

        answers = [p.answer.lower().strip() for p in self.positions]
        unique = len(set(answers))
        return 1.0 - (unique / len(answers))

    def generate_anomalies(self) -> list[Anomaly]:
        """Generate convergence/divergence anomalies."""
        anomalies: list[Anomaly] = []

        if len(self.positions) < 2:
            return anomalies

        score = self.uniformity_score()

        if score > 0.7:
            anomalies.append(Anomaly(
                description=(
                    f"Excess convergence detected (uniformity={score:.2f}). "
                    "Sources may form an echo chamber."
                ),
                gap_type=GapType.CONVERGENCE_EXCESS,
                severity=Severity.HIGH,
                recommendation="Search for dissenting or alternative views",
            ))

        if score < 0.1:
            anomalies.append(Anomaly(
                description=(
                    f"Excess divergence detected (uniformity={score:.2f}). "
                    "No agreement between sources."
                ),
                gap_type=GapType.DIVERGENCE_EXCESS,
                severity=Severity.MEDIUM,
                recommendation="Look for review/synthesis articles",
            ))

        # Check for isolated advocates (theory with only one voice)
        by_question: dict[str, dict[str, list[str]]] = {}
        for p in self.positions:
            q = p.question.lower()
            by_question.setdefault(q, {})
            by_question[q].setdefault(p.answer.lower(), []).append(p.theory)

        for question, answers in by_question.items():
            for answer, theories in answers.items():
                if len(theories) == 1:
                    anomalies.append(Anomaly(
                        description=(
                            f"Isolated advocate: only '{theories[0]}' "
                            f"answers '{question}' with '{answer}'"
                        ),
                        gap_type=GapType.VOICE,
                        severity=Severity.MEDIUM,
                        recommendation=(
                            "Search for additional advocates or critics"
                        ),
                    ))

        return anomalies


# ============================================================
# EMPTY QUERY ANALYZER
# ============================================================

class EmptyQueryAnalyzer:
    """Analyzes patterns in empty (no-result) queries.

    Detects systematic language gaps and entity reachability issues.
    """

    def __init__(self) -> None:
        self.results: list[QueryResult] = []

    def register_result(self, result: QueryResult) -> None:
        """Register a query result."""
        self.results.append(result)

    def register_from_findings(
        self, query: str, language: str, findings: list[Finding]
    ) -> None:
        """Convenience: register from query + findings list."""
        self.results.append(QueryResult(
            query=query,
            language=language,
            findings_count=len(findings),
            empty=len(findings) == 0,
        ))

    def language_productivity(self) -> dict[str, dict[str, int]]:
        """Per-language query statistics."""
        stats: dict[str, dict[str, int]] = {}
        for r in self.results:
            lang = r.language
            if lang not in stats:
                stats[lang] = {"total": 0, "empty": 0, "productive": 0}
            stats[lang]["total"] += 1
            if r.empty:
                stats[lang]["empty"] += 1
            else:
                stats[lang]["productive"] += 1
        return stats

    def generate_anomalies(self) -> list[Anomaly]:
        """Generate anomalies from empty query patterns."""
        anomalies: list[Anomaly] = []

        stats = self.language_productivity()

        for lang, counts in stats.items():
            if counts["total"] >= 2:
                empty_ratio = counts["empty"] / counts["total"]
                if empty_ratio > 0.6:
                    anomalies.append(Anomaly(
                        description=(
                            f"Language '{lang}' has {empty_ratio:.0%} empty "
                            f"queries ({counts['empty']}/{counts['total']})"
                        ),
                        gap_type=GapType.EMPTY_QUERY_PATTERN,
                        severity=Severity.HIGH,
                        recommendation=(
                            f"Rephrase queries in {lang} or use "
                            "different terminology"
                        ),
                    ))

        # Overall empty ratio
        total = len(self.results)
        if total >= 5:
            empty = sum(1 for r in self.results if r.empty)
            if empty / total > 0.5:
                anomalies.append(Anomaly(
                    description=(
                        f"High overall empty query ratio: "
                        f"{empty}/{total} ({empty / total:.0%})"
                    ),
                    gap_type=GapType.EMPTY_QUERY_PATTERN,
                    severity=Severity.MEDIUM,
                    recommendation="Review query strategy and terminology",
                ))

        return anomalies


# ============================================================
# FACADE
# ============================================================

class ContentAnalysisEngine:
    """Facade combining all content analysis modules."""

    def __init__(self) -> None:
        self.structural = StructuralAbsenceDetector()
        self.convergence = ConvergenceAnalyzer()
        self.empty_queries = EmptyQueryAnalyzer()

    def generate_all_anomalies(self) -> list[Anomaly]:
        """Run all analyzers and collect anomalies."""
        anomalies: list[Anomaly] = []
        anomalies.extend(self.structural.generate_anomalies())
        anomalies.extend(self.convergence.generate_anomalies())
        anomalies.extend(self.empty_queries.generate_anomalies())
        return anomalies
