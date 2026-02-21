"""Tests for EntityRegistry and entity classification in knowledge.py."""

from __future__ import annotations

import pytest

from epistemix.knowledge import (
    EntityRegistry,
    KNOWN_HISTORICAL_FIGURES,
    KNOWN_ANCIENT_SOURCES,
    KNOWN_DEITIES_CONCEPTS,
    KNOWN_PLACES,
    classify_entity_name,
)


# ============================================================
# ENTITY REGISTRY — SEED CLASSIFICATION
# ============================================================

class TestEntityRegistrySeedClassification:
    """Test classification against the hardcoded seed sets."""

    def setup_method(self) -> None:
        self.registry = EntityRegistry()

    def test_classify_historical_figure(self) -> None:
        assert self.registry.classify("Alexander the Great") == "historical_figure"
        assert self.registry.classify("hephaestion") == "historical_figure"
        assert self.registry.classify("OLYMPIAS") == "historical_figure"

    def test_classify_ancient_source(self) -> None:
        assert self.registry.classify("Plutarch") == "ancient_source"
        assert self.registry.classify("diodorus siculus") == "ancient_source"

    def test_classify_deity_as_unknown(self) -> None:
        assert self.registry.classify("Zeus") == "unknown"
        assert self.registry.classify("persephone") == "unknown"

    def test_classify_place_as_site(self) -> None:
        assert self.registry.classify("Amphipolis") == "site"
        assert self.registry.classify("vergina") == "site"

    def test_classify_unknown_defaults_to_scholar(self) -> None:
        assert self.registry.classify("Jane Doe") == "scholar"
        assert self.registry.classify("Katerina Peristeri") == "scholar"

    def test_classify_empty_string(self) -> None:
        assert self.registry.classify("") == "unknown"
        assert self.registry.classify("   ") == "unknown"


# ============================================================
# ENTITY REGISTRY — TRANSLITERATION / NORMALIZATION
# ============================================================

class TestEntityRegistryNormalization:
    """Test the normalize() method and transliteration-based classification."""

    def setup_method(self) -> None:
        self.registry = EntityRegistry()

    def test_normalize_known_variant(self) -> None:
        assert self.registry.normalize("efestione") == "hephaestion"
        assert self.registry.normalize("alessandro magno") == "alexander the great"

    def test_normalize_unknown_returns_original(self) -> None:
        assert self.registry.normalize("Jane Doe") == "Jane Doe"

    def test_classify_via_transliteration(self) -> None:
        # "efestione" (Italian) should resolve to "hephaestion" -> historical_figure
        assert self.registry.classify("efestione") == "historical_figure"
        assert self.registry.classify("alessandro magno") == "historical_figure"

    def test_transliteration_resolves_ancient_source(self) -> None:
        # "deinokratis" maps to "dinocrates" which is in historical_figures
        assert self.registry.classify("deinokratis") == "historical_figure"


# ============================================================
# ENTITY REGISTRY — INSTITUTION KEYWORD HEURISTIC
# ============================================================

class TestEntityRegistryInstitutionKeywords:
    """Test the extended keyword heuristic for institutions."""

    def setup_method(self) -> None:
        self.registry = EntityRegistry()

    def test_original_keywords(self) -> None:
        assert self.registry.classify("Aristotle University of Thessaloniki") == "institution"
        assert self.registry.classify("National Archaeological Museum") == "institution"
        assert self.registry.classify("Greek Ministry of Culture") == "institution"

    def test_extended_keywords_corporation(self) -> None:
        assert self.registry.classify("TSMC Corporation") == "institution"
        assert self.registry.classify("Samsung Electronics Ltd") == "institution"

    def test_extended_keywords_government(self) -> None:
        assert self.registry.classify("European Commission") == "institution"
        assert self.registry.classify("Federal Bureau of Investigation") == "institution"
        assert self.registry.classify("National Science Foundation") == "institution"

    def test_extended_keywords_board_agency(self) -> None:
        assert self.registry.classify("National Board of Review") == "institution"
        assert self.registry.classify("Central Intelligence Agency") == "institution"


# ============================================================
# ENTITY REGISTRY — DYNAMIC REGISTRATION
# ============================================================

