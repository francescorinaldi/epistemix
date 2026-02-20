"""Content analysis — detect structural absences, convergence anomalies, and empty query patterns.

Three analyzers + a facade:
- StructuralAbsenceAnalyzer: N entities found, M discussed → N-M gaps
- ConvergenceAnalyzer: uniformity score, excess convergence/divergence
- EmptyQueryAnalyzer: patterns in queries that returned nothing
- ContentAnalysisEngine: facade combining all three
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

from epistemix.models import (
    Anomaly,
    AnomalyType,
    Finding,
    FindingType,
    Query,
    Severity,
)


@dataclass
class StructuralAbsenceAnalyzer:
    """Detect gaps between found entities and discussed entities.

    If we found N scholars but only M are discussed in the literature,
    N - M scholars represent structural absences — people whose work
    exists but isn't being cited or discussed.
    """

    _found: dict[FindingType, set[str]] = field(default_factory=dict)
    _discussed: dict[FindingType, set[str]] = field(default_factory=dict)

    def register_found(self, finding: Finding) -> None:
        name = finding.name.lower().strip()
        if finding.finding_type not in self._found:
            self._found[finding.finding_type] = set()
        self._found[finding.finding_type].add(name)

    def register_discussed(self, name: str, finding_type: FindingType) -> None:
        name_norm = name.lower().strip()
        if finding_type not in self._discussed:
            self._discussed[finding_type] = set()
        self._discussed[finding_type].add(name_norm)

    def detect_absences(self) -> list[Anomaly]:
        anomalies = []
        for ftype, found_set in self._found.items():
            discussed_set = self._discussed.get(ftype, set())
            absent = found_set - discussed_set
            if len(absent) > 0 and len(found_set) >= 3:
                ratio = len(absent) / len(found_set)
                if ratio >= 0.3:
                    severity = Severity.HIGH if ratio >= 0.5 else Severity.MEDIUM
                    anomalies.append(Anomaly(
                        id=f"A-SA-{ftype.value}",
                        anomaly_type=AnomalyType.STRUCTURAL_ABSENCE,
                        severity=severity,
                        description=(
                            f"{len(absent)}/{len(found_set)} {ftype.value}s found but "
                            f"not discussed in literature: {', '.join(sorted(absent)[:5])}"
                        ),
                        suggested_queries=[
                            f"{name} publications" for name in sorted(absent)[:3]
                        ],
                    ))
        return anomalies


@dataclass
class ConvergenceAnalyzer:
    """Detect excess convergence or divergence in findings.

    Excess convergence: all sources agree on the same thing (echo chamber).
    Excess divergence: no two sources agree (fragmented field or poor search).
    """

    _claims: list[str] = field(default_factory=list)
    _sources_per_claim: Counter = field(default_factory=Counter)

    def register_claim(self, claim: str, source: str = "") -> None:
        claim_norm = claim.lower().strip()
        self._claims.append(claim_norm)
        self._sources_per_claim[claim_norm] += 1

    def uniformity_score(self) -> float:
        """0.0 = all unique claims, 1.0 = all claims identical."""
        if len(self._claims) <= 1:
            return 0.0
        unique = len(set(self._claims))
        return round(1.0 - (unique / len(self._claims)), 3)

    def detect_anomalies(self, min_claims: int = 5) -> list[Anomaly]:
        anomalies = []
        if len(self._claims) < min_claims:
            return anomalies

        score = self.uniformity_score()

        if score > 0.7:
            anomalies.append(Anomaly(
                id="A-CONV-excess",
                anomaly_type=AnomalyType.CONVERGENCE_EXCESS,
                severity=Severity.HIGH,
                description=(
                    f"Excess convergence detected (uniformity={score:.2f}). "
                    "Sources overwhelmingly agree — possible echo chamber."
                ),
                suggested_queries=[
                    "alternative interpretations",
                    "criticism of mainstream view",
                    "dissenting scholars",
                ],
            ))
        elif score < 0.1 and len(self._claims) >= min_claims:
            anomalies.append(Anomaly(
                id="A-CONV-divergence",
                anomaly_type=AnomalyType.DIVERGENCE_EXCESS,
                severity=Severity.MEDIUM,
                description=(
                    f"Excess divergence detected (uniformity={score:.2f}). "
                    "No agreement between sources — field may be fragmented "
                    "or search queries may be too broad."
                ),
                suggested_queries=[
                    "consensus views on topic",
                    "review articles",
                    "state of the art summary",
                ],
            ))

        return anomalies


@dataclass
class EmptyQueryAnalyzer:
    """Analyze patterns in queries that returned no results.

    Empty queries are informative — they tell us what we expected to find
    but couldn't. Patterns in empty queries reveal systematic blind spots.
    """

    _empty_queries: list[Query] = field(default_factory=list)
    _all_queries: list[Query] = field(default_factory=list)

    def register_query(self, query: Query) -> None:
        self._all_queries.append(query)
        if query.executed and query.result_count == 0:
            self._empty_queries.append(query)

    @property
    def empty_ratio(self) -> float:
        executed = [q for q in self._all_queries if q.executed]
        if not executed:
            return 0.0
        return len(self._empty_queries) / len(executed)

    def detect_language_pattern(self) -> list[Anomaly]:
        """Check if empty queries cluster by language."""
        if not self._empty_queries:
            return []

        lang_counts: Counter = Counter()
        for q in self._empty_queries:
            lang_counts[q.language] += 1

        anomalies = []
        for lang, count in lang_counts.most_common():
            total_in_lang = sum(
                1 for q in self._all_queries if q.executed and q.language == lang
            )
            if total_in_lang >= 2 and count / total_in_lang > 0.6:
                anomalies.append(Anomaly(
                    id=f"A-EQ-lang-{lang.value}",
                    anomaly_type=AnomalyType.EMPTY_QUERY_PATTERN,
                    severity=Severity.MEDIUM,
                    description=(
                        f"{count}/{total_in_lang} queries in {lang.name} returned "
                        "no results — possible language barrier or incorrect terminology"
                    ),
                    suggested_queries=[
                        f"Verify search terms in {lang.name}",
                    ],
                ))

        return anomalies

    def detect_anomalies(self) -> list[Anomaly]:
        anomalies = []

        # High overall empty ratio
        if len(self._all_queries) >= 5 and self.empty_ratio > 0.5:
            anomalies.append(Anomaly(
                id="A-EQ-high-empty",
                anomaly_type=AnomalyType.EMPTY_QUERY_PATTERN,
                severity=Severity.HIGH,
                description=(
                    f"{len(self._empty_queries)}/{len(self._all_queries)} queries "
                    f"returned no results ({self.empty_ratio:.0%}) — "
                    "search strategy may need revision"
                ),
                suggested_queries=[
                    "broaden search terms",
                    "use alternative terminology",
                ],
            ))

        anomalies.extend(self.detect_language_pattern())
        return anomalies


@dataclass
class ContentAnalysisEngine:
    """Facade combining all three content analyzers."""

    structural: StructuralAbsenceAnalyzer = field(
        default_factory=StructuralAbsenceAnalyzer
    )
    convergence: ConvergenceAnalyzer = field(default_factory=ConvergenceAnalyzer)
    empty_query: EmptyQueryAnalyzer = field(default_factory=EmptyQueryAnalyzer)

    def register_finding(self, finding: Finding) -> None:
        self.structural.register_found(finding)

    def register_discussed(self, name: str, finding_type: FindingType) -> None:
        self.structural.register_discussed(name, finding_type)

    def register_claim(self, claim: str, source: str = "") -> None:
        self.convergence.register_claim(claim, source)

    def register_query(self, query: Query) -> None:
        self.empty_query.register_query(query)

    def detect_all_anomalies(self) -> list[Anomaly]:
        anomalies = []
        anomalies.extend(self.structural.detect_absences())
        anomalies.extend(self.convergence.detect_anomalies())
        anomalies.extend(self.empty_query.detect_anomalies())
        return anomalies
