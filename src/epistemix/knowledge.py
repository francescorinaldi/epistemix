"""Domain knowledge — geographic-linguistic data, transliterations, known entities.

This module contains the structured knowledge that drives multilingual
query generation and entity classification. Extracted from the founder's
v2 design into a standalone module for maintainability.

To add a new country: add an entry to GEOGRAPHIC_LINGUISTIC.
To add a new proper name translation: add to TRANSLITERATIONS.
To improve entity classification: update the KNOWN_* sets.
"""

from __future__ import annotations

from epistemix.models import AccessTier, LanguageEcosystem


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
    "China": {
        "primary_languages": ["zh", "en"],
        "foreign_traditions": {},
        "transliteration_map": {},
    },
    "Japan": {
        "primary_languages": ["ja", "en"],
        "foreign_traditions": {},
        "transliteration_map": {},
    },
    "South Korea": {
        "primary_languages": ["ko", "en"],
        "foreign_traditions": {},
        "transliteration_map": {},
    },
    "Saudi Arabia": {
        "primary_languages": ["ar", "en"],
        "foreign_traditions": {},
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
# LANGUAGE ECOSYSTEM REGISTRY (access-barrier reasoning)
# ============================================================

LANGUAGE_ECOSYSTEMS: dict[str, LanguageEcosystem] = {
    "zh": LanguageEcosystem(
        language="zh",
        access_tier=AccessTier.WALLED_GARDEN,
        gated_databases=("CNKI", "Wanfang", "VIP", "CQVIP"),
        estimated_gated_share=0.70,
        query_style="phrasal",
        script="cjk",
    ),
    "ar": LanguageEcosystem(
        language="ar",
        access_tier=AccessTier.PARTIAL_ACCESS,
        gated_databases=("Al-Manhal", "E-Marefa", "Dar Al Mandumah"),
        estimated_gated_share=0.35,
        query_style="morphological",
        script="arabic",
    ),
    "ja": LanguageEcosystem(
        language="ja",
        access_tier=AccessTier.PARTIAL_ACCESS,
        gated_databases=("CiNii", "J-STAGE", "NDL Digital"),
        estimated_gated_share=0.40,
        query_style="phrasal",
        script="cjk",
    ),
    "ko": LanguageEcosystem(
        language="ko",
        access_tier=AccessTier.PARTIAL_ACCESS,
        gated_databases=("RISS", "KCI", "DBpia"),
        estimated_gated_share=0.35,
        query_style="phrasal",
        script="hangul",
    ),
}


# ============================================================
# CROSS-LANGUAGE STRATEGIES (indirect access to gated ecosystems)
# ============================================================

CROSS_LANGUAGE_STRATEGIES: dict[str, list[tuple[str, str]]] = {
    "zh": [
        ("en", "Chinese research on {topic}"),
        ("ja", "{topic} 中国の研究"),
    ],
    "ar": [
        ("en", "Arabic-language research on {topic}"),
        ("fr", "recherche arabophone sur {topic}"),
    ],
    "ja": [
        ("en", "Japanese research on {topic}"),
    ],
    "ko": [
        ("en", "Korean research on {topic}"),
    ],
}


# ============================================================
# QUERY GENERATION HELPERS
# ============================================================

STOPWORDS: set[str] = {
    "the", "and", "for", "from", "with", "near", "about",
    "this", "that", "tomb", "della", "del", "von", "des",
}


def classify_entity_name(name: str) -> str:
    """Classify an entity name using knowledge heuristics.

    Returns an EntityType value string.
    """
    lower = name.lower().strip()

    # Check known sets
    if lower in KNOWN_HISTORICAL_FIGURES:
        return "historical_figure"
    if lower in KNOWN_ANCIENT_SOURCES:
        return "ancient_source"
    if lower in KNOWN_DEITIES_CONCEPTS:
        return "unknown"  # deities are not researchable entities
    if lower in KNOWN_PLACES:
        return "site"

    # Check transliterations
    if lower in KNOWN_TRANSLITERATIONS:
        canonical = KNOWN_TRANSLITERATIONS[lower]
        if canonical.lower() in KNOWN_HISTORICAL_FIGURES:
            return "historical_figure"

    # Heuristic: institution keywords
    institution_keywords = {
        "university", "museum", "institute", "ministry",
        "school", "department", "laboratory", "centre", "center",
        "archaeological service", "ephorate",
    }
    for kw in institution_keywords:
        if kw in lower:
            return "institution"

    # Default: assume scholar (most commonly mentioned entities are people)
    return "scholar"
