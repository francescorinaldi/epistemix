"""EPISTEMIX v2 — Dynamic Epistemic Engine.

Core engine with dynamic postulates, multilingual query generation,
expectation derivation, satisfaction checking, and audit.

Architecture:
  Seed Input → Query Gen → Findings → Ingester → Inference →
  Auditor → New Queries → (loop)

Based on the founder's v2 design. Postulates are DYNAMIC: they grow
as findings are ingested. Every new scholar, institution, or theory
mentioned in a finding becomes a new postulate.

Classes:
  DynamicPostulates      — manages entity/theory/language tracking
  MultilingualQueryGenerator — generates seed and gap-filling queries
  DynamicInferenceEngine — derives expectations from current state
  ExpectationSatisfier   — checks which expectations are met
  AuditEngine            — detects unmet expectations and anomalies
  EpistemixEngine         — the main orchestrator
"""

from __future__ import annotations

from typing import Any

from epistemix.models import (
    Anomaly,
    CycleSnapshot,
    Entity,
    EntityType,
    Expectation,
    Finding,
    GapType,
    NegativePostulate,
    SearchQuery,
    Severity,
    WeightedPostulate,
)
from epistemix.knowledge import (
    EntityRegistry,
    GEOGRAPHIC_LINGUISTIC,
    KNOWN_TRANSLITERATIONS,
    STOPWORDS,
    TRANSLITERATIONS,
    classify_entity_name,
)
from epistemix.semantic_graph import SemanticGraph


# ============================================================
# DECAY RATES BY DOMAIN (Phase 7)
# ============================================================

DECAY_RATES: dict[str, float] = {
    "archaeology": 0.02,
    "history": 0.03,
    "medicine": 0.08,
    "finance": 0.15,
    "virology": 0.10,
    "law": 0.05,
    "default": 0.02,
}

# Confidence calculation constants (Phase 1)
_CONFIDENCE_BASE = {1: 0.2, 2: 0.4, 3: 0.6, 4: 0.7, 5: 0.8}
_MAX_LANGUAGE_BONUS = 0.2


# ============================================================
# DYNAMIC POSTULATES
# ============================================================

