"""Data models for the Epistemix epistemic audit framework.

All data structures are centralized here to prevent circular imports.
Types are based on the founder's v2 dynamic design, with serialization
methods for the production web/worker stack.

Dependency: this module has ZERO internal imports — everything else
imports from here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Severity(Enum):
    """Severity levels for anomalies and expectations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    def __lt__(self, other: Severity) -> bool:
        order = {
            Severity.LOW: 0, Severity.MEDIUM: 1,
            Severity.HIGH: 2, Severity.CRITICAL: 3,
        }
        return order[self] < order[other]

    def __le__(self, other: Severity) -> bool:
        return self == other or self < other

    @property
    def weight(self) -> int:
        """Numeric weight for coverage calculations."""
        return {
            Severity.LOW: 1, Severity.MEDIUM: 2,
            Severity.HIGH: 3, Severity.CRITICAL: 5,
        }[self]


class GapType(Enum):
    """Types of epistemic gaps — used in both expectations and anomalies."""
    # Core gap types (from founder's v2 engine)
    LINGUISTIC = "linguistic"
    INSTITUTIONAL = "institutional"
    VOICE = "voice"
    SOURCE_TYPE = "source_type"
    ENTITY_UNRESEARCHED = "entity"
    THEORY_UNSOURCED = "theory"
    TEMPORAL = "temporal"
    GEOGRAPHIC = "geographic"
    # Additional gap types (from analysis modules)
    DISCIPLINE_GAP = "discipline_gap"
    SCHOOL_GAP = "school_gap"
    CITATION_ISLAND = "citation_island"
    CONVERGENCE_EXCESS = "convergence_excess"
    DIVERGENCE_EXCESS = "divergence_excess"
    STRUCTURAL_ABSENCE = "structural_absence"
    EMPTY_QUERY_PATTERN = "empty_query_pattern"
    # v3 Phase 3: semantic graph gap types
    RELATIONAL_GAP = "relational_gap"
    FRACTURE_LINE = "fracture_line"
    INFLUENCE_GAP = "influence_gap"
    ACCESS_BARRIER = "access_barrier"


class EntityType(Enum):
    """Classification of discovered entities."""
    SCHOLAR = "scholar"
    INSTITUTION = "institution"
    THEORY = "theory"
    HISTORICAL_FIGURE = "historical_figure"
    ANCIENT_SOURCE = "ancient_source"
    SITE = "site"
    PUBLICATION = "publication"
    EVIDENCE = "evidence"
    METHOD = "method"
    EVENT = "event"
    UNKNOWN = "unknown"


class QueryLanguage(Enum):
    """Supported query languages."""
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


class RelationType(Enum):
    """Types of semantic relations between entities."""
    SUPPORTS = "supports"
    CONTESTS = "contests"
    CONTRADICTS = "contradicts"
    CITES = "cites"
    EXTENDS = "extends"
    SUPERVISES = "supervises"
    COAUTHORS = "coauthors"
    TRANSLATES = "translates"


class AccessTier(Enum):
    """How reachable a language's academic ecosystem is via web search."""
    OPEN_WEB = "open_web"
    PARTIAL_ACCESS = "partial_access"
    WALLED_GARDEN = "walled_garden"


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LanguageEcosystem:
    """Per-language metadata for access-barrier reasoning."""
    language: str
    access_tier: AccessTier
    gated_databases: tuple[str, ...]
    estimated_gated_share: float
    query_style: str   # "keyword", "morphological", "phrasal"
    script: str        # "latin", "arabic", "cjk", "hangul"

    def to_dict(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "access_tier": self.access_tier.value,
            "gated_databases": list(self.gated_databases),
            "estimated_gated_share": self.estimated_gated_share,
            "query_style": self.query_style,
            "script": self.script,
        }


@dataclass
class CoverageBreakdown:
    """Split coverage: what we verified vs. what we estimate is unreachable."""
    accessible_score: float
    estimated_unreachable: float
    barrier_annotations: list[str] = field(default_factory=list)
    gated_expectations_count: int = 0
    gated_expectations_met: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "accessible_score": round(self.accessible_score, 1),
            "estimated_unreachable": round(self.estimated_unreachable, 1),
            "barrier_annotations": self.barrier_annotations,
            "gated_expectations_count": self.gated_expectations_count,
            "gated_expectations_met": self.gated_expectations_met,
        }