class TestEntityRegistryDynamic:
    """Test dynamic registration of new entities."""

    def setup_method(self) -> None:
        self.registry = EntityRegistry()

    def test_register_then_classify(self) -> None:
        # Before: defaults to scholar
        assert self.registry.classify("TSMC") == "scholar"
        # Register
        self.registry.register("TSMC", "institution")
        # After: classified correctly
        assert self.registry.classify("TSMC") == "institution"

    def test_register_many(self) -> None:
        self.registry.register_many({
            "Biden": "historical_figure",
            "ASML": "institution",
            "Chip War": "publication",
        })
        assert self.registry.classify("Biden") == "historical_figure"
        assert self.registry.classify("ASML") == "institution"
        assert self.registry.classify("Chip War") == "publication"

    def test_dynamic_overrides_default_scholar(self) -> None:
        """Dynamic registration should override the scholar default."""
        name = "Lee Hsien Loong"
        assert self.registry.classify(name) == "scholar"  # default
        self.registry.register(name, "historical_figure")
        assert self.registry.classify(name) == "historical_figure"

    def test_dynamic_takes_priority_over_seed(self) -> None:
        """Dynamic registrations take precedence over seed sets."""
        # "amphipolis" is in KNOWN_PLACES -> "site"
        assert self.registry.classify("amphipolis") == "site"
        # Override with dynamic
        self.registry.register("amphipolis", "evidence")
        assert self.registry.classify("amphipolis") == "evidence"

    def test_is_non_scholar(self) -> None:
        assert not self.registry.is_non_scholar("Jane Doe")  # defaults to scholar
        assert self.registry.is_non_scholar("Amphipolis")     # site
        assert self.registry.is_non_scholar("Plutarch")       # ancient_source


# ============================================================
# ENTITY REGISTRY — STATS
# ============================================================

class TestEntityRegistryStats:
    """Test the stats() method."""

    def test_stats_on_fresh_registry(self) -> None:
        registry = EntityRegistry()
        stats = registry.stats()
        assert stats["seed_historical_figures"] == len(KNOWN_HISTORICAL_FIGURES)
        assert stats["seed_ancient_sources"] == len(KNOWN_ANCIENT_SOURCES)
        assert stats["seed_deities"] == len(KNOWN_DEITIES_CONCEPTS)
        assert stats["seed_places"] == len(KNOWN_PLACES)
        assert stats["dynamic_registrations"] == 0
        assert stats["dynamic_by_type"] == {}

    def test_stats_after_registrations(self) -> None:
        registry = EntityRegistry()
        registry.register_many({
            "TSMC": "institution",
            "Samsung": "institution",
            "Biden": "historical_figure",
        })
        stats = registry.stats()
        assert stats["dynamic_registrations"] == 3
        assert stats["dynamic_by_type"]["institution"] == 2
        assert stats["dynamic_by_type"]["historical_figure"] == 1


# ============================================================
# BACKWARD COMPATIBILITY — classify_entity_name() wrapper
# ============================================================

class TestClassifyEntityNameWrapper:
    """Ensure the module-level classify_entity_name() still works."""

    def test_wrapper_classifies_known_entity(self) -> None:
        assert classify_entity_name("Plutarch") == "ancient_source"

    def test_wrapper_classifies_unknown_as_scholar(self) -> None:
        assert classify_entity_name("Jane Doe") == "scholar"

    def test_wrapper_classifies_institution(self) -> None:
        assert classify_entity_name("National Museum") == "institution"


# ============================================================
# BACKWARD COMPATIBILITY — KNOWN_* module-level sets
# ============================================================

class TestKnownSetsRetrocompat:
    """Ensure the KNOWN_* sets are still importable and contain expected data."""

    def test_known_historical_figures_has_alexander(self) -> None:
        assert "alexander the great" in KNOWN_HISTORICAL_FIGURES

    def test_known_ancient_sources_has_plutarch(self) -> None:
        assert "plutarch" in KNOWN_ANCIENT_SOURCES

    def test_known_deities_has_zeus(self) -> None:
        assert "zeus" in KNOWN_DEITIES_CONCEPTS

    def test_known_places_has_amphipolis(self) -> None:
        assert "amphipolis" in KNOWN_PLACES