class DynamicPostulates:
    """Postulates that grow as research progresses.

    Starts with minimal seed info; expands with each finding.
    Tracks entities (scholars, institutions, theories) discovered
    so far and their investigation status.
    """

    def __init__(
        self,
        country: str,
        topic: str,
        discipline: str = "",
        entity_registry: EntityRegistry | None = None,
    ) -> None:
        self.country = country
        self.topic = topic
        self.discipline = discipline
        self.discovery_year: int = 0
        self.ongoing: bool = True

        # Shared entity registry for dynamic classification
        self.entity_registry = entity_registry or EntityRegistry()

        # These grow dynamically
        self.entities: dict[str, Entity] = {}
        self.theories: list[str] = []
        self.languages_covered: set[str] = set()
        self.institutions: set[str] = set()
        self.scholars: set[str] = set()

        # Track evolution
        self.history: list[dict] = []

        # v3: Weighted postulates (Phase 1)
        self.weighted_postulates: dict[str, WeightedPostulate] = {}

        # v3: Negative postulates (Phase 2)
        self.negative_postulates: list[NegativePostulate] = []

    def ingest_finding(self, finding: Finding) -> list[str]:
        """Process a finding: extract entities, update postulates.
        Returns list of NEW entity names discovered.
        """
        new_entities: list[str] = []

        # Track language
        self.languages_covered.add(finding.language)

        # Process author
        if finding.author:
            canonical_author = self.entity_registry.normalize(finding.author)
            if self._register_entity(
                finding.author, EntityType.SCHOLAR,
                finding.source, finding.language,
                institution=finding.institution,
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
                finding.source, finding.language,
            ):
                new_entities.append(finding.institution)
            self.institutions.add(finding.institution)

        # Process theory
        if (
            finding.theory_supported
            and finding.theory_supported not in self.theories
        ):
            self.theories.append(finding.theory_supported)

        # Process mentioned entities
        for name in finding.entities_mentioned:
            entity_type_str = self.entity_registry.classify(name)
            entity_type = EntityType(entity_type_str)
            if self._register_entity(
                name, entity_type,
                finding.source, finding.language,
            ):
                new_entities.append(name)
            else:
                # Already known — increment mention count
                key = self.entity_registry.normalize(name).lower()
                if key in self.entities:
                    self.entities[key].times_mentioned += 1
                    self.entities[key].languages_seen_in.add(finding.language)

        # v3: Update weighted postulates (Phase 1)
        self._update_weighted_postulates(finding, finding.cycle)

        return new_entities

    def _register_entity(
        self,
        name: str,
        entity_type: EntityType,
        source: str,
        language: str,
        institution: str = "",
    ) -> bool:
        """Register entity if new. Returns True if new."""
        canonical = self.entity_registry.normalize(name)
        key = canonical.lower()

        if key in self.entities:
            self.entities[key].times_mentioned += 1
            self.entities[key].languages_seen_in.add(language)
            return False

        self.entities[key] = Entity(
            name=canonical,
            entity_type=entity_type,
            first_seen_in=source,
            times_mentioned=1,
            investigated=False,
            languages_seen_in={language},
            affiliated_institution=institution,
        )
        return True

    def _update_weighted_postulates(
        self, finding: Finding, cycle: int,
    ) -> None:
        """Update weighted postulates from a finding (Phase 1).

        For each entity/theory/institution in the finding, find or create
        a WeightedPostulate and update its confidence score.
        """
        decay_rate = DECAY_RATES.get(
            self.discipline.lower(), DECAY_RATES["default"]
        )
        subjects: list[tuple[str, str]] = []

        if finding.author:
            subjects.append((finding.author, "MA-02"))
        if finding.institution:
            subjects.append((finding.institution, "MA-02"))
        if finding.theory_supported:
            subjects.append((finding.theory_supported, "MA-03"))
        for name in finding.entities_mentioned:
            subjects.append((name, "MA-05"))

        for subject, axiom_id in subjects:
            key = subject.lower().strip()
            if not key:
                continue

            if key not in self.weighted_postulates:
                self.weighted_postulates[key] = WeightedPostulate(
                    description=subject,
                    meta_axiom_id=axiom_id,
                    source_count=0,
                    language_spread=0,
                    confidence=0.0,
                    last_confirmed_cycle=cycle,
                    decay_rate=decay_rate,
                )

            wp = self.weighted_postulates[key]
            wp.source_count += 1
            wp.last_confirmed_cycle = cycle

            # Count distinct languages across all findings for this subject
            langs = set()
            for entity in self.entities.values():
                if entity.name.lower().strip() == key:
                    langs = entity.languages_seen_in
                    break
            langs.add(finding.language)
            wp.language_spread = len(langs)

            # Confidence = base_from_sources × language_bonus
            sc = wp.source_count
            base = _CONFIDENCE_BASE.get(
                min(sc, 5), 0.8 + 0.02 * min(sc - 5, 10)
            )
            lang_bonus = min(
                _MAX_LANGUAGE_BONUS,
                (wp.language_spread - 1) * 0.1,
            )
            wp.confidence = min(1.0, base + lang_bonus)

    def register_negative_postulate(self, neg: NegativePostulate) -> None:
        """Register a negative postulate (Phase 2)."""
        self.negative_postulates.append(neg)

    def get_uninvestigated_scholars(self) -> list[Entity]:
        """Scholars mentioned but not yet investigated (no publication found)."""
        return [
            e for e in self.entities.values()
            if e.entity_type == EntityType.SCHOLAR
            and not e.investigated
            and e.times_mentioned >= 1
        ]

    def get_uninvestigated_institutions(self) -> list[Entity]:
        """Institutions mentioned but not yet investigated."""
        return [
            e for e in self.entities.values()
            if e.entity_type == EntityType.INSTITUTION
            and not e.investigated
        ]

    def snapshot(self) -> dict[str, Any]:
        """Return current state as a dict."""
        wps = list(self.weighted_postulates.values())
        avg_conf = (
            sum(wp.confidence for wp in wps) / len(wps) if wps else 0.0
        )
        return {
            "scholars": len(self.scholars),
            "theories": len(self.theories),
            "institutions": len(self.institutions),
            "total_entities": len(self.entities),
            "languages": sorted(self.languages_covered),
            "weighted_postulates": len(wps),
            "avg_confidence": round(avg_conf, 3),
            "negative_postulates": len(self.negative_postulates),
        }

    def describe(self) -> str:
        """Human-readable description of current postulate state."""
        lines = [
            f"Topic: {self.topic}",
            f"Country: {self.country}",
            f"Discipline: {self.discipline}",
            f"Scholars tracked: {len(self.scholars)}",
            f"Theories: {len(self.theories)}",
            f"Institutions: {len(self.institutions)}",
            f"Languages covered: {', '.join(sorted(self.languages_covered))}",
            f"Total entities: {len(self.entities)}",
        ]
        uninvestigated = self.get_uninvestigated_scholars()
        if uninvestigated:
            top = sorted(uninvestigated, key=lambda e: -e.times_mentioned)[:5]
            lines.append(f"Uninvestigated scholars (top {len(top)}):")
            for e in top:
                lines.append(
                    f"  - {e.name} (mentioned {e.times_mentioned}x)"
                )
        # v3: confidence distribution
        if self.weighted_postulates:
            wps = list(self.weighted_postulates.values())
            avg = sum(wp.confidence for wp in wps) / len(wps)
            by_action = {}
            for wp in wps:
                by_action[wp.action] = by_action.get(wp.action, 0) + 1
            lines.append(f"Weighted postulates: {len(wps)} (avg confidence: {avg:.2f})")
            for action, count in sorted(by_action.items()):
                lines.append(f"  - {action}: {count}")
        if self.negative_postulates:
            lines.append(f"Negative postulates: {len(self.negative_postulates)}")
        return "\n".join(lines)


# ============================================================
# MULTILINGUAL QUERY GENERATOR
# ============================================================

