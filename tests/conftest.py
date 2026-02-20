"""Shared test fixtures and mock data for Epistemix tests."""

from __future__ import annotations

import pytest

from epistemix.models import (
    Anomaly,
    AnomalyType,
    CoverageScore,
    Finding,
    FindingType,
    Postulate,
    PostulateStatus,
    Query,
    QueryLanguage,
    ResearchState,
    Severity,
)


# ---------------------------------------------------------------------------
# Amphipolis domain fixtures
# ---------------------------------------------------------------------------

AMPHIPOLIS_TOPIC = "Amphipolis tomb excavation"
AMPHIPOLIS_COUNTRY = "Greece"
AMPHIPOLIS_DISCIPLINE = "archaeology"


@pytest.fixture
def amphipolis_state() -> ResearchState:
    return ResearchState(
        topic=AMPHIPOLIS_TOPIC,
        country=AMPHIPOLIS_COUNTRY,
        discipline=AMPHIPOLIS_DISCIPLINE,
    )


@pytest.fixture
def sample_findings() -> list[Finding]:
    return [
        Finding(
            name="Katerina Peristeri",
            finding_type=FindingType.SCHOLAR,
            source_query="Amphipolis tomb lead archaeologist",
            description="Lead excavator of Amphipolis tomb, Hellenic Ministry of Culture",
            language=QueryLanguage.ENGLISH,
        ),
        Finding(
            name="Michalis Lefantzis",
            finding_type=FindingType.SCHOLAR,
            source_query="Amphipolis tomb architect",
            description="Architect who studied the tomb structure",
            language=QueryLanguage.ENGLISH,
        ),
        Finding(
            name="Oscar Broneer",
            finding_type=FindingType.SCHOLAR,
            source_query="Amphipolis ancient excavations",
            description="Early excavator at Amphipolis in the 1960s",
            language=QueryLanguage.ENGLISH,
        ),
        Finding(
            name="Lazaridis",
            finding_type=FindingType.SCHOLAR,
            source_query="Amphipolis excavation history",
            description="Dimitrios Lazaridis, pioneer archaeologist at Amphipolis",
            language=QueryLanguage.ENGLISH,
        ),
        Finding(
            name="Alexander the Great burial theory",
            finding_type=FindingType.THEORY,
            source_query="Amphipolis tomb theories",
            description="Theory that the tomb was built for Alexander the Great",
            language=QueryLanguage.ENGLISH,
        ),
        Finding(
            name="Hephaestion memorial theory",
            finding_type=FindingType.THEORY,
            source_query="Amphipolis tomb occupant theories",
            description="Theory that the tomb was a memorial for Hephaestion",
            language=QueryLanguage.ENGLISH,
        ),
        Finding(
            name="Royal family member theory",
            finding_type=FindingType.THEORY,
            source_query="Amphipolis tomb occupant theories",
            description="Theory that the tomb housed a member of Alexander's family",
            language=QueryLanguage.ENGLISH,
        ),
        Finding(
            name="Hellenic Ministry of Culture",
            finding_type=FindingType.INSTITUTION,
            source_query="Amphipolis tomb excavation authority",
            description="Government body overseeing the excavation",
            language=QueryLanguage.ENGLISH,
        ),
        Finding(
            name="Aristotle University of Thessaloniki",
            finding_type=FindingType.INSTITUTION,
            source_query="Amphipolis tomb university research",
            description="University involved in Amphipolis research",
            language=QueryLanguage.ENGLISH,
        ),
        Finding(
            name="Caryatid sculptures",
            finding_type=FindingType.EVIDENCE,
            source_query="Amphipolis tomb artifacts",
            description="Two caryatid sculptures found at the entrance",
            language=QueryLanguage.ENGLISH,
        ),
        Finding(
            name="Floor mosaic",
            finding_type=FindingType.EVIDENCE,
            source_query="Amphipolis tomb mosaic",
            description="Mosaic depicting the abduction of Persephone",
            language=QueryLanguage.ENGLISH,
        ),
        Finding(
            name="Human remains",
            finding_type=FindingType.EVIDENCE,
            source_query="Amphipolis tomb skeletal remains",
            description="Skeletal remains of at least five individuals",
            language=QueryLanguage.ENGLISH,
        ),
    ]


