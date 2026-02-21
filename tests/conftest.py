"""Shared test fixtures and mock data for Epistemix tests.

Based on the founder's Amphipolis simulation data with rich Finding
objects containing authors, institutions, theories, source types.
"""

from __future__ import annotations

import pytest

from epistemix.models import (
    Anomaly,
    Entity,
    EntityType,
    Expectation,
    Finding,
    GapType,
    RelationType,
    SearchQuery,
    SemanticRelation,
    Severity,
)


# ============================================================
# AMPHIPOLIS FINDINGS — 4 cycles of rich simulation data
# ============================================================

@pytest.fixture
def amphipolis_topic() -> str:
    return "Amphipolis tomb excavation"


@pytest.fixture
def amphipolis_country() -> str:
    return "Greece"


@pytest.fixture
def amphipolis_discipline() -> str:
    return "archaeology"


@pytest.fixture
def cycle_0_findings() -> list[Finding]:
    """Initial cycle: key researchers and basic facts."""
    return [
        Finding(
            source="Excavation report 2014",
            language="en",
            author="Katerina Peristeri",
            institution="Greek Ministry of Culture",
            theory_supported="Hephaestion memorial",
            source_type="institutional",
            year=2014,
            entities_mentioned=[
                "Michalis Lefantzis", "Amphipolis", "Hephaestion",
                "Alexander the Great",
            ],
        ),
        Finding(
            source="Monogram analysis paper",
            language="en",
            author="Andrew Chugg",
            institution="",
            theory_supported="Olympias burial",
            source_type="peer_reviewed",
            year=2015,
            entities_mentioned=[
                "Olympias", "Hephaestion", "Dinocrates",
                "Amphipolis",
            ],
        ),
        Finding(
            source="Skeletal analysis report",
            language="en",
            author="",
            institution="Aristotle University of Thessaloniki",
            theory_supported="",
            source_type="institutional",
            year=2015,
            entities_mentioned=[
                "Amphipolis", "Katerina Peristeri",
            ],
        ),
        Finding(
            source="Archaiologiko Deltion publication",
            language="el",
            author="Katerina Peristeri",
            institution="Greek Archaeological Service",
            theory_supported="Hephaestion memorial",
            source_type="peer_reviewed",
            year=2016,
            entities_mentioned=[
                "Michalis Lefantzis", "Amphipolis",
            ],
        ),
        Finding(
            source="DAI Athens newsletter",
            language="de",
            author="",
            institution="German Archaeological Institute",
            theory_supported="",
            source_type="institutional",
            year=2015,
            entities_mentioned=["Amphipolis", "Peristeri"],
        ),
    ]


@pytest.fixture
def cycle_1_findings() -> list[Finding]:
    """Second cycle: more theories and international coverage."""
    return [
        Finding(
            source="Solstice alignment study",
            language="en",
            author="Savvides",
            institution="",
            theory_supported="Astronomical alignment",
            source_type="peer_reviewed",
            year=2025,
            entities_mentioned=["Amphipolis", "winter solstice"],
        ),
        Finding(
            source="Italian monograph on Anfipoli",
            language="it",
            author="Mavrogiannis",
            institution="Universita di Napoli",
            theory_supported="Olympias burial",
            source_type="peer_reviewed",
            year=2010,
            entities_mentioned=[
                "Olympias", "Anfipoli", "Lazaridis",
                "Alexander the Great", "Efestione",
            ],
        ),
        Finding(
            source="French review of Macedonian tombs",
            language="fr",
            author="Bonias",
            institution="EfA",
            theory_supported="",
            source_type="peer_reviewed",
            year=2018,
            entities_mentioned=["Amphipolis", "Vergina", "Aigai"],
        ),
        Finding(
            source="BBC News coverage",
            language="en",
            author="",
            institution="BBC",
            theory_supported="",
            source_type="news",
            year=2014,
            entities_mentioned=[
                "Amphipolis", "Peristeri", "Alexander the Great",
            ],
        ),
    ]