class MultilingualQueryGenerator:
    """Generates multilingual search queries from postulate state."""

    def __init__(self, postulates: DynamicPostulates) -> None:
        self.postulates = postulates

    def generate_initial_queries(self) -> list[SearchQuery]:
        """Generate seed queries in all relevant languages."""
        queries: list[SearchQuery] = []
        topic = self.postulates.topic
        country = self.postulates.country
        discipline = self.postulates.discipline

        geo = GEOGRAPHIC_LINGUISTIC.get(country, {})
        primary_langs = geo.get("primary_languages", ["en"])
        foreign = geo.get("foreign_traditions", {})

        # Queries in primary languages
        for lang in primary_langs:
            if lang == "en":
                queries.append(SearchQuery(
                    query=f"{topic} {discipline} research {country}",
                    language="en",
                    rationale=f"Seed English query for {topic}",
                    priority=Severity.HIGH,
                    target_gap=GapType.LINGUISTIC,
                ))
            else:
                # Translate key terms if possible
                translated_terms = []
                for term in self._extract_key_terms(topic):
                    translated = self._transliterate(term, lang)
                    translated_terms.append(translated)
                if translated_terms:
                    q = " ".join(translated_terms)
                    queries.append(SearchQuery(
                        query=q,
                        language=lang,
                        rationale=f"Seed query in {lang} for {topic}",
                        priority=Severity.HIGH,
                        target_gap=GapType.LINGUISTIC,
                    ))

        # Queries for foreign academic traditions
        for lang, tradition_name in foreign.items():
            if lang not in primary_langs:
                translated = self._transliterate(topic, lang)
                queries.append(SearchQuery(
                    query=f"{translated} {discipline} {tradition_name}",
                    language=lang,
                    rationale=f"Foreign tradition: {tradition_name}",
                    priority=Severity.MEDIUM,
                    target_gap=GapType.INSTITUTIONAL,
                ))

        # Academic English query
        queries.append(SearchQuery(
            query=f'"{topic}" academic research peer-reviewed {discipline}',
            language="en",
            rationale="Academic peer-reviewed sources",
            priority=Severity.MEDIUM,
            target_gap=GapType.SOURCE_TYPE,
        ))

        return queries

    def generate_gap_filling_queries(
        self, anomalies: list[Anomaly]
    ) -> list[SearchQuery]:
        """Generate targeted queries to fill detected gaps."""
        queries: list[SearchQuery] = []
        seen: set[tuple[str, str]] = set()

        for anomaly in anomalies:
            gap = anomaly.gap_type

            if gap == GapType.ENTITY_UNRESEARCHED:
                uninvestigated = self.postulates.get_uninvestigated_scholars()
                top = sorted(
                    uninvestigated, key=lambda e: -e.times_mentioned
                )[:5]
                for entity in top:
                    for lang in self._relevant_languages():
                        q = f"{entity.name} {self.postulates.topic} research"
                        key = (q.lower(), lang)
                        if key not in seen:
                            seen.add(key)
                            queries.append(SearchQuery(
                                query=q,
                                language=lang,
                                rationale=f"Investigate {entity.name}",
                                priority=Severity.HIGH,
                                target_gap=GapType.ENTITY_UNRESEARCHED,
                            ))

            elif gap == GapType.LINGUISTIC:
                covered = self.postulates.languages_covered
                for lang in self._relevant_languages():
                    if lang not in covered:
                        translated = self._transliterate(
                            self.postulates.topic, lang
                        )
                        q = f"{translated} research"
                        key = (q.lower(), lang)
                        if key not in seen:
                            seen.add(key)
                            queries.append(SearchQuery(
                                query=q,
                                language=lang,
                                rationale=f"Fill language gap: {lang}",
                                priority=Severity.HIGH,
                                target_gap=GapType.LINGUISTIC,
                            ))

            elif gap == GapType.INSTITUTIONAL:
                uninvestigated = (
                    self.postulates.get_uninvestigated_institutions()
                )
                for inst in uninvestigated[:3]:
                    q = f"{inst.name} {self.postulates.topic} publications"
                    key = (q.lower(), "en")
                    if key not in seen:
                        seen.add(key)
                        queries.append(SearchQuery(
                            query=q,
                            language="en",
                            rationale=f"Investigate institution: {inst.name}",
                            priority=Severity.MEDIUM,
                            target_gap=GapType.INSTITUTIONAL,
                        ))

            elif gap == GapType.THEORY_UNSOURCED:
                for theory in self.postulates.theories:
                    q = (
                        f'"{theory}" academic paper peer-reviewed '
                        f"{self.postulates.topic}"
                    )
                    key = (q.lower(), "en")
                    if key not in seen:
                        seen.add(key)
                        queries.append(SearchQuery(
                            query=q,
                            language="en",
                            rationale=f"Find peer-reviewed source for: {theory}",
                            priority=Severity.HIGH,
                            target_gap=GapType.THEORY_UNSOURCED,
                        ))

            # Use anomaly's own suggested queries
            for sq in anomaly.suggested_queries:
                key = (sq.lower(), "en")
                if key not in seen:
                    seen.add(key)
                    queries.append(SearchQuery(
                        query=sq,
                        language="en",
                        rationale=f"Anomaly-suggested: {anomaly.description[:40]}",
                        priority=anomaly.severity,
                        target_gap=anomaly.gap_type,
                    ))

        # v3 Phase 2: Add reformulated queries from negative postulates
        for neg in self.postulates.negative_postulates:
            if neg.reformulation:
                key = (neg.reformulation.lower(), neg.language)
                if key not in seen:
                    seen.add(key)
                    queries.append(SearchQuery(
                        query=neg.reformulation,
                        language=neg.language,
                        rationale=(
                            f"Reformulation (attempt {neg.attempts + 1}): "
                            f"original '{neg.query_text[:30]}' returned nothing"
                        ),
                        priority=Severity.MEDIUM,
                        target_gap=GapType.EMPTY_QUERY_PATTERN,
                    ))

        return queries

    def generate_confidence_queries(self) -> list[SearchQuery]:
        """Generate queries driven by postulate confidence (Phase 1).

        Low-confidence postulates (< 0.3) get verification queries.
        High-confidence postulates (> 0.8) with few sources get
        deepening queries in underrepresented languages.
        """
        queries: list[SearchQuery] = []
        seen: set[tuple[str, str]] = set()

        for key, wp in self.postulates.weighted_postulates.items():
            if wp.confidence < 0.3 and wp.source_count >= 1:
                # VERIFY: try to confirm this postulate
                q = (
                    f'"{wp.description}" '
                    f"{self.postulates.topic} research"
                )
                qkey = (q.lower(), "en")
                if qkey not in seen:
                    seen.add(qkey)
                    queries.append(SearchQuery(
                        query=q,
                        language="en",
                        rationale=(
                            f"Verify low-confidence postulate "
                            f"({wp.confidence:.0%}): {wp.description}"
                        ),
                        priority=Severity.MEDIUM,
                        target_gap=GapType.VOICE,
                    ))

            elif wp.confidence > 0.8 and wp.language_spread < 2:
                # DEEPEN: try other languages for well-known subjects
                for lang in self._relevant_languages():
                    if lang != "en":
                        translated = self._transliterate(
                            wp.description, lang
                        )
                        q = f"{translated} {self.postulates.topic}"
                        qkey = (q.lower(), lang)
                        if qkey not in seen:
                            seen.add(qkey)
                            queries.append(SearchQuery(
                                query=q,
                                language=lang,
                                rationale=(
                                    f"Deepen reliable postulate in {lang}: "
                                    f"{wp.description}"
                                ),
                                priority=Severity.LOW,
                                target_gap=GapType.LINGUISTIC,
                            ))
                            break  # one deepening query per postulate

        return queries

    def _relevant_languages(self) -> set[str]:
        """All languages relevant to this country."""
        geo = GEOGRAPHIC_LINGUISTIC.get(self.postulates.country, {})
        langs = set(geo.get("primary_languages", []))
        langs.update(geo.get("foreign_traditions", {}).keys())
        langs.add("en")
        return langs

    def _extract_key_terms(self, topic: str) -> list[str]:
        """Extract searchable terms from a topic string."""
        import re
        words = re.split(r"[\s,;.\-/]+", topic)
        return [
            w for w in words
            if len(w) > 3 and w.lower() not in STOPWORDS
        ]

    def _transliterate(self, term: str, language: str) -> str:
        """Translate a term to another language if possible."""
        for name, translations in TRANSLITERATIONS.items():
            if term.lower() == name.lower() and language in translations:
                return translations[language]

        geo = GEOGRAPHIC_LINGUISTIC.get(self.postulates.country, {})
        trans_map = geo.get("transliteration_map", {})
        if language in trans_map:
            for eng, local in trans_map[language].items():
                if eng.lower() in term.lower():
                    return term.lower().replace(eng.lower(), local)

        return term


