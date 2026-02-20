"""Data models for the Epistemix epistemic audit framework.

All data structures are centralized here to prevent circular imports
and ensure a clean DAG dependency graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"

    def __lt__(self, other: Severity) -> bool:
        order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2}
        return order[self] < order[other]

    def __le__(self, other: Severity) -> bool:
        return self == other or self < other


class FindingType(Enum):
    SCHOLAR = "scholar"
    THEORY = "theory"
    INSTITUTION = "institution"
    PUBLICATION = "publication"
    SCHOOL = "school"
    EVIDENCE = "evidence"
    METHOD = "method"
    EVENT = "event"
    OTHER = "other"


class PostulateStatus(Enum):
    UNCONFIRMED = "unconfirmed"
    CONFIRMED = "confirmed"
    REFUTED = "refuted"


class AnomalyType(Enum):
    LANGUAGE_GAP = "language_gap"
    THEORY_GAP = "theory_gap"
    DISCIPLINE_GAP = "discipline_gap"
    INSTITUTION_GAP = "institution_gap"
    SCHOOL_GAP = "school_gap"
    PUBLICATION_GAP = "publication_gap"
    TEMPORAL_GAP = "temporal_gap"
    CITATION_ISLAND = "citation_island"
    CONVERGENCE_EXCESS = "convergence_excess"
    DIVERGENCE_EXCESS = "divergence_excess"
    STRUCTURAL_ABSENCE = "structural_absence"
    EMPTY_QUERY_PATTERN = "empty_query_pattern"


class QueryLanguage(Enum):
    ENGLISH = "en"
    GREEK = "el"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    SPANISH = "es"
    TURKISH = "tr"
    ARABIC = "ar"
    CHINESE = "zh"
    JAPANESE = "ja"


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    """A discovered entity — scholar, theory, institution, etc."""
    name: str
    finding_type: FindingType
    source_query: str = ""
    description: str = ""
    language: QueryLanguage = QueryLanguage.ENGLISH
    citations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash((self.name.lower().strip(), self.finding_type))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Finding):
            return NotImplemented
        return (
            self.name.lower().strip() == other.name.lower().strip()
            and self.finding_type == other.finding_type
        )


@dataclass
class Postulate:
    """A dynamic assertion about what knowledge should exist."""
    id: str
    description: str
    meta_axiom_id: str
    status: PostulateStatus = PostulateStatus.UNCONFIRMED
    confirming_findings: list[str] = field(default_factory=list)
    generated_at_cycle: int = 0

    def confirm(self, finding_name: str) -> None:
        self.status = PostulateStatus.CONFIRMED
        if finding_name not in self.confirming_findings:
            self.confirming_findings.append(finding_name)

    def refute(self, reason: str = "") -> None:
        self.status = PostulateStatus.REFUTED


@dataclass
class Anomaly:
    """A gap between expectation and reality."""
    id: str
    anomaly_type: AnomalyType
    severity: Severity
    description: str
    suggested_queries: list[str] = field(default_factory=list)
    related_postulate_id: str = ""
    detected_at_cycle: int = 0
    resolved: bool = False

    def __hash__(self) -> int:
        return hash((self.anomaly_type, self.description.lower().strip()))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Anomaly):
            return NotImplemented
        return (
            self.anomaly_type == other.anomaly_type
            and self.description.lower().strip() == other.description.lower().strip()
        )


@dataclass
class Query:
    """A search query to execute."""
    text: str
    language: QueryLanguage = QueryLanguage.ENGLISH
    priority: float = 1.0
    executed: bool = False
    result_count: int = 0
    source_anomaly_id: str = ""
    cycle: int = 0


@dataclass
class CoverageScore:
    """Coverage is always a lower bound — we can never be sure we found everything."""
    confirmed: int
    total: int
    anomaly_count: int = 0
    cycle: int = 0

    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0.0
        return round((self.confirmed / self.total) * 100, 1)

    def __repr__(self) -> str:
        return (
            f"CoverageScore({self.confirmed}/{self.total} = {self.percentage}%, "
            f"anomalies={self.anomaly_count}, cycle={self.cycle})"
        )


@dataclass
class ResearchState:
    """Complete audit state container."""
    topic: str
    country: str
    discipline: str
    findings: list[Finding] = field(default_factory=list)
    postulates: list[Postulate] = field(default_factory=list)
    anomalies: list[Anomaly] = field(default_factory=list)
    queries: list[Query] = field(default_factory=list)
    coverage_history: list[CoverageScore] = field(default_factory=list)
    current_cycle: int = 0

    @property
    def unique_findings(self) -> set[Finding]:
        return set(self.findings)

    @property
    def unresolved_anomalies(self) -> list[Anomaly]:
        return [a for a in self.anomalies if not a.resolved]

    @property
    def confirmed_postulates(self) -> list[Postulate]:
        return [p for p in self.postulates if p.status == PostulateStatus.CONFIRMED]

    @property
    def unconfirmed_postulates(self) -> list[Postulate]:
        return [p for p in self.postulates if p.status == PostulateStatus.UNCONFIRMED]

    def add_finding(self, finding: Finding) -> bool:
        """Add a finding, returning True if it's new (not a duplicate)."""
        if finding in self.findings:
            return False
        self.findings.append(finding)
        return True

    def add_anomaly(self, anomaly: Anomaly) -> bool:
        """Add an anomaly, returning True if it's new."""
        if anomaly in self.anomalies:
            return False
        self.anomalies.append(anomaly)
        return True

    def current_coverage(self) -> CoverageScore:
        total = len(self.postulates)
        confirmed = len(self.confirmed_postulates)
        anomaly_count = len(self.unresolved_anomalies)
        return CoverageScore(
            confirmed=confirmed,
            total=total,
            anomaly_count=anomaly_count,
            cycle=self.current_cycle,
        )

    def to_dict(self) -> dict[str, Any]:
        coverage = self.current_coverage()
        return {
            "topic": self.topic,
            "country": self.country,
            "discipline": self.discipline,
            "cycle": self.current_cycle,
            "coverage_percentage": coverage.percentage,
            "confirmed_postulates": coverage.confirmed,
            "total_postulates": coverage.total,
            "total_findings": len(self.unique_findings),
            "total_anomalies": len(self.anomalies),
            "unresolved_anomalies": len(self.unresolved_anomalies),
            "coverage_history": [
                {"cycle": c.cycle, "percentage": c.percentage}
                for c in self.coverage_history
            ],
        }