@pytest.fixture
def cycle_2_findings() -> list[Finding]:
    """Third cycle: deeper investigation, more specialists."""
    return [
        Finding(
            source="DNA analysis preliminary report",
            language="en",
            author="Aris Poulianos",
            institution="Aristotle University of Thessaloniki",
            theory_supported="",
            source_type="peer_reviewed",
            year=2017,
            entities_mentioned=["Amphipolis", "ancient DNA"],
        ),
        Finding(
            source="Mosaic iconography study",
            language="en",
            author="Maria Tsimbidou-Avloniti",
            institution="Archaeological Museum of Thessaloniki",
            theory_supported="",
            source_type="peer_reviewed",
            year=2016,
            entities_mentioned=[
                "Amphipolis", "Persephone", "mosaic", "caryatid",
            ],
        ),
        Finding(
            source="Epigraphy analysis of inscriptions",
            language="en",
            author="Panagiotis Faklaris",
            institution="Aristotle University of Thessaloniki",
            theory_supported="Hephaestion memorial",
            source_type="peer_reviewed",
            year=2018,
            entities_mentioned=[
                "Amphipolis", "inscription", "monogram",
                "PARELABON", "Hephaestion",
            ],
        ),
    ]


@pytest.fixture
def cycle_3_findings() -> list[Finding]:
    """Fourth cycle: final investigation of remaining gaps."""
    return [
        Finding(
            source="Numismatic evidence from Amphipolis",
            language="en",
            author="Katerini Liampi",
            institution="University of Thessaly",
            theory_supported="",
            source_type="peer_reviewed",
            year=2019,
            entities_mentioned=["Amphipolis", "coins", "mint"],
        ),
        Finding(
            source="Architectural survey of Kasta tomb",
            language="en",
            author="Michalis Lefantzis",
            institution="Greek Ministry of Culture",
            theory_supported="Hephaestion memorial",
            source_type="institutional",
            year=2015,
            entities_mentioned=[
                "Amphipolis", "vault", "column", "chamber",
                "architecture",
            ],
        ),
    ]


@pytest.fixture
def all_findings(
    cycle_0_findings, cycle_1_findings,
    cycle_2_findings, cycle_3_findings,
) -> list[Finding]:
    """All findings from all 4 cycles."""
    return (
        cycle_0_findings + cycle_1_findings
        + cycle_2_findings + cycle_3_findings
    )


@pytest.fixture
def sample_findings() -> list[Finding]:
    """Minimal set for quick tests."""
    return [
        Finding(
            source="Paper A",
            language="en",
            author="Alice",
            institution="MIT",
            theory_supported="Theory X",
            source_type="peer_reviewed",
            year=2024,
            entities_mentioned=["Bob", "Carol"],
        ),
        Finding(
            source="Paper B",
            language="en",
            author="Bob",
            institution="Oxford",
            theory_supported="Theory Y",
            source_type="peer_reviewed",
            year=2023,
            entities_mentioned=["Alice", "Dave"],
        ),
        Finding(
            source="Paper C",
            language="fr",
            author="Carol",
            institution="Sorbonne",
            theory_supported="Theory X",
            source_type="institutional",
            year=2024,
            entities_mentioned=["Alice", "Bob"],
        ),
    ]


@pytest.fixture
def amphipolis_relations() -> list[SemanticRelation]:
    """Semantic relations for the Amphipolis scenario."""
    return [
        SemanticRelation(
            source="Katerina Peristeri", target="Michalis Lefantzis",
            relation=RelationType.COAUTHORS, confidence=0.95,
            evidence="Co-directed excavation at Amphipolis",
            language="en",
        ),
        SemanticRelation(
            source="Panagiotis Faklaris", target="Katerina Peristeri",
            relation=RelationType.SUPPORTS, confidence=0.7,
            evidence="Faklaris epigraphy supports Peristeri dating",
            language="en",
        ),
        SemanticRelation(
            source="Andrew Chugg", target="Katerina Peristeri",
            relation=RelationType.CITES, confidence=0.9,
            evidence="Chugg cites Peristeri excavation data",
            language="en",
        ),
        SemanticRelation(
            source="Mavrogiannis", target="Katerina Peristeri",
            relation=RelationType.CONTESTS, confidence=0.8,
            evidence="Mavrogiannis contests Peristeri interpretation",
            language="it",
        ),
        SemanticRelation(
            source="Katerina Peristeri", target="Hephaestion memorial",
            relation=RelationType.SUPPORTS, confidence=0.9,
            evidence="Peristeri argues tomb is Hephaestion memorial",
            language="en",
        ),
        SemanticRelation(
            source="Andrew Chugg", target="Olympias burial",
            relation=RelationType.SUPPORTS, confidence=0.85,
            evidence="Chugg proposes Olympias as occupant",
            language="en",
        ),
    ]


