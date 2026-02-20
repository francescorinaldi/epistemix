"""Tests for disciplinary expectations."""

from epistemix.disciplines import (
    ARCHAEOLOGY_DISCIPLINES,
    DisciplineAnalyzer,
    get_discipline_set,
)
from epistemix.models import Finding, GapType


class TestDisciplineTemplates:
    def test_archaeology_has_disciplines(self):
        assert len(ARCHAEOLOGY_DISCIPLINES) >= 8

    def test_required_disciplines_exist(self):
        required = [d for d in ARCHAEOLOGY_DISCIPLINES if d.required]
        assert len(required) >= 1  # At least field archaeology

    def test_get_discipline_set_default(self):
        disciplines = get_discipline_set("unknown")
        assert len(disciplines) > 0


class TestDisciplineAnalyzer:
    def test_detects_relevant_disciplines(self):
        analyzer = DisciplineAnalyzer("archaeology")
        findings = [
            Finding(
                source="Inscription study",
                language="en",
                author="Alice",
                entities_mentioned=["inscription", "monogram"],
            ),
        ]
        analyzer.ingest_findings(findings)
        summary = analyzer.coverage_summary()
        assert "Epigraphy" in summary["relevant_disciplines"]

    def test_detects_missing_specialist(self):
        analyzer = DisciplineAnalyzer("archaeology")
        findings = [
            Finding(
                source="Bone analysis",
                language="en",
                author="Alice",
                entities_mentioned=["skeleton", "burial", "human remains"],
            ),
        ]
        analyzer.ingest_findings(findings)
        anomalies = analyzer.generate_anomalies()
        disc_anomalies = [
            a for a in anomalies if a.gap_type == GapType.DISCIPLINE_GAP
        ]
        assert len(disc_anomalies) >= 1
        # Should flag Osteology as missing
        osteology = [
            a for a in disc_anomalies if "Osteology" in a.description
        ]
        assert len(osteology) >= 1

    def test_specialist_found_no_anomaly(self):
        analyzer = DisciplineAnalyzer("archaeology")
        findings = [
            Finding(
                source="DNA study by geneticist",
                language="en",
                author="geneticist Smith",
                entities_mentioned=["dna", "ancient dna", "geneticist"],
            ),
        ]
        analyzer.ingest_findings(findings)
        anomalies = analyzer.generate_anomalies()
        dna_anomalies = [
            a for a in anomalies if "DNA" in a.description
        ]
        assert len(dna_anomalies) == 0

    def test_generate_expectations(self):
        analyzer = DisciplineAnalyzer("archaeology")
        findings = [
            Finding(
                source="Excavation report",
                language="en",
                author="Alice",
                entities_mentioned=["excavation", "stratigraphy"],
            ),
        ]
        analyzer.ingest_findings(findings)
        expectations = analyzer.generate_expectations(cycle=1)
        assert len(expectations) >= 1

    def test_coverage_summary(self):
        analyzer = DisciplineAnalyzer("archaeology")
        findings = [
            Finding(
                source="Test archaeologist report",
                language="en",
                author="archaeologist Jones",
                entities_mentioned=[
                    "excavation", "archaeologist",
                ],
            ),
        ]
        analyzer.ingest_findings(findings)
        summary = analyzer.coverage_summary()
        assert "coverage_ratio" in summary
        assert isinstance(summary["coverage_ratio"], float)