@dataclass
class Entity:
    """A tracked entity discovered during research.

    Entities grow: mention count increases, investigation status updates,
    and languages-seen-in expands as more findings reference them.
    """
    name: str
    entity_type: EntityType
    first_seen_in: str = ""
    times_mentioned: int = 1
    investigated: bool = False
    languages_seen_in: set = field(default_factory=set)
    affiliated_institution: str = ""

    def __hash__(self) -> int:
        return hash(self.name.lower())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return self.name.lower() == other.name.lower()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "entity_type": self.entity_type.value,
            "times_mentioned": self.times_mentioned,
            "investigated": self.investigated,
            "languages_seen_in": sorted(self.languages_seen_in),
            "affiliated_institution": self.affiliated_institution,
        }


@dataclass
class Expectation:
    """A derived expectation about what knowledge should exist.

    Generated by the DynamicInferenceEngine each cycle. Expectations
    are satisfied (or not) by matching findings against them.
    """
    description: str
    gap_type: GapType
    severity_if_unmet: Severity
    met: bool = False
    evidence: str = ""
    derived_in_cycle: int = 0

    def satisfy(self, evidence: str) -> None:
        self.met = True
        self.evidence = evidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "gap_type": self.gap_type.value,
            "severity": self.severity_if_unmet.value,
            "met": self.met,
            "evidence": self.evidence,
            "derived_in_cycle": self.derived_in_cycle,
        }


@dataclass
class WeightedPostulate:
    """A postulate with confidence tracking and temporal decay.

    Confidence reflects how well-supported a postulate is:
      - source_count: independent sources confirming it
      - language_spread: number of distinct languages
      - confidence: composite score (0.0–1.0)
      - last_confirmed_cycle: when last supported by a finding
      - decay_rate: per-month confidence decay (domain-dependent)

    Confidence thresholds drive query strategy:
      < 0.2  → VERIFY (generate confirmation queries)
      0.2–0.6 → STANDARD
      0.6–0.9 → RELIABLE (generate deepening queries)
      ≥ 0.9  → CONSOLIDATED
    """
    description: str
    meta_axiom_id: str = ""
    source_count: int = 0
    language_spread: int = 0
    confidence: float = 0.5
    last_confirmed_cycle: int = 0
    decay_rate: float = 0.02

    def effective_confidence(
        self,
        current_cycle: int,
        cycles_per_month: float = 2.0,
    ) -> float:
        """Confidence with temporal decay applied."""
        if self.decay_rate == 0 or current_cycle <= self.last_confirmed_cycle:
            return self.confidence
        months = (current_cycle - self.last_confirmed_cycle) / cycles_per_month
        return self.confidence * ((1 - self.decay_rate) ** months)

    @property
    def action(self) -> str:
        """Query strategy based on confidence level."""
        if self.confidence < 0.2:
            return "VERIFY"
        elif self.confidence < 0.6:
            return "STANDARD"
        elif self.confidence < 0.9:
            return "RELIABLE"
        return "CONSOLIDATED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "meta_axiom_id": self.meta_axiom_id,
            "source_count": self.source_count,
            "language_spread": self.language_spread,
            "confidence": round(self.confidence, 3),
            "last_confirmed_cycle": self.last_confirmed_cycle,
            "decay_rate": self.decay_rate,
            "action": self.action,
        }


@dataclass
class NegativePostulate:
    """Evidence of absence — a query that found nothing.

    When queries return zero results, the void is structured as a
    NegativePostulate with hypotheses about why:
      - access_barrier: walled-garden ecosystem (CNKI, etc.)
      - wrong_terminology: terms don't match local usage
      - genuinely_absent: the knowledge doesn't exist
      - wrong_language: topic not studied in this language

    The reformulation field suggests how to retry in the next cycle.
    """
    query_text: str
    language: str
    expected_by: str = ""
    attempts: int = 1
    possible_reason: str = ""
    reformulation: str = ""
    detected_at_cycle: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_text": self.query_text,
            "language": self.language,
            "expected_by": self.expected_by,
            "attempts": self.attempts,
            "possible_reason": self.possible_reason,
            "reformulation": self.reformulation,
            "detected_at_cycle": self.detected_at_cycle,
        }


@dataclass
class SemanticRelation:
    """A typed relationship between two entities.

    Extracted by the connector (LLM) from findings.
    Confidence reflects how certain the extraction is.
    Evidence is the textual quote justifying the relation.
    """
    source: str
    target: str
    relation: RelationType
    confidence: float
    evidence: str
    language: str
    cycle: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation.value,
            "confidence": round(self.confidence, 3),
            "evidence": self.evidence,
            "language": self.language,
            "cycle": self.cycle,
        }