# ============================================================
# JFK ASSASSINATION FINDINGS — investigative scenario
# ============================================================

@pytest.fixture
def jfk_topic() -> str:
    return "JFK assassination"


@pytest.fixture
def jfk_country() -> str:
    return "United States"


@pytest.fixture
def jfk_discipline() -> str:
    return "history"


@pytest.fixture
def jfk_cycle_0_findings() -> list[Finding]:
    """Initial cycle: official accounts and key actors."""
    return [
        Finding(
            source="Warren Commission Report (1964)",
            language="en",
            author="Earl Warren",
            institution="Warren Commission",
            theory_supported="Lone gunman",
            source_type="institutional",
            year=1964,
            entities_mentioned=[
                "Lee Harvey Oswald", "Jack Ruby",
                "Texas School Book Depository", "Dealey Plaza",
            ],
        ),
        Finding(
            source="House Select Committee on Assassinations Report",
            language="en",
            author="G. Robert Blakey",
            institution="US House of Representatives",
            theory_supported="Conspiracy probable",
            source_type="institutional",
            year=1979,
            entities_mentioned=[
                "Lee Harvey Oswald", "Organized crime",
                "CIA", "Dallas Police Department",
            ],
        ),
        Finding(
            source="Crossfire: The Plot That Killed Kennedy",
            language="en",
            author="Jim Marrs",
            institution="",
            theory_supported="Conspiracy probable",
            source_type="journalistic",
            year=1989,
            entities_mentioned=[
                "Lee Harvey Oswald", "Jack Ruby", "CIA",
                "FBI", "Lyndon B. Johnson",
            ],
        ),
        Finding(
            source="Oswald: el asesino solitario",
            language="es",
            author="Carlos Fuentes Mendoza",
            institution="Universidad Nacional Autónoma de México",
            theory_supported="Lone gunman",
            source_type="peer_reviewed",
            year=2013,
            entities_mentioned=[
                "Lee Harvey Oswald", "Marina Oswald",
                "Dallas", "Mexico City",
            ],
        ),
    ]


@pytest.fixture
def jfk_cycle_1_findings() -> list[Finding]:
    """Second cycle: forensic and media sources."""
    return [
        Finding(
            source="JFK: An Unfinished Life",
            language="en",
            author="Robert Dallek",
            institution="Boston University",
            theory_supported="Lone gunman",
            source_type="peer_reviewed",
            year=2003,
            entities_mentioned=[
                "Lee Harvey Oswald", "Robert F. Kennedy",
                "Secret Service",
            ],
        ),
        Finding(
            source="Reclaiming History",
            language="en",
            author="Vincent Bugliosi",
            institution="",
            theory_supported="Lone gunman",
            source_type="journalistic",
            year=2007,
            entities_mentioned=[
                "Lee Harvey Oswald", "Jack Ruby",
                "Zapruder film", "Parkland Hospital",
            ],
        ),
        Finding(
            source="Ubiystvo Kennedi: novye fakty",
            language="ru",
            author="Nikolai Yakovlev",
            institution="Russian Academy of Sciences",
            theory_supported="Conspiracy probable",
            source_type="peer_reviewed",
            year=1985,
            entities_mentioned=[
                "Lee Harvey Oswald", "KGB",
                "Cold War", "Cuba",
            ],
        ),
    ]


@pytest.fixture
def jfk_all_findings(
    jfk_cycle_0_findings, jfk_cycle_1_findings,
) -> list[Finding]:
    """All JFK findings from both cycles."""
    return jfk_cycle_0_findings + jfk_cycle_1_findings
