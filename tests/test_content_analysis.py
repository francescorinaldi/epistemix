"""Tests for content analysis module."""

from epistemix.content_analysis import (
    ContentAnalysisEngine,
    ConvergenceAnalyzer,
    EmptyQueryAnalyzer,
    QueryResult,
    StructuralAbsenceDetector,
    StructuralFact,
    TheoryPosition,
)
from epistemix.models import GapType


class TestStructuralAbsenceDetector:
    def test_all_addressed(self):
        detector = StructuralAbsenceDetector()
        fact = StructuralFact(
            description="Tomb contents",
            items=["skeleton", "coins"],
        )
        fact.register_addressing("Theory A", ["skeleton", "coins"])
        detector.register_fact(fact)
        anomalies = detector.generate_anomalies()
        assert len(anomalies) == 0

    def test_unaddressed_items(self):
        detector = StructuralAbsenceDetector()
        fact = StructuralFact(
            description="Five individuals in tomb",
            items=["woman ~60", "man 35-45", "newborn", "cremated"],
        )
        fact.register_addressing("Theory A", ["woman ~60"])
        detector.register_fact(fact)
        anomalies = detector.generate_anomalies()
        assert len(anomalies) >= 1
        assert anomalies[0].gap_type == GapType.STRUCTURAL_ABSENCE

    def test_severity_increases_with_ratio(self):
        detector = StructuralAbsenceDetector()
        fact = StructuralFact(
            description="Test",
            items=["a", "b", "c", "d"],
        )
        # None addressed = 100% unaddressed = CRITICAL
        detector.register_fact(fact)
        anomalies = detector.generate_anomalies()
        assert anomalies[0].severity.value == "critical"


class TestConvergenceAnalyzer:
    def test_high_convergence(self):
        analyzer = ConvergenceAnalyzer()
        # 9 same answers + 1 different = high uniformity
        for i in range(9):
            analyzer.register_position(TheoryPosition(
                question="Who is buried?",
                theory=f"Scholar{i}",
                answer="Hephaestion",
            ))
        analyzer.register_position(TheoryPosition(
            question="Who is buried?",
            theory="Outlier",
            answer="Olympias",
        ))
        score = analyzer.uniformity_score()
        assert score > 0.7
        anomalies = analyzer.generate_anomalies()
        convergence = [
            a for a in anomalies
            if a.gap_type == GapType.CONVERGENCE_EXCESS
        ]
        assert len(convergence) >= 1

    def test_balanced_positions(self):
        analyzer = ConvergenceAnalyzer()
        analyzer.register_position(TheoryPosition(
            question="Q", theory="A", answer="X",
        ))
        analyzer.register_position(TheoryPosition(
            question="Q", theory="B", answer="Y",
        ))
        score = analyzer.uniformity_score()
        assert 0.0 <= score <= 0.5

    def test_empty_returns_zero(self):
        analyzer = ConvergenceAnalyzer()
        assert analyzer.uniformity_score() == 0.0


class TestEmptyQueryAnalyzer:
    def test_language_gap_detection(self):
        analyzer = EmptyQueryAnalyzer()
        # Greek: 3 queries, all empty
        for i in range(3):
            analyzer.register_result(QueryResult(
                query=f"query{i}", language="el", empty=True,
            ))
        # English: 2 queries, all productive
        for i in range(2):
            analyzer.register_result(QueryResult(
                query=f"query{i}", language="en",
                findings_count=3, empty=False,
            ))
        anomalies = analyzer.generate_anomalies()
        el_anomalies = [
            a for a in anomalies
            if "'el'" in a.description
        ]
        assert len(el_anomalies) >= 1

    def test_no_anomaly_when_productive(self):
        analyzer = EmptyQueryAnalyzer()
        for i in range(5):
            analyzer.register_result(QueryResult(
                query=f"q{i}", language="en",
                findings_count=2, empty=False,
            ))
        anomalies = analyzer.generate_anomalies()
        assert len(anomalies) == 0

    def test_language_productivity(self):
        analyzer = EmptyQueryAnalyzer()
        analyzer.register_result(QueryResult(
            query="q1", language="en", empty=False, findings_count=3,
        ))
        analyzer.register_result(QueryResult(
            query="q2", language="en", empty=True,
        ))
        stats = analyzer.language_productivity()
        assert stats["en"]["total"] == 2
        assert stats["en"]["empty"] == 1