# ============================================================
# DYNAMIC INFERENCE ENGINE
# ============================================================

class DynamicInferenceEngine:
    """Derives expectations from the current state of postulates.

    Each sub-method corresponds to a meta-axiom:
      _linguistic      → MA-01 Linguistic Diversity
      _institutional   → MA-02 Institutional Multiplicity
      _plurality       → MA-03 Theoretical Pluralism + MA-04 School Formation
      _source_types    → MA-06 Publication Channels
      _temporal        → MA-07 Temporal Evolution
      _entity_coverage → MA-05 Disciplinary Breadth
    """

    MIN_VOICES_PER_THEORY = 2
    EXPECTED_VOICES_RATIO = 3
    MIN_INVESTIGATION_RATIO = 0.5

    def __init__(self, postulates: DynamicPostulates) -> None:
        self.postulates = postulates

    def derive(self, cycle: int) -> list[Expectation]:
        """Derive all expectations for the current cycle."""
        expectations: list[Expectation] = []
        expectations.extend(self._linguistic(cycle))
        expectations.extend(self._plurality(cycle))
        expectations.extend(self._source_types(cycle))
        expectations.extend(self._temporal(cycle))
        expectations.extend(self._entity_coverage(cycle))
        expectations.extend(self._institutional(cycle))
        return expectations

    def _linguistic(self, cycle: int) -> list[Expectation]:
        """Expectations for primary language coverage and foreign traditions."""
        expectations: list[Expectation] = []
        geo = GEOGRAPHIC_LINGUISTIC.get(self.postulates.country, {})

        for lang in geo.get("primary_languages", []):
            expectations.append(Expectation(
                description=f"Sources in '{lang}' language found",
                gap_type=GapType.LINGUISTIC,
                severity_if_unmet=Severity.HIGH,
                derived_in_cycle=cycle,
            ))

        for lang, tradition in geo.get("foreign_traditions", {}).items():
            expectations.append(Expectation(
                description=f"Sources checked from {tradition} ({lang})",
                gap_type=GapType.INSTITUTIONAL,
                severity_if_unmet=Severity.MEDIUM,
                derived_in_cycle=cycle,
            ))

        return expectations

    def _plurality(self, cycle: int) -> list[Expectation]:
        """Expectations for theoretical pluralism and voice diversity."""
        expectations: list[Expectation] = []
        n_theories = len(self.postulates.theories)

        if n_theories > 0:
            min_scholars = n_theories * self.MIN_VOICES_PER_THEORY
            expectations.append(Expectation(
                description=(
                    f"At least {min_scholars} scholars supporting "
                    f"{n_theories} theories"
                ),
                gap_type=GapType.VOICE,
                severity_if_unmet=Severity.MEDIUM,
                derived_in_cycle=cycle,
            ))

            for theory in self.postulates.theories:
                expectations.append(Expectation(
                    description=f"Peer-reviewed source for theory: {theory}",
                    gap_type=GapType.THEORY_UNSOURCED,
                    severity_if_unmet=Severity.HIGH,
                    derived_in_cycle=cycle,
                ))

        return expectations

    def _source_types(self, cycle: int) -> list[Expectation]:
        """Expectations for source type diversity."""
        return [
            Expectation(
                description="Peer-reviewed sources found",
                gap_type=GapType.SOURCE_TYPE,
                severity_if_unmet=Severity.HIGH,
                derived_in_cycle=cycle,
            ),
            Expectation(
                description="Institutional sources found",
                gap_type=GapType.SOURCE_TYPE,
                severity_if_unmet=Severity.MEDIUM,
                derived_in_cycle=cycle,
            ),
            Expectation(
                description="Quality journalistic sources found",
                gap_type=GapType.SOURCE_TYPE,
                severity_if_unmet=Severity.LOW,
                derived_in_cycle=cycle,
            ),
        ]

    def _temporal(self, cycle: int) -> list[Expectation]:
        """Expectations for temporal coverage."""
        expectations: list[Expectation] = []
        if self.postulates.ongoing:
            expectations.append(Expectation(
                description="Sources from last 3 years found",
                gap_type=GapType.TEMPORAL,
                severity_if_unmet=Severity.MEDIUM,
                derived_in_cycle=cycle,
            ))
        if self.postulates.discovery_year > 0:
            expectations.append(Expectation(
                description=(
                    f"Sources span from {self.postulates.discovery_year} "
                    "to present"
                ),
                gap_type=GapType.TEMPORAL,
                severity_if_unmet=Severity.MEDIUM,
                derived_in_cycle=cycle,
            ))
        return expectations

    def _entity_coverage(self, cycle: int) -> list[Expectation]:
        """DYNAMIC: expect investigation of frequently-mentioned scholars."""
        expectations: list[Expectation] = []
        for entity in self.postulates.entities.values():
            if (
                entity.entity_type == EntityType.SCHOLAR
                and entity.times_mentioned >= 2
                and not entity.investigated
            ):
                expectations.append(Expectation(
                    description=(
                        f"Scholar '{entity.name}' investigated "
                        f"(mentioned {entity.times_mentioned}x)"
                    ),
                    gap_type=GapType.ENTITY_UNRESEARCHED,
                    severity_if_unmet=Severity.HIGH,
                    derived_in_cycle=cycle,
                ))
        return expectations

    def _institutional(self, cycle: int) -> list[Expectation]:
        """Expectations for institutional publication review."""
        expectations: list[Expectation] = []
        for inst in self.postulates.institutions:
            expectations.append(Expectation(
                description=f"Publications from {inst} reviewed",
                gap_type=GapType.INSTITUTIONAL,
                severity_if_unmet=Severity.MEDIUM,
                derived_in_cycle=cycle,
            ))
        return expectations


