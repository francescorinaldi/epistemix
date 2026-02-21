"""Tests for the JFK assassination scenario — investigative/history domain.

Validates that Epistemix generalises beyond archaeology (Amphipolis)
to a different domain, country, language mix, and entity types.
"""

from __future__ import annotations

import pytest

from epistemix.core import EpistemixEngine
from epistemix.knowledge import EntityRegistry
from epistemix.models import Finding


# ============================================================
# BASIC ENGINE BEHAVIOR ON JFK SCENARIO
# ============================================================

class TestJFKSimulation:
    """Run the JFK scenario through the engine and verify key behaviors."""

    def test_engine_accepts_us_history_config(
        self, jfk_topic, jfk_country, jfk_discipline,
    ) -> None:
        engine = EpistemixEngine(jfk_country, jfk_topic, jfk_discipline)
        engine.initialize()
        assert engine.pending_queries
        assert any(
            q.language == "en" for q in engine.pending_queries
        )

    def test_ingest_discovers_key_entities(
        self, jfk_topic, jfk_country, jfk_discipline,
        jfk_cycle_0_findings,
    ) -> None:
        engine = EpistemixEngine(jfk_country, jfk_topic, jfk_discipline)
        engine.initialize()
        new_entities = engine.ingest_findings(jfk_cycle_0_findings)
        names_lower = [n.lower() for n in new_entities]
        assert any("oswald" in n for n in names_lower)
        assert any("warren" in n for n in names_lower)

    def test_theories_tracked(
        self, jfk_topic, jfk_country, jfk_discipline,
        jfk_cycle_0_findings,
    ) -> None:
        engine = EpistemixEngine(jfk_country, jfk_topic, jfk_discipline)
        engine.initialize()
        engine.ingest_findings(jfk_cycle_0_findings)
        engine.run_cycle()
        theories = engine.postulates.theories
        assert "Lone gunman" in theories
        assert "Conspiracy probable" in theories

    def test_multilingual_coverage_en_es(
        self, jfk_topic, jfk_country, jfk_discipline,
        jfk_cycle_0_findings,
    ) -> None:
        engine = EpistemixEngine(jfk_country, jfk_topic, jfk_discipline)
        engine.initialize()
        engine.ingest_findings(jfk_cycle_0_findings)
        engine.run_cycle()
        langs = engine.postulates.languages_covered
        assert "en" in langs
        assert "es" in langs

    def test_two_cycle_coverage_progression(
        self, jfk_topic, jfk_country, jfk_discipline,
        jfk_cycle_0_findings, jfk_cycle_1_findings,
    ) -> None:
        engine = EpistemixEngine(jfk_country, jfk_topic, jfk_discipline)
        engine.initialize()

        engine.ingest_findings(jfk_cycle_0_findings)
        snap1 = engine.run_cycle()

        engine.ingest_findings(jfk_cycle_1_findings)
        snap2 = engine.run_cycle()

        assert snap2.cycle == 2
        assert snap2.n_findings > snap1.n_findings
        assert snap2.n_expectations_met >= snap1.n_expectations_met

    def test_russian_source_adds_language(
        self, jfk_topic, jfk_country, jfk_discipline,
        jfk_cycle_0_findings, jfk_cycle_1_findings,
    ) -> None:
        engine = EpistemixEngine(jfk_country, jfk_topic, jfk_discipline)
        engine.initialize()
        engine.ingest_findings(jfk_cycle_0_findings)
        engine.run_cycle()
        engine.ingest_findings(jfk_cycle_1_findings)
        engine.run_cycle()
        assert "ru" in engine.postulates.languages_covered

    def test_institutions_tracked(
        self, jfk_topic, jfk_country, jfk_discipline,
        jfk_all_findings,
    ) -> None:
        engine = EpistemixEngine(jfk_country, jfk_topic, jfk_discipline)
        engine.initialize()
        engine.ingest_findings(jfk_all_findings)
        engine.run_cycle()
        institutions = engine.postulates.institutions
        assert any("warren" in i.lower() for i in institutions)

    def test_serialization(
        self, jfk_topic, jfk_country, jfk_discipline,
        jfk_cycle_0_findings, jfk_cycle_1_findings,
    ) -> None:
        engine = EpistemixEngine(jfk_country, jfk_topic, jfk_discipline)
        engine.initialize()
        engine.ingest_findings(jfk_cycle_0_findings)
        engine.run_cycle()
        engine.ingest_findings(jfk_cycle_1_findings)
        engine.run_cycle()
        d = engine.to_dict()
        assert d["cycle"] == 2
        assert len(d["coverage_history"]) == 2
        assert d["findings"]


# ============================================================
# ENTITY REGISTRY GENERALISATION
# ============================================================

class TestJFKEntityRegistry:
    """Verify that EntityRegistry works for non-Amphipolis entities."""

    def test_cia_classified_as_institution_via_keyword(self) -> None:
        registry = EntityRegistry()
        # "Central Intelligence Agency" contains "agency" keyword
        assert registry.classify("Central Intelligence Agency") == "institution"

    def test_fbi_classified_as_institution_via_keyword(self) -> None:
        registry = EntityRegistry()
        assert registry.classify("Federal Bureau of Investigation") == "institution"

    def test_dynamic_registration_for_jfk_entities(self) -> None:
        registry = EntityRegistry()
        # Before: Oswald defaults to scholar
        assert registry.classify("Lee Harvey Oswald") == "scholar"
        # Register as historical figure
        registry.register("Lee Harvey Oswald", "historical_figure")
        assert registry.classify("Lee Harvey Oswald") == "historical_figure"

    def test_registry_shared_with_engine(
        self, jfk_topic, jfk_country, jfk_discipline,
        jfk_cycle_0_findings,
    ) -> None:
        """Engine and postulates share the same registry instance."""
        registry = EntityRegistry()
        registry.register("Lee Harvey Oswald", "historical_figure")

        engine = EpistemixEngine(
            jfk_country, jfk_topic, jfk_discipline,
            entity_registry=registry,
        )
        engine.initialize()
        engine.ingest_findings(jfk_cycle_0_findings)

        # Oswald should be classified as historical_figure, not scholar
        oswald_key = "lee harvey oswald"
        assert oswald_key in engine.postulates.entities
        entity = engine.postulates.entities[oswald_key]
        from epistemix.models import EntityType
        assert entity.entity_type == EntityType.HISTORICAL_FIGURE