class TestNegativePostulateGeneration:
    def test_empty_language_generates_negative_postulate(self):
        """Languages with > 50% empty queries produce NegativePostulates."""
        analyzer = EmptyQueryAnalyzer()
        # German: 3 queries, all empty
        for i in range(3):
            analyzer.register_result(QueryResult(
                query=f"german_query_{i}", language="de", empty=True,
            ))
        negatives = analyzer.generate_negative_postulates(cycle=2)
        assert len(negatives) >= 1
        assert negatives[0].language == "de"
        assert negatives[0].detected_at_cycle == 2

    def test_access_barrier_language(self):
        """Chinese queries should get access_barrier reason."""
        analyzer = EmptyQueryAnalyzer()
        for i in range(3):
            analyzer.register_result(QueryResult(
                query=f"chinese_query_{i}", language="zh", empty=True,
            ))
        negatives = analyzer.generate_negative_postulates()
        zh_negs = [n for n in negatives if n.language == "zh"]
        assert len(zh_negs) >= 1
        assert zh_negs[0].possible_reason == "access_barrier"
        assert "CNKI" in zh_negs[0].reformulation

    def test_wrong_terminology_reason(self):
        """All-empty non-barrier language gets wrong_terminology."""
        analyzer = EmptyQueryAnalyzer()
        for i in range(3):
            analyzer.register_result(QueryResult(
                query=f"german_query_{i}", language="de", empty=True,
            ))
        negatives = analyzer.generate_negative_postulates()
        de_negs = [n for n in negatives if n.language == "de"]
        assert len(de_negs) >= 1
        assert de_negs[0].possible_reason == "wrong_terminology"

    def test_no_negatives_for_productive_language(self):
        """Languages with good results produce no NegativePostulates."""
        analyzer = EmptyQueryAnalyzer()
        for i in range(5):
            analyzer.register_result(QueryResult(
                query=f"en_query_{i}", language="en",
                findings_count=3, empty=False,
            ))
        negatives = analyzer.generate_negative_postulates()
        assert len(negatives) == 0

    def test_mixed_results_genuinely_absent(self):
        """Language with some productive and mostly empty → genuinely_absent."""
        analyzer = EmptyQueryAnalyzer()
        # 1 productive, 4 empty = 80% empty
        analyzer.register_result(QueryResult(
            query="good", language="it",
            findings_count=2, empty=False,
        ))
        for i in range(4):
            analyzer.register_result(QueryResult(
                query=f"empty_{i}", language="it", empty=True,
            ))
        negatives = analyzer.generate_negative_postulates()
        it_negs = [n for n in negatives if n.language == "it"]
        assert len(it_negs) >= 1
        assert it_negs[0].possible_reason == "genuinely_absent"


class TestContentAnalysisEngine:
    def test_facade_collects_all_anomalies(self):
        engine = ContentAnalysisEngine()
        # Add some data to trigger anomalies
        engine.structural.register_fact(StructuralFact(
            description="Test",
            items=["a", "b", "c"],
        ))
        for i in range(9):
            engine.convergence.register_position(TheoryPosition(
                question="Q", theory=f"T{i}", answer="same",
            ))
        engine.convergence.register_position(TheoryPosition(
            question="Q", theory="outlier", answer="different",
        ))
        anomalies = engine.generate_all_anomalies()
        assert len(anomalies) >= 2  # structural + convergence

    def test_facade_generates_negative_postulates(self):
        """ContentAnalysisEngine facade should delegate to EmptyQueryAnalyzer."""
        engine = ContentAnalysisEngine()
        for i in range(3):
            engine.empty_queries.register_result(QueryResult(
                query=f"q{i}", language="de", empty=True,
            ))
        negatives = engine.generate_negative_postulates(cycle=1)
        assert len(negatives) >= 1
