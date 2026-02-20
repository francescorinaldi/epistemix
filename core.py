"""
EPISTEMIX v2 — Dynamic Epistemic Framework

Key differences from v1:
  - Postulates are DYNAMIC: they start nearly empty and grow
    as findings are ingested. Every new scholar name, institution,
    or theory mentioned in a finding becomes a new postulate.
  - Multilingual by DEFAULT: the system generates search queries
    in all relevant languages based on geographic axioms.
  - CYCLIC: the engine runs in find → ingest → re-derive → audit
    loops, getting smarter with each cycle.
  - SELF-AWARE of its own evolution: tracks how postulates,
    expectations, and coverage change across cycles.

Architecture:
  ┌─────────────┐
  │  Seed Input  │  Minimal starting info (topic, country)
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │  Query Gen  │  Generates multilingual search queries
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │  Findings   │  Results come in (simulated or real)
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │  Ingester   │  Extracts entities → updates postulates
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │  Inference  │  Re-derives expectations from new postulates
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │   Auditor   │  Compares findings vs expectations
  └──────┬──────┘
         ▼
  ┌─────────────┐
  │  New Queries│  Generates targeted queries for gaps
  └──────┬──────┘
         │
         └──────── loops back to Findings ───────┘
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime
import json
import re


# ============================================================
# TYPES
# ============================================================

class Severity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class GapType(Enum):
    LINGUISTIC = "linguistic"
    INSTITUTIONAL = "institutional"
    VOICE = "voice"
    SOURCE_TYPE = "source_type"
    ENTITY_UNRESEARCHED = "entity"
    THEORY_UNSOURCED = "theory"
    TEMPORAL = "temporal"
    GEOGRAPHIC = "geographic"


class EntityType(Enum):
    """Classifies discovered entities to know how to handle them."""
    SCHOLAR = "scholar"           # Academic researcher
    INSTITUTION = "institution"   # University, ministry, etc.
    THEORY = "theory"             # Competing hypothesis
    HISTORICAL_FIGURE = "historical_figure"  # Subject of study
    ANCIENT_SOURCE = "ancient_source"        # Diodorus, Plutarch...
    SITE = "site"                 # Archaeological site
    UNKNOWN = "unknown"


@dataclass
class Entity:
    """A named entity discovered during research."""
    name: str
    entity_type: EntityType
    first_seen_in: str = ""       # Which finding first mentioned it
    times_mentioned: int = 1
    investigated: bool = False    # Have we searched FOR this entity?
    languages_seen_in: set = field(default_factory=set)
    affiliated_institution: str = ""

    def __hash__(self):
        return hash(self.name.lower())

    def __eq__(self, other):
        if isinstance(other, Entity):
            return self.name.lower() == other.name.lower()
        return False


@dataclass
class Expectation:
    description: str
    gap_type: GapType
    severity_if_unmet: Severity
    met: bool = False
    evidence: str = ""
    derived_in_cycle: int = 0

    def satisfy(self, evidence: str):
        self.met = True
        self.evidence = evidence

    def __repr__(self):
        status = "✓" if self.met else "✗"
        return f"[{status}] ({self.severity_if_unmet.name}) {self.description}"


@dataclass
class Finding:
    """A piece of information found during research."""
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

    def __repr__(self):
        return f"[{self.language}] {self.source} ({self.year})"


@dataclass
class Anomaly:
    description: str
    gap_type: GapType
    severity: Severity
    recommendation: str
    suggested_queries: list = field(default_factory=list)

    def __repr__(self):
        icon = {
            Severity.LOW: "⚪", Severity.MEDIUM: "🟡",
            Severity.HIGH: "🟠", Severity.CRITICAL: "🔴"
        }[self.severity]
        return f"{icon} [{self.severity.name}] {self.description}"


@dataclass
class SearchQuery:
    """A search query generated by the system."""
    query: str
    language: str
    rationale: str
    priority: Severity
    target_gap: GapType
    executed: bool = False

    def __repr__(self):
        status = "✓" if self.executed else "○"
        return f"[{status}] [{self.language}] {self.query}"


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


# ============================================================
# GEOGRAPHIC-LINGUISTIC AXIOMS
# ============================================================

GEOGRAPHIC_LINGUISTIC = {
    "Greece": {
        "primary_languages": ["el", "en"],
        "foreign_traditions": {
            "it": "Italian School of Archaeology at Athens",
            "de": "German Archaeological Institute (DAI)",
            "fr": "French School at Athens (EfA)",
            "en": "British School at Athens (BSA)",
        },
        "transliteration_map": {
            "el": {
                "tomb": "τάφος",
                "tumulus": "τύμβος",
                "burial": "ταφή",
                "excavation": "ανασκαφή",
                "archaeology": "αρχαιολογία",
            }
        }
    },
    "Egypt": {
        "primary_languages": ["ar", "en"],
        "foreign_traditions": {
            "fr": "IFAO Cairo",
            "de": "DAI Cairo",
            "it": "Centro Archeologico Italiano",
        },
        "transliteration_map": {}
    },
    "Italy": {
        "primary_languages": ["it"],
        "foreign_traditions": {
            "en": "British School at Rome",
            "de": "DAI Rome",
            "fr": "École française de Rome",
        },
        "transliteration_map": {}
    },
    "Turkey": {
        "primary_languages": ["tr", "en"],
        "foreign_traditions": {
            "de": "DAI Istanbul",
            "en": "British Institute at Ankara",
            "fr": "IFEA",
        },
        "transliteration_map": {}
    },
}

# Known name transliterations for multilingual search
TRANSLITERATIONS = {
    "Amphipolis": {
        "el": "Αμφίπολη",
        "it": "Anfipoli",
        "de": "Amphipolis",
        "fr": "Amphipolis",
    },
    "Hephaestion": {
        "el": "Ηφαιστίων",
        "it": "Efestione",
        "de": "Hephaistion",
        "fr": "Héphestion",
    },
    "Olympias": {
        "el": "Ολυμπιάδα",
        "it": "Olimpiade",
        "de": "Olympias",
        "fr": "Olympias",
    },
    "Alexander the Great": {
        "el": "Μέγας Αλέξανδρος",
        "it": "Alessandro Magno",
        "de": "Alexander der Große",
        "fr": "Alexandre le Grand",
    },
    "Kasta": {
        "el": "Καστά",
        "it": "Kasta",
        "de": "Kasta",
        "fr": "Kasta",
    },
}

# Entity classification heuristics
KNOWN_HISTORICAL_FIGURES = {
    "alexander", "alexander the great", "alexander iv",
    "hephaestion", "olympias", "cassander",
    "philip", "philip ii", "roxane", "nearchus",
    "antipatros", "antipater",
    "perdiccas", "ptolemy", "dinocrates", "deinokratis",
    "laomedon", "eurydice", "arrhidaeus",
    "amyntor",
}

KNOWN_ANCIENT_SOURCES = {
    "diodorus", "diodorus siculus", "plutarch", "arrian",
    "arrianus", "justin", "strabo", "pausanias",
}

KNOWN_DEITIES_CONCEPTS = {
    "cybele", "persephone", "hades", "pluto", "hermes",
    "dionysus", "artemis", "demeter", "zeus",
}

KNOWN_PLACES = {
    "amphipolis", "vergina", "pella", "thessaloniki",
    "aigai", "athens", "dion", "babylon", "susa",
    "alexandria", "sidon", "anfipoli",
}

# Transliterated variants of historical figures / concepts
# that should NOT be treated as separate scholars
KNOWN_TRANSLITERATIONS = {
    "alessandro magno": "alexander the great",
    "efestione": "hephaestion",
    "hephaistion": "hephaestion",
    "ηφαιστίων": "hephaestion",
    "μέγας αλέξανδρος": "alexander the great",
    "olimpiade": "olympias",
    "ολυμπιάδα": "olympias",
    "deinokratis": "dinocrates",
    "antipatros": "antipater",
    "παρελαβον": "PARELABON",
    "ΠΑΡΕΛΑΒΟΝ": "PARELABON",
}


# ============================================================
# DYNAMIC POSTULATES
# ============================================================

class DynamicPostulates:
    """
    Postulates that grow as research progresses.
    Starts with minimal seed info; expands with each finding.
    """

    def __init__(self, country: str, topic: str, discipline: str = ""):
        self.country = country
        self.topic = topic
        self.discipline = discipline
        self.discovery_year: int = 0
        self.ongoing: bool = True

        # These grow dynamically
        self.entities: dict[str, Entity] = {}
        self.theories: list[str] = []
        self.languages_covered: set[str] = set()
        self.institutions: set[str] = set()
        self.scholars: set[str] = set()

        # Track evolution
        self.history: list[dict] = []

    def ingest_finding(self, finding: Finding) -> list[str]:
        """
        Process a finding: extract entities, update postulates.
        Returns list of NEW entities discovered.
        """
        new_entities = []

        # Track language
        self.languages_covered.add(finding.language)

        # Process author
        if finding.author:
            canonical_author = KNOWN_TRANSLITERATIONS.get(
                finding.author.lower(), finding.author
            )
            if self._register_entity(
                finding.author, EntityType.SCHOLAR,
                finding.source, finding.language,
                institution=finding.institution
            ):
                new_entities.append(finding.author)
            # Mark as investigated (we have their publication)
            key = canonical_author.lower()
            if key in self.entities:
                self.entities[key].investigated = True
            self.scholars.add(canonical_author)

        # Process institution
        if finding.institution:
            if self._register_entity(
                finding.institution, EntityType.INSTITUTION,
                finding.source, finding.language
            ):
                new_entities.append(finding.institution)
            self.institutions.add(finding.institution)

        # Process theory
        if (finding.theory_supported and
                finding.theory_supported not in self.theories):
            self.theories.append(finding.theory_supported)

        # Process mentioned entities
        for name in finding.entities_mentioned:
            entity_type = self._classify_entity(name)
            if self._register_entity(
                name, entity_type,
                finding.source, finding.language
            ):
                new_entities.append(name)
            else:
                # Already known — increment mention count
                canonical = KNOWN_TRANSLITERATIONS.get(
                    name.lower(), name
                )
                key = canonical.lower()
                if key in self.entities:
                    self.entities[key].times_mentioned += 1
                    self.entities[key].languages_seen_in.add(
                        finding.language
                    )

        return new_entities

    def _register_entity(
        self, name: str, entity_type: EntityType,
        source: str, language: str,
        institution: str = ""
    ) -> bool:
        """Register entity. Returns True if new."""
        # Resolve transliterations to canonical name
        canonical = KNOWN_TRANSLITERATIONS.get(
            name.lower(), name
        )
        key = canonical.lower()

        if key in self.entities:
            return False

        self.entities[key] = Entity(
            name=canonical,
            entity_type=entity_type,
            first_seen_in=source,
            times_mentioned=1,
            languages_seen_in={language},
            affiliated_institution=institution,
        )
        return True

    def _classify_entity(self, name: str) -> EntityType:
        """Heuristic classification of an entity."""
        lower = name.lower()

        if lower in KNOWN_HISTORICAL_FIGURES:
            return EntityType.HISTORICAL_FIGURE
        if lower in KNOWN_ANCIENT_SOURCES:
            return EntityType.ANCIENT_SOURCE
        if lower in KNOWN_DEITIES_CONCEPTS:
            return EntityType.UNKNOWN  # Not a research target
        if lower in KNOWN_PLACES:
            return EntityType.SITE
        if lower in KNOWN_TRANSLITERATIONS:
            return EntityType.HISTORICAL_FIGURE  # transliteration

        # Heuristics for scholars vs institutions
        if any(w in lower for w in [
            "university", "museum", "ministry",
            "institute", "school", "lab"
        ]):
            return EntityType.INSTITUTION

        # Default: assume scholar (most common in academic findings)
        return EntityType.SCHOLAR

    def get_uninvestigated_scholars(self) -> list[Entity]:
        """Scholars mentioned but not searched for."""
        return [
            e for e in self.entities.values()
            if e.entity_type == EntityType.SCHOLAR
            and not e.investigated
            and e.times_mentioned >= 1
        ]

    def get_uninvestigated_institutions(self) -> list[Entity]:
        """Institutions mentioned but not checked."""
        return [
            e for e in self.entities.values()
            if e.entity_type == EntityType.INSTITUTION
            and not e.investigated
        ]

    def snapshot(self) -> dict:
        return {
            "scholars": len(self.scholars),
            "theories": len(self.theories),
            "institutions": len(self.institutions),
            "total_entities": len(self.entities),
            "languages": sorted(self.languages_covered),
        }

    def describe(self) -> str:
        lines = [
            f"Topic: {self.topic}",
            f"Country: {self.country}",
            f"Discipline: {self.discipline}",
            f"Scholars discovered: {len(self.scholars)}",
            f"  {', '.join(sorted(self.scholars)) or '(none yet)'}",
            f"Theories identified: {len(self.theories)}",
        ]
        for t in self.theories:
            lines.append(f"  • {t}")
        lines.append(
            f"Institutions: {len(self.institutions)}"
        )
        for i in sorted(self.institutions):
            lines.append(f"  • {i}")
        lines.append(
            f"Languages covered: "
            f"{', '.join(sorted(self.languages_covered)) or '(none)'}"
        )
        return "\n".join(lines)


# ============================================================
# MULTILINGUAL QUERY GENERATOR
# ============================================================

class MultilingualQueryGenerator:
    """
    Generates search queries in all relevant languages.
    Uses geographic axioms + transliteration tables.
    """

    def __init__(self, postulates: DynamicPostulates):
        self.postulates = postulates

    def generate_initial_queries(self) -> list[SearchQuery]:
        """Generate seed queries in all relevant languages."""
        queries = []
        country = self.postulates.country
        topic = self.postulates.topic
        geo = GEOGRAPHIC_LINGUISTIC.get(country, {})

        # Determine all relevant languages
        all_langs = set(geo.get("primary_languages", ["en"]))
        all_langs.update(geo.get("foreign_traditions", {}).keys())
        all_langs.add("en")  # Always include English

        # Get transliterations for topic keywords
        topic_words = self._extract_key_terms(topic)

        for lang in sorted(all_langs):
            # Translate/transliterate key terms
            translated_terms = []
            for word in topic_words:
                trans = self._transliterate(word, lang)
                translated_terms.append(trans)

            query_text = " ".join(translated_terms)

            queries.append(SearchQuery(
                query=query_text,
                language=lang,
                rationale=f"Initial seed query in {lang}",
                priority=Severity.HIGH if lang in geo.get(
                    "primary_languages", []
                ) else Severity.MEDIUM,
                target_gap=GapType.LINGUISTIC,
            ))

            # Academic-specific query
            if lang == "en":
                queries.append(SearchQuery(
                    query=f"{topic} academic publication research",
                    language="en",
                    rationale="Target academic sources in English",
                    priority=Severity.HIGH,
                    target_gap=GapType.SOURCE_TYPE,
                ))

        return queries

    def generate_gap_filling_queries(
        self, anomalies: list[Anomaly]
    ) -> list[SearchQuery]:
        """Generate targeted queries to fill detected gaps."""
        queries = []

        for anomaly in anomalies:
            if anomaly.suggested_queries:
                for sq in anomaly.suggested_queries:
                    queries.append(sq)
                continue

            if anomaly.gap_type == GapType.ENTITY_UNRESEARCHED:
                # Extract entity names from description
                scholars = self.postulates.get_uninvestigated_scholars()
                # Sort by mention count (most mentioned first)
                scholars.sort(
                    key=lambda e: e.times_mentioned, reverse=True
                )

                for scholar in scholars[:5]:  # Top 5 most mentioned
                    # Search in multiple languages
                    for lang in self._relevant_languages():
                        topic_trans = self._transliterate(
                            self.postulates.topic.split()[0], lang
                        )
                        queries.append(SearchQuery(
                            query=(
                                f"{scholar.name} {topic_trans}"
                            ),
                            language=lang,
                            rationale=(
                                f"Investigate scholar "
                                f"'{scholar.name}' mentioned "
                                f"{scholar.times_mentioned}x "
                                f"but not yet researched"
                            ),
                            priority=Severity.HIGH,
                            target_gap=GapType.ENTITY_UNRESEARCHED,
                        ))

            elif anomaly.gap_type == GapType.LINGUISTIC:
                # Find which languages are missing
                covered = self.postulates.languages_covered
                needed = self._relevant_languages()
                missing = needed - covered

                for lang in missing:
                    topic_trans = self._transliterate(
                        self.postulates.topic, lang
                    )
                    queries.append(SearchQuery(
                        query=topic_trans,
                        language=lang,
                        rationale=f"Fill linguistic gap: {lang}",
                        priority=Severity.HIGH,
                        target_gap=GapType.LINGUISTIC,
                    ))

            elif anomaly.gap_type == GapType.INSTITUTIONAL:
                institutions = (
                    self.postulates.get_uninvestigated_institutions()
                )
                for inst in institutions[:3]:
                    queries.append(SearchQuery(
                        query=(
                            f"{inst.name} "
                            f"{self.postulates.topic}"
                        ),
                        language="en",
                        rationale=(
                            f"Check institution: {inst.name}"
                        ),
                        priority=Severity.MEDIUM,
                        target_gap=GapType.INSTITUTIONAL,
                    ))

            elif anomaly.gap_type == GapType.THEORY_UNSOURCED:
                # Search for academic sources for unsourced theories
                for theory in self.postulates.theories:
                    # Extract key term from theory name
                    key_term = theory.split("(")[0].strip()
                    queries.append(SearchQuery(
                        query=(
                            f'"{key_term}" academic paper'
                        ),
                        language="en",
                        rationale=(
                            f"Find primary source for theory: "
                            f"{theory}"
                        ),
                        priority=Severity.HIGH,
                        target_gap=GapType.THEORY_UNSOURCED,
                    ))

        # Deduplicate
        seen = set()
        unique = []
        for q in queries:
            key = (q.query.lower(), q.language)
            if key not in seen:
                seen.add(key)
                unique.append(q)

        return unique

    def _relevant_languages(self) -> set[str]:
        """All languages relevant to this domain."""
        country = self.postulates.country
        geo = GEOGRAPHIC_LINGUISTIC.get(country, {})
        langs = set(geo.get("primary_languages", ["en"]))
        langs.update(geo.get("foreign_traditions", {}).keys())
        langs.add("en")
        return langs

    def _extract_key_terms(self, topic: str) -> list[str]:
        """Extract searchable terms from topic description."""
        # Split on common separators
        words = re.split(r'[\s,;:]+', topic)
        # Keep meaningful words (>3 chars, not stopwords)
        stopwords = {
            "the", "and", "for", "from", "with", "near",
            "about", "this", "that", "tomb", "della", "del",
        }
        return [
            w for w in words
            if len(w) > 3 and w.lower() not in stopwords
        ]

    def _transliterate(self, term: str, language: str) -> str:
        """Attempt to transliterate a term into target language."""
        # Check direct transliteration table
        for key, trans_map in TRANSLITERATIONS.items():
            if key.lower() in term.lower():
                if language in trans_map:
                    return term.replace(key, trans_map[language])

        # Check country-specific translation map
        country = self.postulates.country
        geo = GEOGRAPHIC_LINGUISTIC.get(country, {})
        trans_map = geo.get("transliteration_map", {}).get(
            language, {}
        )
        for en_term, translated in trans_map.items():
            if en_term.lower() in term.lower():
                return term.lower().replace(
                    en_term.lower(), translated
                )

        # No translation found — return original
        return term


# ============================================================
# DYNAMIC INFERENCE ENGINE
# ============================================================

class DynamicInferenceEngine:
    """
    Derives expectations from current state of postulates.
    Re-runs each cycle as postulates evolve.
    """

    MIN_VOICES_PER_THEORY = 2
    EXPECTED_VOICES_RATIO = 3
    MIN_INVESTIGATION_RATIO = 0.5

    def __init__(self, postulates: DynamicPostulates):
        self.postulates = postulates

    def derive(self, cycle: int) -> list[Expectation]:
        expectations = []
        expectations.extend(self._linguistic(cycle))
        expectations.extend(self._plurality(cycle))
        expectations.extend(self._source_types(cycle))
        expectations.extend(self._temporal(cycle))
        expectations.extend(self._entity_coverage(cycle))
        expectations.extend(self._institutional(cycle))
        return expectations

    def _linguistic(self, cycle) -> list[Expectation]:
        exps = []
        country = self.postulates.country
        geo = GEOGRAPHIC_LINGUISTIC.get(country, {})

        for lang in geo.get("primary_languages", []):
            exps.append(Expectation(
                description=(
                    f"Research includes sources in primary "
                    f"language '{lang}' of {country}"
                ),
                gap_type=GapType.LINGUISTIC,
                severity_if_unmet=Severity.HIGH,
                derived_in_cycle=cycle,
            ))

        for lang, inst in geo.get(
            "foreign_traditions", {}
        ).items():
            exps.append(Expectation(
                description=(
                    f"Sources checked in '{lang}' ({inst})"
                ),
                gap_type=GapType.INSTITUTIONAL,
                severity_if_unmet=Severity.MEDIUM,
                derived_in_cycle=cycle,
            ))

        return exps

    def _plurality(self, cycle) -> list[Expectation]:
        exps = []
        n = len(self.postulates.theories)
        if n > 0:
            minimum = n * self.MIN_VOICES_PER_THEORY
            ideal = n * self.EXPECTED_VOICES_RATIO
            exps.append(Expectation(
                description=(
                    f"At least {minimum} independent scholarly "
                    f"voices for {n} theories (ideal: {ideal}+)"
                ),
                gap_type=GapType.VOICE,
                severity_if_unmet=Severity.HIGH,
                derived_in_cycle=cycle,
            ))

            for theory in self.postulates.theories:
                exps.append(Expectation(
                    description=(
                        f"Primary academic source for: "
                        f"'{theory}'"
                    ),
                    gap_type=GapType.THEORY_UNSOURCED,
                    severity_if_unmet=Severity.HIGH,
                    derived_in_cycle=cycle,
                ))
        return exps

    def _source_types(self, cycle) -> list[Expectation]:
        types = [
            "peer-reviewed", "institutional",
            "journalistic (quality)"
        ]
        return [
            Expectation(
                description=f"At least one {st} source found",
                gap_type=GapType.SOURCE_TYPE,
                severity_if_unmet=Severity.MEDIUM,
                derived_in_cycle=cycle,
            )
            for st in types
        ]

    def _temporal(self, cycle) -> list[Expectation]:
        exps = []
        if self.postulates.ongoing:
            exps.append(Expectation(
                description="Sources from within last 3 years",
                gap_type=GapType.TEMPORAL,
                severity_if_unmet=Severity.MEDIUM,
                derived_in_cycle=cycle,
            ))
        if self.postulates.discovery_year:
            exps.append(Expectation(
                description=(
                    f"Sources span from ~{self.postulates.discovery_year}"
                    f" to present"
                ),
                gap_type=GapType.TEMPORAL,
                severity_if_unmet=Severity.LOW,
                derived_in_cycle=cycle,
            ))
        return exps

    def _entity_coverage(self, cycle) -> list[Expectation]:
        """
        DYNAMIC: expectations generated from discovered entities.
        Scholars mentioned 2+ times should be investigated.
        """
        exps = []
        for entity in self.postulates.entities.values():
            if (entity.entity_type == EntityType.SCHOLAR
                    and entity.times_mentioned >= 2
                    and not entity.investigated):
                exps.append(Expectation(
                    description=(
                        f"Scholar '{entity.name}' mentioned "
                        f"{entity.times_mentioned}x — "
                        f"investigate their publications"
                    ),
                    gap_type=GapType.ENTITY_UNRESEARCHED,
                    severity_if_unmet=Severity.HIGH,
                    derived_in_cycle=cycle,
                ))
        return exps

    def _institutional(self, cycle) -> list[Expectation]:
        exps = []
        for inst in self.postulates.institutions:
            exps.append(Expectation(
                description=(
                    f"Publications from '{inst}' reviewed"
                ),
                gap_type=GapType.INSTITUTIONAL,
                severity_if_unmet=Severity.MEDIUM,
                derived_in_cycle=cycle,
            ))
        return exps


# ============================================================
# EXPECTATION SATISFIER
# ============================================================

class ExpectationSatisfier:
    """Checks which expectations are met by current findings."""

    @staticmethod
    def satisfy(
        expectations: list[Expectation],
        findings: list[Finding],
        postulates: DynamicPostulates
    ):
        langs = set(f.language for f in findings)
        types = set(f.source_type for f in findings)
        authors = set(f.author.lower() for f in findings if f.author)
        years = [f.year for f in findings if f.year > 0]
        institutions = set(
            f.institution.lower() for f in findings
            if f.institution
        )

        # Theories with peer-reviewed sources
        theories_sourced = set()
        for f in findings:
            if f.theory_supported and f.source_type in (
                "peer_reviewed", "peer-reviewed"
            ):
                theories_sourced.add(f.theory_supported.lower())

        for exp in expectations:
            if exp.met:
                continue

            desc_lower = exp.description.lower()

            # Linguistic
            if exp.gap_type == GapType.LINGUISTIC:
                for lang in langs:
                    if f"'{lang}'" in desc_lower:
                        exp.satisfy(f"Sources found in {lang}")

            # Institutional (language traditions)
            elif (exp.gap_type == GapType.INSTITUTIONAL and
                    "sources checked" in desc_lower):
                for lang in langs:
                    if f"'{lang}'" in desc_lower:
                        exp.satisfy(f"Found in {lang}")

            # Institutional (specific institutions)
            elif (exp.gap_type == GapType.INSTITUTIONAL and
                    "publications from" in desc_lower):
                for inst in institutions:
                    if inst in desc_lower:
                        exp.satisfy(f"Found: {inst}")

            # Voice plurality
            elif exp.gap_type == GapType.VOICE:
                n_scholars = len(postulates.scholars)
                # Extract minimum from description
                match = re.search(r'at least (\d+)', desc_lower)
                if match:
                    minimum = int(match.group(1))
                    if n_scholars >= minimum:
                        exp.satisfy(
                            f"{n_scholars} scholars found"
                        )

            # Theory sourcing
            elif exp.gap_type == GapType.THEORY_UNSOURCED:
                for theory in theories_sourced:
                    # Check if any key words match
                    theory_words = set(
                        w for w in theory.split()
                        if len(w) > 4
                    )
                    desc_words = set(
                        w for w in desc_lower.split()
                        if len(w) > 4
                    )
                    if theory_words & desc_words:
                        exp.satisfy(f"Sourced: {theory}")

            # Source types
            elif exp.gap_type == GapType.SOURCE_TYPE:
                type_map = {
                    "peer-reviewed": {"peer_reviewed", "peer-reviewed"},
                    "institutional": {"institutional"},
                    "journalistic": {"journalistic"},
                }
                for label, matches in type_map.items():
                    if label in desc_lower and types & matches:
                        exp.satisfy(f"Found {label} source")

            # Temporal
            elif exp.gap_type == GapType.TEMPORAL:
                if years:
                    if "last 3" in desc_lower and max(years) >= 2023:
                        exp.satisfy(f"Recent: {max(years)}")
                    if "span" in desc_lower:
                        if (min(years) <= 2014 and
                                max(years) >= 2023):
                            exp.satisfy(
                                f"{min(years)}-{max(years)}"
                            )

            # Entity coverage (scholars to investigate)
            elif exp.gap_type == GapType.ENTITY_UNRESEARCHED:
                # Check if the named scholar is now investigated
                for entity in postulates.entities.values():
                    if (entity.name.lower() in desc_lower and
                            entity.investigated):
                        exp.satisfy(
                            f"{entity.name} now investigated"
                        )


# ============================================================
# AUDIT ENGINE
# ============================================================

class AuditEngine:

    def __init__(
        self,
        expectations: list[Expectation],
        findings: list[Finding],
        postulates: DynamicPostulates,
    ):
        self.expectations = expectations
        self.findings = findings
        self.postulates = postulates
        self.anomalies: list[Anomaly] = []

    def run(self) -> list[Anomaly]:
        self.anomalies = []
        self._check_unmet()
        self._check_monolingual()
        self._check_investigation_ratio()
        return self.anomalies

    def _check_unmet(self):
        for exp in self.expectations:
            if not exp.met:
                self.anomalies.append(Anomaly(
                    description=f"UNMET: {exp.description}",
                    gap_type=exp.gap_type,
                    severity=exp.severity_if_unmet,
                    recommendation=self._rec(exp.gap_type),
                ))

    def _check_monolingual(self):
        langs = set(f.language for f in self.findings)
        needed = set()
        country = self.postulates.country
        geo = GEOGRAPHIC_LINGUISTIC.get(country, {})
        needed.update(geo.get("primary_languages", []))
        needed.add("en")

        missing = needed - langs
        if missing:
            self.anomalies.append(Anomaly(
                description=(
                    f"Primary language(s) not covered: "
                    f"{', '.join(sorted(missing))}"
                ),
                gap_type=GapType.LINGUISTIC,
                severity=Severity.HIGH,
                recommendation=(
                    f"Search in: {', '.join(sorted(missing))}"
                ),
            ))

    def _check_investigation_ratio(self):
        scholars = [
            e for e in self.postulates.entities.values()
            if e.entity_type == EntityType.SCHOLAR
        ]
        if not scholars:
            return

        investigated = sum(1 for s in scholars if s.investigated)
        ratio = investigated / len(scholars)

        if ratio < 0.5:
            uninv = [
                s for s in scholars if not s.investigated
            ]
            # Sort by mention count
            uninv.sort(
                key=lambda e: e.times_mentioned, reverse=True
            )
            top_names = [s.name for s in uninv[:7]]

            self.anomalies.append(Anomaly(
                description=(
                    f"Scholar investigation ratio: "
                    f"{ratio:.0%} ({investigated}/"
                    f"{len(scholars)}). "
                    f"Top uninvestigated: "
                    f"{', '.join(top_names)}"
                ),
                gap_type=GapType.ENTITY_UNRESEARCHED,
                severity=Severity.HIGH,
                recommendation=(
                    f"Search for publications by: "
                    f"{', '.join(top_names)}"
                ),
            ))

    def _rec(self, gap_type: GapType) -> str:
        return {
            GapType.LINGUISTIC: "Search in missing languages",
            GapType.INSTITUTIONAL: "Check this institution",
            GapType.VOICE: "Find more independent scholars",
            GapType.THEORY_UNSOURCED: "Find primary source",
            GapType.SOURCE_TYPE: "Look for this source type",
            GapType.TEMPORAL: "Find more recent sources",
            GapType.ENTITY_UNRESEARCHED: "Investigate this entity",
            GapType.GEOGRAPHIC: "Check geographic perspectives",
        }.get(gap_type, "Investigate further")


# ============================================================
# COVERAGE CALCULATOR
# ============================================================

def calculate_coverage(
    expectations: list[Expectation],
    anomalies: list[Anomaly]
) -> float:
    if not expectations:
        return 0.0

    weights = {
        Severity.LOW: 1, Severity.MEDIUM: 2,
        Severity.HIGH: 3, Severity.CRITICAL: 5
    }

    total = sum(
        weights[e.severity_if_unmet] for e in expectations
    )
    met = sum(
        weights[e.severity_if_unmet]
        for e in expectations if e.met
    )

    if total == 0:
        return 0.0

    base = (met / total) * 100

    penalty = sum(weights[a.severity] * 0.5 for a in anomalies)
    penalty_norm = min(penalty / max(total, 1) * 100, 30)

    return max(base - penalty_norm, 0)


# ============================================================
# THE CYCLE ENGINE — Orchestrates everything
# ============================================================

class EpistemixEngine:
    """
    The main engine. Runs research cycles:
    seed → search → ingest → derive → audit → new queries → repeat
    """

    def __init__(self, country: str, topic: str, discipline: str = ""):
        self.postulates = DynamicPostulates(
            country, topic, discipline
        )
        self.query_gen = MultilingualQueryGenerator(self.postulates)
        self.findings: list[Finding] = []
        self.all_expectations: list[Expectation] = []
        self.all_anomalies: list[Anomaly] = []
        self.pending_queries: list[SearchQuery] = []
        self.cycle_history: list[CycleSnapshot] = []
        self.current_cycle = 0

    def initialize(self) -> list[SearchQuery]:
        """
        Step 0: Generate initial multilingual queries.
        Returns queries that should be executed.
        """
        self.pending_queries = self.query_gen.generate_initial_queries()
        return self.pending_queries

    def ingest_findings(
        self, new_findings: list[Finding]
    ) -> list[str]:
        """
        Ingest new findings into the system.
        Returns list of all newly discovered entities.
        """
        all_new = []
        for f in new_findings:
            f.cycle = self.current_cycle
            self.findings.append(f)
            new_entities = self.postulates.ingest_finding(f)
            all_new.extend(new_entities)
        return all_new

    def run_cycle(self) -> CycleSnapshot:
        """
        Run one complete audit cycle:
        1. Derive expectations from current postulates
        2. Check which are satisfied
        3. Run audit
        4. Generate gap-filling queries
        5. Snapshot state
        """
        self.current_cycle += 1

        # 1. Derive expectations
        inferrer = DynamicInferenceEngine(self.postulates)
        self.all_expectations = inferrer.derive(self.current_cycle)

        # 2. Satisfy expectations
        ExpectationSatisfier.satisfy(
            self.all_expectations, self.findings, self.postulates
        )

        # 3. Audit
        auditor = AuditEngine(
            self.all_expectations, self.findings, self.postulates
        )
        self.all_anomalies = auditor.run()

        # 4. Generate new queries for gaps
        self.pending_queries = (
            self.query_gen.generate_gap_filling_queries(
                self.all_anomalies
            )
        )

        # 5. Snapshot
        coverage = calculate_coverage(
            self.all_expectations, self.all_anomalies
        )
        snapshot = CycleSnapshot(
            cycle=self.current_cycle,
            n_postulate_scholars=len(self.postulates.scholars),
            n_postulate_theories=len(self.postulates.theories),
            n_postulate_institutions=len(
                self.postulates.institutions
            ),
            n_expectations=len(self.all_expectations),
            n_expectations_met=sum(
                1 for e in self.all_expectations if e.met
            ),
            n_findings=len(self.findings),
            n_anomalies=len(self.all_anomalies),
            coverage_score=coverage,
            queries_generated=len(self.pending_queries),
        )
        self.cycle_history.append(snapshot)

        return snapshot

    def report(self) -> str:
        """Generate full report of current state."""
        lines = []
        lines.append("=" * 64)
        lines.append("  EPISTEMIX v2 — Dynamic Epistemic Audit")
        lines.append(
            f"  Cycle {self.current_cycle}"
        )
        lines.append("=" * 64)

        # Postulates (dynamically built)
        lines.append("\n📋 DYNAMIC POSTULATES")
        lines.append("-" * 50)
        lines.append(self.postulates.describe())

        # Expectations
        met = sum(1 for e in self.all_expectations if e.met)
        total = len(self.all_expectations)
        pct = (met / total * 100) if total > 0 else 0
        lines.append(
            f"\n📐 EXPECTATIONS: {met}/{total} met ({pct:.0f}%)"
        )
        lines.append("-" * 50)
        for exp in self.all_expectations:
            lines.append(f"  {exp}")

        # Findings summary
        lines.append(
            f"\n🔍 FINDINGS: {len(self.findings)} sources"
        )
        lines.append("-" * 50)
        langs = set(f.language for f in self.findings)
        lines.append(
            f"  Languages: {', '.join(sorted(langs))}"
        )
        lines.append(
            f"  Authors: {', '.join(sorted(self.postulates.scholars))}"
        )

        # Anomalies
        lines.append(
            f"\n⚠️  ANOMALIES: {len(self.all_anomalies)}"
        )
        lines.append("-" * 50)
        sorted_anom = sorted(
            self.all_anomalies,
            key=lambda a: a.severity.value,
            reverse=True,
        )
        for a in sorted_anom:
            lines.append(f"  {a}")
            lines.append(f"    → {a.recommendation}")

        # Pending queries
        lines.append(
            f"\n🔎 SUGGESTED QUERIES: {len(self.pending_queries)}"
        )
        lines.append("-" * 50)
        for q in self.pending_queries[:15]:
            lines.append(f"  {q}")
            lines.append(f"    Rationale: {q.rationale}")
        if len(self.pending_queries) > 15:
            lines.append(
                f"  ... and {len(self.pending_queries) - 15} more"
            )

        # Coverage
        coverage = calculate_coverage(
            self.all_expectations, self.all_anomalies
        )
        lines.append(f"\n📊 COVERAGE: {coverage:.0f}%")
        lines.append("-" * 50)
        if coverage >= 80:
            lines.append(
                "  Good. Check remaining gaps before concluding."
            )
        elif coverage >= 60:
            lines.append(
                "  Moderate. Gaps may affect conclusions."
            )
        elif coverage >= 40:
            lines.append(
                "  Insufficient. Conclusions unreliable."
            )
        else:
            lines.append(
                "  Poor. Do not draw conclusions yet."
            )

        # Evolution across cycles
        if len(self.cycle_history) > 1:
            lines.append(f"\n📈 EVOLUTION")
            lines.append("-" * 50)
            lines.append(
                f"  {'Cycle':>5} {'Scholars':>8} "
                f"{'Theories':>8} {'Expect':>6} "
                f"{'Met':>4} {'Anom':>4} {'Cover':>6}"
            )
            for snap in self.cycle_history:
                lines.append(
                    f"  {snap.cycle:>5} "
                    f"{snap.n_postulate_scholars:>8} "
                    f"{snap.n_postulate_theories:>8} "
                    f"{snap.n_expectations:>6} "
                    f"{snap.n_expectations_met:>4} "
                    f"{snap.n_anomalies:>4} "
                    f"{snap.coverage_score:>5.0f}%"
                )

        # Disclaimer
        lines.append(f"\n⚡ EPISTEMOLOGICAL NOTE")
        lines.append("-" * 50)
        lines.append(
            "  Coverage score = LOWER BOUND on completeness."
        )
        lines.append(
            "  Unknown unknowns remain undetectable."
        )
        lines.append(
            "  Dynamic postulates reduce but do not eliminate"
        )
        lines.append(
            "  blind spots. External review recommended."
        )

        lines.append("\n" + "=" * 64)
        return "\n".join(lines)
