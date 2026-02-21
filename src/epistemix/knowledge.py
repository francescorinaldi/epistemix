"""Domain knowledge — geographic-linguistic data, transliterations, known entities.

This module contains the structured knowledge that drives multilingual
query generation and entity classification. Extracted from the founder's
v2 design into a standalone module for maintainability.

To add a new country: add an entry to GEOGRAPHIC_LINGUISTIC.
To add a new proper name translation: add to TRANSLITERATIONS.
To improve entity classification: update the KNOWN_* sets.
"""

from __future__ import annotations

from typing import Any


# ============================================================
# GEOGRAPHIC-LINGUISTIC AXIOMS
# ============================================================

GEOGRAPHIC_LINGUISTIC: dict[str, dict] = {
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
                "tomb": "\u03c4\u03ac\u03c6\u03bf\u03c2",
                "tumulus": "\u03c4\u03cd\u03bc\u03b2\u03bf\u03c2",
                "burial": "\u03c4\u03b1\u03c6\u03ae",
                "excavation": "\u03b1\u03bd\u03b1\u03c3\u03ba\u03b1\u03c6\u03ae",
                "archaeology": "\u03b1\u03c1\u03c7\u03b1\u03b9\u03bf\u03bb\u03bf\u03b3\u03af\u03b1",
            }
        },
    },
    "Egypt": {
        "primary_languages": ["ar", "en"],
        "foreign_traditions": {
            "fr": "IFAO Cairo",
            "de": "DAI Cairo",
            "it": "Centro Archeologico Italiano",
        },
        "transliteration_map": {},
    },
    "Italy": {
        "primary_languages": ["it"],
        "foreign_traditions": {
            "en": "British School at Rome",
            "de": "DAI Rome",
            "fr": "\u00c9cole fran\u00e7aise de Rome",
        },
        "transliteration_map": {},
    },
    "Turkey": {
        "primary_languages": ["tr", "en"],
        "foreign_traditions": {
            "de": "DAI Istanbul",
            "en": "British Institute at Ankara",
            "fr": "IFEA",
        },
        "transliteration_map": {},
    },
    "Israel": {
        "primary_languages": ["he", "en"],
        "foreign_traditions": {
            "fr": "\u00c9cole biblique et arch\u00e9ologique fran\u00e7aise",
            "de": "DAI Jerusalem",
        },
        "transliteration_map": {},
    },
    "Spain": {
        "primary_languages": ["es"],
        "foreign_traditions": {
            "en": "British School at Rome",
            "de": "DAI Madrid",
            "fr": "Casa de Vel\u00e1zquez",
        },
        "transliteration_map": {},
    },
    "France": {
        "primary_languages": ["fr"],
        "foreign_traditions": {
            "en": "British institutions",
            "de": "German institutions",
        },
        "transliteration_map": {},
    },
    "Germany": {
        "primary_languages": ["de"],
        "foreign_traditions": {
            "en": "British institutions",
            "fr": "French institutions",
        },
        "transliteration_map": {},
    },
}


# ============================================================
# PROPER NAME TRANSLITERATIONS
# ============================================================

TRANSLITERATIONS: dict[str, dict[str, str]] = {
    "Amphipolis": {
        "el": "\u0391\u03bc\u03c6\u03af\u03c0\u03bf\u03bb\u03b7",
        "it": "Anfipoli",
        "de": "Amphipolis",
        "fr": "Amphipolis",
    },
    "Hephaestion": {
        "el": "\u0397\u03c6\u03b1\u03b9\u03c3\u03c4\u03af\u03c9\u03bd",
        "it": "Efestione",
        "de": "Hephaistion",
        "fr": "H\u00e9phestion",
    },
    "Olympias": {
        "el": "\u039f\u03bb\u03c5\u03bc\u03c0\u03b9\u03ac\u03b4\u03b1",
        "it": "Olimpiade",
        "de": "Olympias",
        "fr": "Olympias",
    },
    "Alexander the Great": {
        "el": "\u039c\u03ad\u03b3\u03b1\u03c2 \u0391\u03bb\u03ad\u03be\u03b1\u03bd\u03b4\u03c1\u03bf\u03c2",
        "it": "Alessandro Magno",
        "de": "Alexander der Gro\u00dfe",
        "fr": "Alexandre le Grand",
    },
    "Kasta": {
        "el": "\u039a\u03b1\u03c3\u03c4\u03ac",
        "it": "Kasta",
        "de": "Kasta",
        "fr": "Kasta",
    },
}

# Canonical name resolution: variant → canonical English name
KNOWN_TRANSLITERATIONS: dict[str, str] = {
    "alessandro magno": "alexander the great",
    "efestione": "hephaestion",
    "hephaistion": "hephaestion",
    "\u03b7\u03c6\u03b1\u03b9\u03c3\u03c4\u03af\u03c9\u03bd": "hephaestion",
    "\u03bc\u03ad\u03b3\u03b1\u03c2 \u03b1\u03bb\u03ad\u03be\u03b1\u03bd\u03b4\u03c1\u03bf\u03c2": "alexander the great",
    "olimpiade": "olympias",
    "\u03bf\u03bb\u03c5\u03bc\u03c0\u03b9\u03ac\u03b4\u03b1": "olympias",
    "deinokratis": "dinocrates",
    "antipatros": "antipater",
    "\u03c0\u03b1\u03c1\u03b5\u03bb\u03b1\u03b2\u03bf\u03bd": "PARELABON",
    "\u03a0\u0391\u03a1\u0395\u039b\u0391\u0392\u039f\u039d": "PARELABON",
}


# ============================================================
# KNOWN ENTITY SETS (for entity classification heuristics)
# ============================================================

