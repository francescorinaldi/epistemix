"""Tests for disciplinary expectations."""

from epistemix.disciplines import DisciplineExpectations, EVIDENCE_DISCIPLINE_MAP
from epistemix.models import (
    AnomalyType,
    Finding,
    FindingType,
    PostulateStatus,
    Severity,
)


def _evidence(name: str, description: str) -> Finding:
    return Finding(
        name=name,
        finding_type=FindingType.EVIDENCE,
        description=description,
    )


def _scholar(name: str, description: str) -> Finding:
    return Finding(
        name=name,
        finding_type=FindingType.SCHOLAR,
        description=description,
    )


class TestDisciplineExpectations:
    def test_register_inscription_evidence(self):
        de = DisciplineExpectations()
        postulates = de.register_evidence(
            _evidence("Stone tablet", "Inscription found on marble slab")
        )
        assert len(postulates) >= 1
        assert "epigraphy" in de.all_expected_disciplines

    def test_register_human_remains(self):
        de = DisciplineExpectations()
        de.register_evidence(
            _evidence("Skeletal remains", "Human remains of five individuals")
        )
        assert "osteology" in de.all_expected_disciplines
        assert "physical anthropology" in de.all_expected_disciplines

    def test_register_mosaic(self):
        de = DisciplineExpectations()
        de.register_evidence(
            _evidence("Floor mosaic", "Mosaic depicting Persephone")
        )
        assert "art history" in de.all_expected_disciplines

    def test_confirm_from_finding(self):
        de = DisciplineExpectations()
        de.register_evidence(
            _evidence("Inscriptions", "Greek inscriptions found")
        )
        confirmed = de.confirm_from_finding(
            _scholar("Dr. Smith", "Epigraphy specialist at Athens University")
        )
        assert "epigraphy" in confirmed
        assert "epigraphy" not in de.missing_disciplines

    def test_missing_disciplines(self):
        de = DisciplineExpectations()
        de.register_evidence(
            _evidence("Bones", "Human remains and skeletal fragments")
        )
        de.register_evidence(
            _evidence("Mosaic floor", "Mosaic artwork")
        )
        # Don't confirm any specialist
        missing = de.missing_disciplines
        assert "osteology" in missing
        assert "art history" in missing

    def test_detect_anomalies_amphipolis(self):
        """Simulate the Amphipolis scenario: inscriptions, bones, mosaic
        found but no epigrapher, osteologist, or art historian."""
        de = DisciplineExpectations()
        de.register_evidence(
            _evidence("Stone inscriptions", "Greek inscriptions at entrance")
        )
        de.register_evidence(
            _evidence("Skeletal remains", "Human remains of five individuals")
        )
        de.register_evidence(
            _evidence("Persephone mosaic", "Floor mosaic in main chamber")
        )

        anomalies = de.detect_anomalies()
        types = {a.description for a in anomalies}
        # Should flag epigraphy, osteology, art history as missing
        assert any("epigraphy" in d for d in types)
        assert any("osteology" in d for d in types)
        assert any("art history" in d for d in types)

    def test_severity_multiple_evidence(self):
        de = DisciplineExpectations()
        # "burial" and "skeletal" both map to osteology
        de.register_evidence(_evidence("Burial site", "Burial chamber found"))
        de.register_evidence(_evidence("Bones", "Skeletal fragments analyzed"))
        anomalies = de.detect_anomalies()
        osteology_anomaly = next(
            (a for a in anomalies if "osteology" in a.description), None
        )
        assert osteology_anomaly is not None
        assert osteology_anomaly.severity == Severity.CRITICAL

    def test_no_anomalies_when_all_confirmed(self):
        de = DisciplineExpectations()
        de.register_evidence(
            _evidence("Inscriptions", "Greek inscriptions found")
        )
        de.confirm_from_finding(
            _scholar("Dr. Smith", "Epigraphy expert")
        )
        anomalies = de.detect_anomalies()
        assert len(anomalies) == 0

    def test_postulates_created(self):
        de = DisciplineExpectations()
        postulates = de.register_evidence(
            _evidence("Coins", "Bronze coins from Hellenistic period")
        )
        assert len(postulates) >= 1
        assert all(p.meta_axiom_id == "MA-05" for p in postulates)
        assert all(p.status == PostulateStatus.UNCONFIRMED for p in postulates)

    def test_postulate_confirmed_on_specialist_found(self):
        de = DisciplineExpectations()
        de.register_evidence(
            _evidence("Coins", "Numismatic evidence")
        )
        de.confirm_from_finding(
            _scholar("Dr. Jones", "Numismatics researcher")
        )
        confirmed = [p for p in de._postulates if p.status == PostulateStatus.CONFIRMED]
        assert len(confirmed) >= 1
