"""Tests for Epistemix data models."""

from epistemix.models import (
    Anomaly,
    CycleSnapshot,
    Entity,
    EntityType,
    Expectation,
    Finding,
    GapType,
    SearchQuery,
    Severity,
)


class TestSeverity:
    def test_ordering(self):
        assert Severity.LOW < Severity.MEDIUM
        assert Severity.MEDIUM < Severity.HIGH
        assert Severity.HIGH < Severity.CRITICAL

    def test_weight(self):
        assert Severity.LOW.weight == 1
        assert Severity.CRITICAL.weight == 5

    def test_le(self):
        assert Severity.HIGH <= Severity.HIGH
        assert Severity.MEDIUM <= Severity.HIGH


class TestEntity:
    def test_hash_case_insensitive(self):
        a = Entity(name="Alice", entity_type=EntityType.SCHOLAR)
        b = Entity(name="alice", entity_type=EntityType.SCHOLAR)
        assert a == b
        assert hash(a) == hash(b)

    def test_to_dict(self):
        e = Entity(
            name="Bob", entity_type=EntityType.INSTITUTION,
            times_mentioned=3, investigated=True,
        )
        d = e.to_dict()
        assert d["name"] == "Bob"
        assert d["entity_type"] == "institution"
        assert d["times_mentioned"] == 3


class TestExpectation:
    def test_satisfy(self):
        exp = Expectation(
            description="Test",
            gap_type=GapType.LINGUISTIC,
            severity_if_unmet=Severity.HIGH,
        )
        assert not exp.met
        exp.satisfy("found it")
        assert exp.met
        assert exp.evidence == "found it"

    def test_to_dict(self):
        exp = Expectation(
            description="Test",
            gap_type=GapType.TEMPORAL,
            severity_if_unmet=Severity.MEDIUM,
            met=True,
            evidence="2024",
        )
        d = exp.to_dict()
        assert d["gap_type"] == "temporal"
        assert d["met"] is True


class TestFinding:
    def test_dedup_same_source_and_language(self):
        a = Finding(source="Paper A", language="en")
        b = Finding(source="paper a", language="en", author="Alice")
        assert a == b

    def test_different_language_not_equal(self):
        a = Finding(source="Paper A", language="en")
        b = Finding(source="Paper A", language="fr")
        assert a != b

    def test_to_dict(self):
        f = Finding(
            source="Test", language="en",
            author="Alice", institution="MIT",
            theory_supported="Theory X", year=2024,
        )
        d = f.to_dict()
        assert d["author"] == "Alice"
        assert d["year"] == 2024

    def test_repr(self):
        f = Finding(source="Paper", language="en", year=2024)
        assert "[en]" in repr(f)
        assert "2024" in repr(f)


class TestAnomaly:
    def test_dedup_same_type_and_description(self):
        a = Anomaly(
            description="Missing language", gap_type=GapType.LINGUISTIC,
            severity=Severity.HIGH,
        )
        b = Anomaly(
            description="missing language", gap_type=GapType.LINGUISTIC,
            severity=Severity.MEDIUM,
        )
        assert a == b

    def test_different_gap_type_not_equal(self):
        a = Anomaly(description="X", gap_type=GapType.LINGUISTIC, severity=Severity.HIGH)
        b = Anomaly(description="X", gap_type=GapType.TEMPORAL, severity=Severity.HIGH)
        assert a != b

    def test_to_dict(self):
        a = Anomaly(
            description="Test", gap_type=GapType.VOICE,
            severity=Severity.CRITICAL, recommendation="Investigate",
        )
        d = a.to_dict()
        assert d["severity"] == "critical"
        assert d["recommendation"] == "Investigate"


class TestSearchQuery:
    def test_to_dict(self):
        q = SearchQuery(
            query="test", language="en",
            priority=Severity.HIGH, target_gap=GapType.LINGUISTIC,
        )
        d = q.to_dict()
        assert d["priority"] == "high"
        assert d["target_gap"] == "linguistic"


class TestCycleSnapshot:
    def test_to_dict(self):
        snap = CycleSnapshot(
            cycle=1, n_postulate_scholars=5, n_postulate_theories=2,
            n_postulate_institutions=3, n_expectations=10,
            n_expectations_met=7, n_findings=15, n_anomalies=4,
            coverage_score=65.3,
        )
        d = snap.to_dict()
        assert d["cycle"] == 1
        assert d["percentage"] == 65.3
        assert d["confirmed"] == 7