# ============================================================
# EXPECTATION SATISFIER
# ============================================================

class ExpectationSatisfier:
    """Checks which expectations are met by current findings."""

    @staticmethod
    def satisfy(
        expectations: list[Expectation],
        findings: list[Finding],
        postulates: DynamicPostulates,
    ) -> None:
        """Mark expectations as satisfied based on findings."""
        import re as _re

        langs = set(f.language for f in findings)
        types = set(f.source_type for f in findings)
        authors = set(f.author.lower() for f in findings if f.author)
        years = [f.year for f in findings if f.year > 0]
        institutions = set(
            f.institution.lower() for f in findings if f.institution
        )

        theories_sourced: set[str] = set()
        for f in findings:
            if f.theory_supported and f.source_type in (
                "peer_reviewed", "peer-reviewed"
            ):
                theories_sourced.add(f.theory_supported.lower())

        for exp in expectations:
            if exp.met:
                continue

            desc_lower = exp.description.lower()

            if exp.gap_type == GapType.LINGUISTIC:
                for lang in langs:
                    if f"'{lang}'" in desc_lower:
                        exp.satisfy(f"Found sources in {lang}")
                        break

            elif exp.gap_type == GapType.INSTITUTIONAL:
                if "sources checked" in desc_lower:
                    for lang in langs:
                        if f"({lang})" in desc_lower:
                            exp.satisfy(f"Sources found in {lang}")
                            break
                elif "publications from" in desc_lower:
                    for inst in institutions:
                        if inst in desc_lower:
                            exp.satisfy(f"Publications from {inst}")
                            break

            elif exp.gap_type == GapType.VOICE:
                match = _re.search(r"at least (\d+)", desc_lower)
                if match:
                    minimum = int(match.group(1))
                    if len(authors) >= minimum:
                        exp.satisfy(f"{len(authors)} scholars found")

            elif exp.gap_type == GapType.THEORY_UNSOURCED:
                for theory in theories_sourced:
                    theory_words = {
                        w for w in theory.split() if len(w) > 4
                    }
                    desc_words = {
                        w for w in desc_lower.split() if len(w) > 4
                    }
                    if theory_words & desc_words:
                        exp.satisfy(f"Peer-reviewed source: {theory}")
                        break

            elif exp.gap_type == GapType.SOURCE_TYPE:
                source_type_map = {
                    "peer-reviewed": {"peer_reviewed", "peer-reviewed"},
                    "institutional": {"institutional", "government"},
                    "journalistic": {"news", "journalistic", "media"},
                }
                for label, accepted in source_type_map.items():
                    if label in desc_lower and types & accepted:
                        exp.satisfy(f"Found {label} sources")
                        break

            elif exp.gap_type == GapType.TEMPORAL:
                if "last 3" in desc_lower and years:
                    if max(years) >= 2023:
                        exp.satisfy(f"Recent source: {max(years)}")
                elif "span" in desc_lower and len(years) >= 2:
                    span = max(years) - min(years)
                    if span >= 5:
                        exp.satisfy(f"Temporal span: {span} years")

            elif exp.gap_type == GapType.ENTITY_UNRESEARCHED:
                for entity in postulates.entities.values():
                    if (
                        entity.name.lower() in desc_lower
                        and entity.investigated
                    ):
                        exp.satisfy(f"{entity.name} now investigated")
                        break


