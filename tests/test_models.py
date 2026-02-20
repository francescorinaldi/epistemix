"""Tests for Epistemix data models."""

from epistemix.models import (
    Anomaly,
    AnomalyType,
    CoverageScore,
    Finding,
    FindingType,
    Postulate,
    PostulateStatus,
    QueryLanguage,
    ResearchState,
    Severity,
)


class TestSeverity:
    def test_ordering(self):
        assert Severity.CRITICAL < Severity.HIGH
        assert Severity.HIGH < Severity.MEDIUM
        assert Severity.CRITICAL < Severity.MEDIUM

    def test_equality(self):
        assert Severity.CRITICAL <= Severity.CRITICAL
        assert not Severity.HIGH < Severity.HIGH


class TestFinding:
    def test_dedup_by_name_and_type(self):
        f1 = Finding(name="Katerina Peristeri", finding_type=FindingType.SCHOLAR)
        f2 = Finding(name="katerina peristeri", finding_type=FindingType.SCHOLAR)
        assert f1 == f2
        assert hash(f1) == hash(f2)

    def test_different_type_not_equal(self):
        f1 = Finding(name="Amphipolis", finding_type=FindingType.EVIDENCE)
        f2 = Finding(name="Amphipolis", finding_type=FindingType.INSTITUTION)
        assert f1 != f2

    def test_strip_whitespace(self):
        f1 = Finding(name="  Peristeri  ", finding_type=FindingType.SCHOLAR)
        f2 = Finding(name="Peristeri", finding_type=FindingType.SCHOLAR)
        assert f1 == f2

    def test_set_dedup(self):
        f1 = Finding(name="Peristeri", finding_type=FindingType.SCHOLAR)
        f2 = Finding(name="peristeri", finding_type=FindingType.SCHOLAR)
        f3 = Finding(name="Lefantzis", finding_type=FindingType.SCHOLAR)
        assert len({f1, f2, f3}) == 2


class TestPostulate:
    def test_confirm(self):
        p = Postulate(id="P-01", description="test", meta_axiom_id="MA-01")
        assert p.status == PostulateStatus.UNCONFIRMED
        p.confirm("Peristeri")
        assert p.status == PostulateStatus.CONFIRMED
        assert "Peristeri" in p.confirming_findings

    def test_confirm_idempotent(self):
        p = Postulate(id="P-01", description="test", meta_axiom_id="MA-01")
        p.confirm("Peristeri")
        p.confirm("Peristeri")
        assert p.confirming_findings.count("Peristeri") == 1

    def test_refute(self):
        p = Postulate(id="P-01", description="test", meta_axiom_id="MA-01")
        p.refute("insufficient evidence")
        assert p.status == PostulateStatus.REFUTED


class TestAnomaly:
    def test_dedup(self):
        a1 = Anomaly(
            id="A-01",
            anomaly_type=AnomalyType.LANGUAGE_GAP,
            severity=Severity.HIGH,
            description="No Greek sources found",
        )
        a2 = Anomaly(
            id="A-02",
            anomaly_type=AnomalyType.LANGUAGE_GAP,
            severity=Severity.MEDIUM,
            description="no greek sources found",
        )
        assert a1 == a2
        assert len({a1, a2}) == 1

    def test_different_type_not_equal(self):
        a1 = Anomaly(
            id="A-01",
            anomaly_type=AnomalyType.LANGUAGE_GAP,
            severity=Severity.HIGH,
            description="Gap found",
        )
        a2 = Anomaly(
            id="A-02",
            anomaly_type=AnomalyType.THEORY_GAP,
            severity=Severity.HIGH,
            description="Gap found",
        )
        assert a1 != a2


class TestCoverageScore:
    def test_percentage(self):
        cs = CoverageScore(confirmed=5, total=10)
        assert cs.percentage == 50.0

    def test_zero_total(self):
        cs = CoverageScore(confirmed=0, total=0)
        assert cs.percentage == 0.0

    def test_repr(self):
        cs = CoverageScore(confirmed=3, total=8, anomaly_count=2, cycle=1)
        assert "37.5%" in repr(cs)
        assert "cycle=1" in repr(cs)


class TestResearchState:
    def test_add_finding_new(self, amphipolis_state):
        f = Finding(name="Peristeri", finding_type=FindingType.SCHOLAR)
        assert amphipolis_state.add_finding(f) is True
        assert len(amphipolis_state.findings) == 1

    def test_add_finding_duplicate(self, amphipolis_state):
        f1 = Finding(name="Peristeri", finding_type=FindingType.SCHOLAR)
        f2 = Finding(name="peristeri", finding_type=FindingType.SCHOLAR)
        amphipolis_state.add_finding(f1)
        assert amphipolis_state.add_finding(f2) is False
        assert len(amphipolis_state.findings) == 1

    def test_add_anomaly_new(self, amphipolis_state):
        a = Anomaly(
            id="A-01",
            anomaly_type=AnomalyType.LANGUAGE_GAP,
            severity=Severity.HIGH,
            description="No Greek sources",
        )
        assert amphipolis_state.add_anomaly(a) is True

    def test_add_anomaly_duplicate(self, amphipolis_state):
        a1 = Anomaly(
            id="A-01",
            anomaly_type=AnomalyType.LANGUAGE_GAP,
            severity=Severity.HIGH,
            description="No Greek sources",
        )
        a2 = Anomaly(
            id="A-02",
            anomaly_type=AnomalyType.LANGUAGE_GAP,
            severity=Severity.MEDIUM,
            description="no greek sources",
        )
        amphipolis_state.add_anomaly(a1)
        assert amphipolis_state.add_anomaly(a2) is False

    def test_unique_findings(self, amphipolis_state, sample_findings):
        for f in sample_findings:
            amphipolis_state.add_finding(f)
        assert len(amphipolis_state.unique_findings) == len(sample_findings)

    def test_current_coverage(self, amphipolis_state, sample_postulates):
        amphipolis_state.postulates = sample_postulates
        sample_postulates[0].confirm("test")
        sample_postulates[1].confirm("test")
        cov = amphipolis_state.current_coverage()
        assert cov.confirmed == 2
        assert cov.total == 5
        assert cov.percentage == 40.0

    def test_to_dict(self, amphipolis_state):
        result = amphipolis_state.to_dict()
        assert result["topic"] == "Amphipolis tomb excavation"
        assert result["country"] == "Greece"
        assert "coverage_percentage" in result