@pytest.fixture
def sample_postulates() -> list[Postulate]:
    return [
        Postulate(
            id="P-MA01-01",
            description=f"Research on {AMPHIPOLIS_TOPIC} in {AMPHIPOLIS_COUNTRY} "
            "exists in the local language(s)",
            meta_axiom_id="MA-01",
        ),
        Postulate(
            id="P-MA01-02",
            description=f"At least one non-English publication on {AMPHIPOLIS_TOPIC} "
            f"in {AMPHIPOLIS_COUNTRY} exists",
            meta_axiom_id="MA-01",
        ),
        Postulate(
            id="P-MA02-01",
            description=f"At least one university has studied {AMPHIPOLIS_TOPIC} "
            f"in {AMPHIPOLIS_COUNTRY}",
            meta_axiom_id="MA-02",
        ),
        Postulate(
            id="P-MA03-01",
            description=f"At least two competing interpretations of {AMPHIPOLIS_TOPIC} "
            f"in {AMPHIPOLIS_COUNTRY} exist",
            meta_axiom_id="MA-03",
        ),
        Postulate(
            id="P-MA05-01",
            description=f"Multiple academic disciplines have contributed to "
            f"understanding {AMPHIPOLIS_TOPIC} in {AMPHIPOLIS_COUNTRY}",
            meta_axiom_id="MA-05",
        ),
    ]


@pytest.fixture
def sample_queries() -> list[Query]:
    return [
        Query(
            text="Amphipolis tomb excavation lead archaeologist",
            language=QueryLanguage.ENGLISH,
            priority=1.0,
        ),
        Query(
            text="Ανασκαφή τάφου Αμφίπολης αρχαιολόγοι",
            language=QueryLanguage.GREEK,
            priority=0.9,
        ),
        Query(
            text="fouilles tombeau Amphipolis archéologie",
            language=QueryLanguage.FRENCH,
            priority=0.7,
        ),
    ]


@pytest.fixture
def sample_anomalies() -> list[Anomaly]:
    return [
        Anomaly(
            id="A-01",
            anomaly_type=AnomalyType.LANGUAGE_GAP,
            severity=Severity.HIGH,
            description="No Greek-language sources found for Amphipolis research",
            suggested_queries=["Ανασκαφή τάφου Αμφίπολης"],
        ),
        Anomaly(
            id="A-02",
            anomaly_type=AnomalyType.DISCIPLINE_GAP,
            severity=Severity.CRITICAL,
            description="No epigraphy specialist found despite inscriptions being present",
            suggested_queries=["Amphipolis inscriptions epigrapher"],
        ),
        Anomaly(
            id="A-03",
            anomaly_type=AnomalyType.DISCIPLINE_GAP,
            severity=Severity.CRITICAL,
            description="No osteology specialist found despite human remains",
            suggested_queries=["Amphipolis skeletal analysis osteologist"],
        ),
    ]


# ---------------------------------------------------------------------------
# Mock connector response data for Amphipolis
# ---------------------------------------------------------------------------

AMPHIPOLIS_CYCLE_0_RESPONSES: dict[str, str] = {
    "amphipolis tomb": (
        "The Amphipolis tomb is a large Macedonian tomb discovered in 2012 "
        "near Amphipolis, northern Greece. Lead archaeologist Katerina Peristeri "
        "directed the excavation under the Hellenic Ministry of Culture. "
        "The tomb dates to the 4th century BC and features caryatid sculptures, "
        "a mosaic floor, and multiple chambers. Some researchers believe it was "
        "built for a companion of Alexander the Great, possibly Hephaestion."
    ),
    "default": (
        "The Amphipolis tomb excavation has revealed significant archaeological "
        "findings including architectural elements from the Macedonian period."
    ),
}

AMPHIPOLIS_CYCLE_1_RESPONSES: dict[str, str] = {
    "amphipolis": (
        "Additional researchers involved in Amphipolis include Michalis Lefantzis "
        "(architect), Dimitrios Lazaridis (historical excavations), and scholars "
        "from Aristotle University of Thessaloniki. Theories include the "
        "Alexander burial hypothesis, Hephaestion memorial theory, and the "
        "royal family member theory. The Persephone mosaic and caryatids "
        "suggest high-status burial. Greek-language publications by Peristeri "
        "appeared in Archaiologiko Deltion."
    ),
    "default": (
        "Further investigation reveals additional scholarly work on the "
        "Amphipolis tomb from both Greek and international researchers."
    ),
}