# ============================================================
# AUDIT ENGINE
# ============================================================

class AuditEngine:
    """Detects anomalies from unmet expectations and structural issues."""

    _RECOMMENDATIONS: dict[str, str] = {
        GapType.LINGUISTIC.value: "Search in the missing language(s)",
        GapType.INSTITUTIONAL.value: "Check publications from this institution",
        GapType.VOICE.value: "Find more scholars working on this topic",
        GapType.SOURCE_TYPE.value: "Search for this type of source",
        GapType.ENTITY_UNRESEARCHED.value: "Investigate this scholar's work",
        GapType.THEORY_UNSOURCED.value: "Find peer-reviewed source for this theory",
        GapType.TEMPORAL.value: "Search for more recent or historical sources",
        GapType.GEOGRAPHIC.value: "Expand geographic scope of search",
    }

    def __init__(
        self,
        expectations: list[Expectation],
        findings: list[Finding],
        postulates: DynamicPostulates,
    ) -> None:
        self.expectations = expectations
        self.findings = findings
        self.postulates = postulates
        self.anomalies: list[Anomaly] = []

    def run(self) -> list[Anomaly]:
        """Run all anomaly checks."""
        self.anomalies = []
        self._check_unmet()
        self._check_monolingual()
        self._check_investigation_ratio()
        return self.anomalies

    def _check_unmet(self) -> None:
        """Create an anomaly for each unmet expectation."""
        for exp in self.expectations:
            if not exp.met:
                rec = self._RECOMMENDATIONS.get(
                    exp.gap_type.value, "Investigate further",
                )
                self.anomalies.append(Anomaly(
                    description=f"Unmet: {exp.description}",
                    gap_type=exp.gap_type,
                    severity=exp.severity_if_unmet,
                    recommendation=rec,
                ))

    def _check_monolingual(self) -> None:
        """Check if primary languages of the country are covered."""
        geo = GEOGRAPHIC_LINGUISTIC.get(self.postulates.country, {})
        primary = set(geo.get("primary_languages", []))
        covered = self.postulates.languages_covered

        for lang in primary:
            if lang not in covered:
                self.anomalies.append(Anomaly(
                    description=(
                        f"Primary language '{lang}' of "
                        f"{self.postulates.country} not covered"
                    ),
                    gap_type=GapType.LINGUISTIC,
                    severity=Severity.HIGH,
                    recommendation=f"Search in {lang}",
                ))

    def _check_investigation_ratio(self) -> None:
        """Flag if too few scholars are investigated."""
        scholars = [
            e for e in self.postulates.entities.values()
            if e.entity_type == EntityType.SCHOLAR
        ]
        if not scholars:
            return

        investigated = sum(1 for s in scholars if s.investigated)
        ratio = investigated / len(scholars)

        if ratio < DynamicInferenceEngine.MIN_INVESTIGATION_RATIO:
            uninvestigated = [s for s in scholars if not s.investigated]
            top = sorted(
                uninvestigated, key=lambda e: -e.times_mentioned
            )[:7]
            names = ", ".join(e.name for e in top)
            self.anomalies.append(Anomaly(
                description=(
                    f"Only {investigated}/{len(scholars)} scholars "
                    f"investigated ({ratio:.0%}). "
                    f"Top uninvestigated: {names}"
                ),
                gap_type=GapType.ENTITY_UNRESEARCHED,
                severity=Severity.HIGH,
                recommendation="Investigate the listed scholars",
            ))