KNOWN_HISTORICAL_FIGURES: set[str] = {
    "alexander", "alexander the great", "alexander iv",
    "hephaestion", "olympias", "cassander",
    "philip", "philip ii", "roxane", "nearchus",
    "antipatros", "antipater",
    "perdiccas", "ptolemy", "dinocrates", "deinokratis",
    "laomedon", "eurydice", "arrhidaeus",
    "amyntor",
}

KNOWN_ANCIENT_SOURCES: set[str] = {
    "diodorus", "diodorus siculus", "plutarch", "arrian",
    "arrianus", "justin", "strabo", "pausanias",
}

KNOWN_DEITIES_CONCEPTS: set[str] = {
    "cybele", "persephone", "hades", "pluto", "hermes",
    "dionysus", "artemis", "demeter", "zeus",
}

KNOWN_PLACES: set[str] = {
    "amphipolis", "vergina", "pella", "thessaloniki",
    "aigai", "athens", "dion", "babylon", "susa",
    "alexandria", "sidon", "anfipoli",
}


# ============================================================
# QUERY GENERATION HELPERS
# ============================================================

STOPWORDS: set[str] = {
    "the", "and", "for", "from", "with", "near", "about",
    "this", "that", "tomb", "della", "del", "von", "des",
}


# ============================================================
# ENTITY REGISTRY
# ============================================================

# Institution keyword heuristics
_INSTITUTION_KEYWORDS: set[str] = {
    "university", "museum", "institute", "ministry",
    "school", "department", "laboratory", "centre", "center",
    "archaeological service", "ephorate",
    # Extended keywords (from co-founder validation)
    "corporation", "inc", "ltd", "gmbh", "spa",
    "council", "foundation", "authority", "bureau", "office", "board",
    "agency", "commission", "committee",
}


class EntityRegistry:
    """Dynamic entity classification registry.

    Wraps the seed KNOWN_* sets with a dynamic layer that grows
    during live research. Entities discovered at runtime are registered
    and immediately available for future classification.

    Usage:
        registry = EntityRegistry()
        registry.classify("Plutarch")          # -> "ancient_source" (seed)
        registry.classify("TSMC")              # -> "scholar" (unknown default)
        registry.register("TSMC", "institution")
        registry.classify("TSMC")              # -> "institution" (dynamic)
    """

    def __init__(self) -> None:
        # Seed data (references to module-level sets — shared, not copied)
        self._historical_figures = KNOWN_HISTORICAL_FIGURES
        self._ancient_sources = KNOWN_ANCIENT_SOURCES
        self._deities = KNOWN_DEITIES_CONCEPTS
        self._places = KNOWN_PLACES
        self._transliterations = KNOWN_TRANSLITERATIONS

        # Dynamic registrations: lowered name -> entity type string
        self._dynamic: dict[str, str] = {}

    def classify(self, name: str) -> str:
        """Classify an entity name. Checks dynamic, then seed, then heuristic.

        Returns an EntityType value string.
        """
        lower = name.lower().strip()
        if not lower:
            return "unknown"

        # 1. Dynamic registrations take priority
        if lower in self._dynamic:
            return self._dynamic[lower]

        # 2. Seed sets (priority order)
        if lower in self._historical_figures:
            return "historical_figure"
        if lower in self._ancient_sources:
            return "ancient_source"
        if lower in self._deities:
            return "unknown"
        if lower in self._places:
            return "site"

        # 3. Transliteration resolution
        if lower in self._transliterations:
            canonical = self._transliterations[lower].lower()
            if canonical in self._historical_figures:
                return "historical_figure"
            if canonical in self._ancient_sources:
                return "ancient_source"
            if canonical in self._places:
                return "site"
            # Check dynamic for canonical form too
            if canonical in self._dynamic:
                return self._dynamic[canonical]

        # 4. Institution keyword heuristic
        for kw in _INSTITUTION_KEYWORDS:
            if kw in lower:
                return "institution"

        # 5. Default
        return "scholar"

    def normalize(self, name: str) -> str:
        """Resolve variant spellings to canonical English form."""
        lower = name.lower().strip()
        return self._transliterations.get(lower, name)

    def register(self, name: str, entity_type: str) -> None:
        """Register a single entity with its type."""
        lower = name.lower().strip()
        if lower:
            self._dynamic[lower] = entity_type

    def register_many(self, entities: dict[str, str]) -> None:
        """Bulk register entities. Dict maps name -> type string.

        Accepted type strings: 'scholar', 'institution', 'historical_figure',
        'ancient_source', 'site', 'unknown', 'theory', 'publication',
        'evidence', 'method', 'event'.
        """
        for name, etype in entities.items():
            self.register(name, etype)

    def is_non_scholar(self, name: str) -> bool:
        """True if the entity is classified as anything other than scholar."""
        return self.classify(name) != "scholar"

    def stats(self) -> dict[str, Any]:
        """Return classification statistics."""
        counts: dict[str, int] = {}
        for etype in self._dynamic.values():
            counts[etype] = counts.get(etype, 0) + 1
        return {
            "seed_historical_figures": len(self._historical_figures),
            "seed_ancient_sources": len(self._ancient_sources),
            "seed_deities": len(self._deities),
            "seed_places": len(self._places),
            "seed_transliterations": len(self._transliterations),
            "dynamic_registrations": len(self._dynamic),
            "dynamic_by_type": counts,
        }


# Default instance — used by classify_entity_name() wrapper
_DEFAULT_REGISTRY = EntityRegistry()


def classify_entity_name(name: str) -> str:
    """Classify an entity name using knowledge heuristics.

    Returns an EntityType value string.
    Delegates to the default EntityRegistry instance.
    """
    return _DEFAULT_REGISTRY.classify(name)
