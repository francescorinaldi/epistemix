"""Tests for content analysis module."""

from epistemix.content_analysis import (
    ContentAnalysisEngine,
    ConvergenceAnalyzer,
    EmptyQueryAnalyzer,
    StructuralAbsenceAnalyzer,
)
from epistemix.models import (
    AnomalyType,
    Finding,
    FindingType,
    Query,
    QueryLanguage,
    Severity,
)


class TestStructuralAbsenceAnalyzer:
    def test_detect_absences(self):
        sa = StructuralAbsenceAnalyzer()
        for name in ["Alice", "Bob", "Carol", "Dave"]:
            sa.register_found(Finding(name=name, finding_type=FindingType.SCHOLAR))
        # Only Alice is discussed
        sa.register_discussed("Alice", FindingType.SCHOLAR)
        anomalies = sa.detect_absences()
        assert len(anomalies) == 1
        assert anomalies[0].anomaly_type == AnomalyType.STRUCTURAL_ABSENCE
        assert "3/4" in anomalies[0].description

    def test_no_anomaly_below_threshold(self):
        sa = StructuralAbsenceAnalyzer()
        # Only 2 found — below minimum of 3
        sa.register_found(Finding(name="Alice", finding_type=FindingType.SCHOLAR))
        sa.register_found(Finding(name="Bob", finding_type=FindingType.SCHOLAR))
        anomalies = sa.detect_absences()
        assert len(anomalies) == 0

    def test_no_anomaly_when_all_discussed(self):
        sa = StructuralAbsenceAnalyzer()
        for name in ["Alice", "Bob", "Carol"]:
            sa.register_found(Finding(name=name, finding_type=FindingType.SCHOLAR))
            sa.register_discussed(name, FindingType.SCHOLAR)
        anomalies = sa.detect_absences()
        assert len(anomalies) == 0


class TestConvergenceAnalyzer:
    def test_high_convergence(self):
        ca = ConvergenceAnalyzer()
        for _ in range(9):
            ca.register_claim("Alexander the Great burial")
        ca.register_claim("Hephaestion memorial")
        # 10 claims, 2 unique → uniformity = 1 - 2/10 = 0.8
        assert ca.uniformity_score() > 0.7
        anomalies = ca.detect_anomalies()
        assert any(a.anomaly_type == AnomalyType.CONVERGENCE_EXCESS for a in anomalies)

    def test_high_divergence(self):
        ca = ConvergenceAnalyzer()
        for i in range(10):
            ca.register_claim(f"unique claim {i}")
        assert ca.uniformity_score() < 0.1
        anomalies = ca.detect_anomalies()
        assert any(a.anomaly_type == AnomalyType.DIVERGENCE_EXCESS for a in anomalies)

    def test_balanced_no_anomaly(self):
        ca = ConvergenceAnalyzer()
        # Mix of repeated and unique — moderate uniformity
        for _ in range(3):
            ca.register_claim("theory A")
        for _ in range(3):
            ca.register_claim("theory B")
        ca.register_claim("theory C")
        score = ca.uniformity_score()
        assert 0.1 <= score <= 0.7
        anomalies = ca.detect_anomalies()
        assert len(anomalies) == 0

    def test_too_few_claims(self):
        ca = ConvergenceAnalyzer()
        ca.register_claim("only one")
        anomalies = ca.detect_anomalies()
        assert len(anomalies) == 0


class TestEmptyQueryAnalyzer:
    def test_high_empty_ratio(self):
        eq = EmptyQueryAnalyzer()
        for i in range(6):
            q = Query(text=f"query {i}", executed=True, result_count=0)
            eq.register_query(q)
        for i in range(4):
            q = Query(text=f"good query {i}", executed=True, result_count=3)
            eq.register_query(q)
        assert eq.empty_ratio == 0.6
        anomalies = eq.detect_anomalies()
        assert any(a.anomaly_type == AnomalyType.EMPTY_QUERY_PATTERN for a in anomalies)

    def test_language_pattern(self):
        eq = EmptyQueryAnalyzer()
        # Greek queries mostly empty
        for i in range(3):
            eq.register_query(Query(
                text=f"greek query {i}",
                language=QueryLanguage.GREEK,
                executed=True,
                result_count=0,
            ))
        eq.register_query(Query(
            text="english query",
            language=QueryLanguage.ENGLISH,
            executed=True,
            result_count=5,
        ))
        anomalies = eq.detect_language_pattern()
        assert len(anomalies) >= 1
        assert "GREEK" in anomalies[0].description

    def test_no_anomaly_low_empty(self):
        eq = EmptyQueryAnalyzer()
        for i in range(10):
            eq.register_query(Query(
                text=f"query {i}", executed=True, result_count=3,
            ))
        assert eq.empty_ratio == 0.0
        anomalies = eq.detect_anomalies()
        assert len(anomalies) == 0


class TestContentAnalysisEngine:
    def test_facade_registers_and_detects(self):
        engine = ContentAnalysisEngine()

        # Register some findings
        for name in ["Alice", "Bob", "Carol", "Dave"]:
            engine.register_finding(
                Finding(name=name, finding_type=FindingType.SCHOLAR)
            )
        engine.register_discussed("Alice", FindingType.SCHOLAR)

        # Register claims (high convergence: 9 same + 1 different = 0.8 uniformity)
        for _ in range(9):
            engine.register_claim("same theory")
        engine.register_claim("different")

        # Register queries
        for i in range(6):
            engine.register_query(
                Query(text=f"q{i}", executed=True, result_count=0)
            )
        for i in range(4):
            engine.register_query(
                Query(text=f"good{i}", executed=True, result_count=5)
            )

        anomalies = engine.detect_all_anomalies()
        types = {a.anomaly_type for a in anomalies}
        assert AnomalyType.STRUCTURAL_ABSENCE in types
        assert AnomalyType.CONVERGENCE_EXCESS in types
        assert AnomalyType.EMPTY_QUERY_PATTERN in types