# ============================================================
# COVERAGE CALCULATION
# ============================================================

def calculate_coverage(
    expectations: list[Expectation],
    anomalies: list[Anomaly],
) -> float:
    """Calculate weighted coverage score (0-100).

    Uses severity weights: LOW=1, MEDIUM=2, HIGH=3, CRITICAL=5.
    Anomalies penalize the score (up to -30 points).
    """
    if not expectations:
        return 0.0

    weighted_total = 0.0
    weighted_met = 0.0

    for exp in expectations:
        w = exp.severity_if_unmet.weight
        weighted_total += w
        if exp.met:
            weighted_met += w

    base = (weighted_met / weighted_total) * 100 if weighted_total > 0 else 0

    penalty = sum(a.severity.weight * 0.5 for a in anomalies)
    penalty_norm = min(penalty, 30)

    return max(base - penalty_norm, 0.0)


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

class EpistemixEngine:
    """The main epistemic audit engine.

    Usage:
        engine = EpistemixEngine("Greece", "Amphipolis tomb", "archaeology")
        queries = engine.initialize()
        # Execute queries via connector, get findings
        new_entities = engine.ingest_findings(findings)
        snapshot = engine.run_cycle()
        # Repeat for more cycles
    """

    def __init__(
        self,
        country: str,
        topic: str,
        discipline: str = "",
        entity_registry: EntityRegistry | None = None,
    ) -> None:
        self.entity_registry = entity_registry or EntityRegistry()
        self.postulates = DynamicPostulates(
            country, topic, discipline,
            entity_registry=self.entity_registry,
        )
        self.query_gen = MultilingualQueryGenerator(self.postulates)
        self.findings: list[Finding] = []
        self.all_expectations: list[Expectation] = []
        self.all_anomalies: list[Anomaly] = []
        self.pending_queries: list[SearchQuery] = []
        self.cycle_history: list[CycleSnapshot] = []
        self.current_cycle: int = 0
        self.semantic_graph = SemanticGraph()

    def initialize(self) -> list[SearchQuery]:
        """Generate initial multilingual queries."""
        self.pending_queries = self.query_gen.generate_initial_queries()
        return self.pending_queries

    def ingest_findings(self, new_findings: list[Finding]) -> list[str]:
        """Ingest findings. Returns list of new entity names."""
        all_new: list[str] = []
        for f in new_findings:
            f.cycle = self.current_cycle
            self.findings.append(f)
            new_entities = self.postulates.ingest_finding(f)
            all_new.extend(new_entities)
        return all_new

    def run_cycle(self, connector=None) -> CycleSnapshot:
        """Run one complete audit cycle."""
        self.current_cycle += 1

        inferrer = DynamicInferenceEngine(self.postulates)
        self.all_expectations = inferrer.derive(self.current_cycle)

        ExpectationSatisfier.satisfy(
            self.all_expectations, self.findings, self.postulates
        )

        auditor = AuditEngine(
            self.all_expectations, self.findings, self.postulates
        )
        self.all_anomalies = auditor.run()

        # v3 Phase 3: semantic graph — extract relations from this cycle's findings
        # Note: findings are ingested before run_cycle, so their cycle number
        # is current_cycle - 1 (set by ingest_findings before the increment).
        relations_count = 0
        if connector is not None:
            cycle_for_findings = self.current_cycle - 1
            new_findings = [
                f for f in self.findings if f.cycle == cycle_for_findings
            ]
            if new_findings:
                new_relations = connector.extract_relations(new_findings)
                for rel in new_relations:
                    rel.cycle = self.current_cycle
                self.semantic_graph.add_relations(new_relations)
                self.semantic_graph.mark_investigated(self.findings)
                graph_anomalies = self.semantic_graph.generate_anomalies()
                self.all_anomalies.extend(graph_anomalies)
            relations_count = len(self.semantic_graph.relations)

        self.pending_queries = self.query_gen.generate_gap_filling_queries(
            self.all_anomalies
        )

        # v3 Phase 1: confidence-driven queries
        confidence_queries = self.query_gen.generate_confidence_queries()
        self.pending_queries.extend(confidence_queries)

        # v3 Phase 7: apply temporal decay to all weighted postulates
        for wp in self.postulates.weighted_postulates.values():
            wp.confidence = wp.effective_confidence(self.current_cycle)

        coverage = calculate_coverage(
            self.all_expectations, self.all_anomalies
        )
        snap = self.postulates.snapshot()
        snapshot = CycleSnapshot(
            cycle=self.current_cycle,
            n_postulate_scholars=snap["scholars"],
            n_postulate_theories=snap["theories"],
            n_postulate_institutions=snap["institutions"],
            n_expectations=len(self.all_expectations),
            n_expectations_met=sum(
                1 for e in self.all_expectations if e.met
            ),
            n_findings=len(self.findings),
            n_anomalies=len(self.all_anomalies),
            coverage_score=round(coverage, 1),
            new_entities_discovered=[],
            queries_generated=len(self.pending_queries),
            weighted_postulates_count=snap["weighted_postulates"],
            avg_confidence=snap["avg_confidence"],
            negative_postulates_count=snap["negative_postulates"],
            relations_count=relations_count,
            schools_count=len(self.semantic_graph.detect_schools()),
            fractures_count=len(self.semantic_graph.detect_fractures()),
        )
        self.cycle_history.append(snapshot)
        return snapshot

    def report(self) -> str:
        """Generate a human-readable report."""
        lines: list[str] = []
        lines.append("=" * 60)
        lines.append(f"EPISTEMIX AUDIT REPORT \u2014 Cycle {self.current_cycle}")
        lines.append("=" * 60)

        lines.append("\n--- Dynamic Postulates ---")
        lines.append(self.postulates.describe())

        met = sum(1 for e in self.all_expectations if e.met)
        total = len(self.all_expectations)
        pct = (met / total * 100) if total > 0 else 0
        lines.append(f"\n--- Expectations: {met}/{total} ({pct:.0f}%) ---")
        for exp in self.all_expectations:
            mark = "\u2713" if exp.met else "\u2717"
            lines.append(
                f"  [{mark}] ({exp.severity_if_unmet.value.upper()}) "
                f"{exp.description}"
            )

        lines.append(f"\n--- Findings: {len(self.findings)} ---")
        langs = set(f.language for f in self.findings)
        authors = set(f.author for f in self.findings if f.author)
        lines.append(f"  Languages: {', '.join(sorted(langs))}")
        lines.append(f"  Authors: {len(authors)}")

        sorted_anomalies = sorted(
            self.all_anomalies,
            key=lambda a: a.severity.weight,
            reverse=True,
        )
        lines.append(f"\n--- Anomalies: {len(sorted_anomalies)} ---")
        for a in sorted_anomalies:
            lines.append(f"  [{a.severity.value.upper()}] {a.description}")
            if a.recommendation:
                lines.append(f"    -> {a.recommendation}")

        if self.cycle_history:
            latest = self.cycle_history[-1]
            score = latest.coverage_score
            if score >= 80:
                label = "Good"
            elif score >= 60:
                label = "Moderate"
            elif score >= 40:
                label = "Insufficient"
            else:
                label = "Poor"
            lines.append(f"\n--- Coverage: {score:.1f}% ({label}) ---")

        if len(self.cycle_history) > 1:
            lines.append("\n--- Evolution ---")
            lines.append(
                f"{'Cycle':>6} {'Expect':>8} {'Met':>6} "
                f"{'Anom':>6} {'Coverage':>10}"
            )
            for s in self.cycle_history:
                lines.append(
                    f"{s.cycle:>6} {s.n_expectations:>8} "
                    f"{s.n_expectations_met:>6} {s.n_anomalies:>6} "
                    f"{s.coverage_score:>9.1f}%"
                )

        lines.append("\n" + "=" * 60)
        lines.append(
            "NOTE: Coverage is always a LOWER BOUND on completeness."
        )
        lines.append("=" * 60)

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Serialize engine state for the web API / database."""
        coverage = (
            self.cycle_history[-1].coverage_score
            if self.cycle_history else 0.0
        )
        return {
            "topic": self.postulates.topic,
            "country": self.postulates.country,
            "discipline": self.postulates.discipline,
            "cycle": self.current_cycle,
            "coverage_percentage": coverage,
            "expectations_met": sum(
                1 for e in self.all_expectations if e.met
            ),
            "total_expectations": len(self.all_expectations),
            "total_findings": len(self.findings),
            "total_anomalies": len(self.all_anomalies),
            "coverage_history": [
                s.to_dict() for s in self.cycle_history
            ],
            "postulates": self.postulates.snapshot(),
            "findings": [f.to_dict() for f in self.findings],
            "expectations": [e.to_dict() for e in self.all_expectations],
            "anomalies": [a.to_dict() for a in self.all_anomalies],
            "pending_queries": [q.to_dict() for q in self.pending_queries],
            "weighted_postulates": [
                wp.to_dict()
                for wp in self.postulates.weighted_postulates.values()
            ],
            "negative_postulates": [
                np.to_dict()
                for np in self.postulates.negative_postulates
            ],
            "semantic_relations": [
                r.to_dict() for r in self.semantic_graph.relations
            ],
            "semantic_graph": self.semantic_graph.summary(),
        }