@dataclass
class Finding:
    """A research finding from a search query.

    Rich metadata: author, institution, theory supported, year,
    source type, and mentioned entities enable deep analysis.
    """
    source: str
    language: str
    author: str = ""
    institution: str = ""
    theory_supported: str = ""
    source_type: str = ""
    year: int = 0
    entities_mentioned: list = field(default_factory=list)
    search_query_used: str = ""
    cycle: int = 0

    def __hash__(self) -> int:
        return hash((self.source.lower().strip(), self.language))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Finding):
            return NotImplemented
        return (
            self.source.lower().strip() == other.source.lower().strip()
            and self.language == other.language
        )

    def __repr__(self) -> str:
        year_str = f" ({self.year})" if self.year else ""
        return f"[{self.language}] {self.source}{year_str}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "language": self.language,
            "author": self.author,
            "institution": self.institution,
            "theory_supported": self.theory_supported,
            "source_type": self.source_type,
            "year": self.year,
            "entities_mentioned": self.entities_mentioned,
            "cycle": self.cycle,
        }


@dataclass
class Anomaly:
    """A gap between expectation and reality.

    Each anomaly has a gap type, severity, human-readable recommendation,
    and suggested queries to fill the gap.
    """
    description: str
    gap_type: GapType
    severity: Severity
    recommendation: str = ""
    suggested_queries: list = field(default_factory=list)
    detected_at_cycle: int = 0

    def __hash__(self) -> int:
        return hash((self.gap_type, self.description.lower().strip()))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Anomaly):
            return NotImplemented
        return (
            self.gap_type == other.gap_type
            and self.description.lower().strip() == other.description.lower().strip()
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "gap_type": self.gap_type.value,
            "severity": self.severity.value,
            "recommendation": self.recommendation,
            "suggested_queries": self.suggested_queries,
            "detected_at_cycle": self.detected_at_cycle,
        }


@dataclass
class SearchQuery:
    """A search query to execute."""
    query: str
    language: str
    rationale: str = ""
    priority: Severity = Severity.MEDIUM
    target_gap: GapType = GapType.LINGUISTIC
    executed: bool = False

    def __repr__(self) -> str:
        mark = "\u2713" if self.executed else "\u25cb"
        return f"[{mark}] [{self.language}] {self.query}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "language": self.language,
            "rationale": self.rationale,
            "priority": self.priority.value,
            "target_gap": self.target_gap.value,
            "executed": self.executed,
        }


@dataclass
class CycleSnapshot:
    """State of the system at end of a cycle."""
    cycle: int
    n_postulate_scholars: int
    n_postulate_theories: int
    n_postulate_institutions: int
    n_expectations: int
    n_expectations_met: int
    n_findings: int
    n_anomalies: int
    coverage_score: float
    new_entities_discovered: list = field(default_factory=list)
    queries_generated: int = 0
    # v3: weighted postulate metrics
    weighted_postulates_count: int = 0
    avg_confidence: float = 0.0
    negative_postulates_count: int = 0
    # v3 Phase 3: semantic graph metrics
    relations_count: int = 0
    schools_count: int = 0
    fractures_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle": self.cycle,
            "percentage": self.coverage_score,
            "confirmed": self.n_expectations_met,
            "total": self.n_expectations,
            "findings": self.n_findings,
            "anomalies": self.n_anomalies,
            "new_entities": self.new_entities_discovered,
            "queries_generated": self.queries_generated,
            "weighted_postulates": self.weighted_postulates_count,
            "avg_confidence": round(self.avg_confidence, 3),
            "negative_postulates": self.negative_postulates_count,
            "relations": self.relations_count,
            "schools": self.schools_count,
            "fractures": self.fractures_count,
        }


@dataclass
class AgentReport:
    """Result of a single agent's audit."""
    agent_name: str
    agent_focus: str
    expectations: list[Expectation] = field(default_factory=list)
    anomalies: list[Anomaly] = field(default_factory=list)
    coverage_score: float = 0.0

    @property
    def anomaly_signatures(self) -> set[str]:
        """Normalized signatures for cross-agent comparison."""
        return {
            f"{a.gap_type.value}:{a.severity.value}:{a.description[:80]}"
            for a in self.anomalies
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "agent_focus": self.agent_focus,
            "coverage": self.coverage_score,
            "findings": len(self.expectations),
            "anomalies": len(self.anomalies),
            "anomaly_details": [a.to_dict() for a in self.anomalies],
        }


@dataclass
class Discrepancy:
    """A gap found by one agent but missed by another."""
    anomaly: Anomaly
    found_by: str
    missed_by: str
    significance: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.anomaly.description,
            "gap_type": self.anomaly.gap_type.value,
            "severity": self.anomaly.severity.value,
            "found_by": self.found_by,
            "missed_by": self.missed_by,
            "significance": self.significance,
        }
