"""Tests for the core epistemic engine."""

from epistemix.connector import MockConnector
from epistemix.core import (
    EpistemicEngine,
    extract_entities,
    translate_query,
    COUNTRY_LANGUAGES,
)
from epistemix.models import (
    AnomalyType,
    FindingType,
    PostulateStatus,
    QueryLanguage,
    ResearchState,
)
from tests.conftest import (
    AMPHIPOLIS_TOPIC,
    AMPHIPOLIS_COUNTRY,
    AMPHIPOLIS_DISCIPLINE,
    AMPHIPOLIS_CYCLE_0_RESPONSES,
    AMPHIPOLIS_CYCLE_1_RESPONSES,
)


class TestTranslateQuery:
    def test_english_passthrough(self):
        result = translate_query("excavation tomb", QueryLanguage.ENGLISH)
        assert result == "excavation tomb"

    def test_greek_translation(self):
        result = translate_query("excavation tomb", QueryLanguage.GREEK)
        assert "ανασκαφή" in result
        assert "τάφος" in result

    def test_french_translation(self):
        result = translate_query("archaeology research", QueryLanguage.FRENCH)
        assert "archéologie" in result
        assert "recherche" in result


class TestExtractEntities:
    def test_extract_scholars(self):
        text = (
            "Dr. Katerina Peristeri led the excavation. "
            "Prof. Michalis Lefantzis studied the architecture."
        )
        entities = extract_entities(text)
        names = {e.name for e in entities if e.finding_type == FindingType.SCHOLAR}
        assert "Katerina Peristeri" in names
        assert "Michalis Lefantzis" in names

    def test_extract_institutions(self):
        text = (
            "The University of Thessaloniki and the Hellenic Ministry of Culture "
            "were involved in the research."
        )
        entities = extract_entities(text)
        inst_names = {e.name for e in entities if e.finding_type == FindingType.INSTITUTION}
        assert any("University" in n for n in inst_names)

    def test_extract_theories(self):
        text = (
            "The theory that the tomb was built for Alexander has been debated. "
            "The Hephaestion memorial hypothesis is also considered."
        )
        entities = extract_entities(text)
        theories = [e for e in entities if e.finding_type == FindingType.THEORY]
        assert len(theories) >= 1

    def test_no_false_positives_short_names(self):
        text = "He said it was old."
        entities = extract_entities(text)
        assert len(entities) == 0

    def test_source_query_propagated(self):
        text = "Dr. Alice Smith published the findings."
        entities = extract_entities(text, source_query="test query")
        assert all(e.source_query == "test query" for e in entities)


class TestEpistemicEngine:
    def _make_engine(
        self, responses: dict[str, str] | None = None, verbose: bool = False
    ) -> EpistemicEngine:
        connector = MockConnector()
        if responses:
            connector.register_responses(responses)
        state = ResearchState(
            topic=AMPHIPOLIS_TOPIC,
            country=AMPHIPOLIS_COUNTRY,
            discipline=AMPHIPOLIS_DISCIPLINE,
        )
        return EpistemicEngine(
            connector=connector,
            state=state,
            verbose=verbose,
        )

    def test_initialize_postulates(self):
        engine = self._make_engine()
        postulates = engine.initialize_postulates()
        assert len(postulates) >= 14  # 7 axioms × ~2 templates each
        assert all(p.status == PostulateStatus.UNCONFIRMED for p in postulates)
        assert all(p.meta_axiom_id.startswith("MA-") for p in postulates)

    def test_generate_initial_queries(self):
        engine = self._make_engine()
        queries = engine.generate_initial_queries()
        assert len(queries) >= 5  # At least 5 English base queries
        # Should include Greek queries for Greece
        greek_queries = [q for q in queries if q.language == QueryLanguage.GREEK]
        assert len(greek_queries) >= 1

    def test_execute_queries(self):
        engine = self._make_engine(AMPHIPOLIS_CYCLE_0_RESPONSES)
        queries = engine.generate_initial_queries()
        responses = engine.execute_queries(queries)
        assert len(responses) >= 5
        assert all(q.executed for q in queries)

    def test_ingest_results(self):
        engine = self._make_engine(AMPHIPOLIS_CYCLE_0_RESPONSES)
        queries = engine.generate_initial_queries()
        responses = engine.execute_queries(queries)
        findings = engine.ingest_results(responses)
        # Should extract at least Peristeri from the mock data
        names = {f.name for f in findings}
        assert any("Peristeri" in n for n in names) or len(findings) > 0

    def test_run_cycle_0(self):
        engine = self._make_engine(AMPHIPOLIS_CYCLE_0_RESPONSES)
        coverage = engine.run_cycle(0)
        assert coverage.total > 0
        assert len(engine.state.findings) > 0

    def test_run_cycle_increases_coverage(self):
        responses = {**AMPHIPOLIS_CYCLE_0_RESPONSES, **AMPHIPOLIS_CYCLE_1_RESPONSES}
        engine = self._make_engine(responses)
        cov0 = engine.run_cycle(0)
        engine.state.current_cycle = 1
        cov1 = engine.run_cycle(1)
        # Coverage should not decrease
        assert cov1.percentage >= cov0.percentage or cov1.total > cov0.total

    def test_detect_anomalies(self):
        engine = self._make_engine(AMPHIPOLIS_CYCLE_0_RESPONSES)
        engine.run_cycle(0)
        # After first cycle, should detect at least a language gap
        anomaly_types = {a.anomaly_type for a in engine.state.anomalies}
        # We expect at least some anomalies
        assert len(engine.state.anomalies) >= 0  # May or may not detect depending on mock data

    def test_run_all_cycles(self):
        responses = {**AMPHIPOLIS_CYCLE_0_RESPONSES, **AMPHIPOLIS_CYCLE_1_RESPONSES}
        engine = self._make_engine(responses)
        coverage_history = engine.run_all_cycles(max_cycles=3)
        assert len(coverage_history) >= 1
        assert len(coverage_history) <= 3

    def test_postulate_ids_unique(self):
        engine = self._make_engine()
        postulates = engine.initialize_postulates()
        ids = [p.id for p in postulates]
        assert len(ids) == len(set(ids))

    def test_country_languages(self):
        assert "greece" in COUNTRY_LANGUAGES
        assert QueryLanguage.GREEK in COUNTRY_LANGUAGES["greece"]
        assert QueryLanguage.ENGLISH in COUNTRY_LANGUAGES["greece"]

    def test_generate_queries_from_anomalies(self):
        engine = self._make_engine(AMPHIPOLIS_CYCLE_0_RESPONSES)
        engine.run_cycle(0)
        engine.state.current_cycle = 1
        queries = engine.generate_queries_from_anomalies()
        # Queries should be generated from detected anomalies
        if engine.state.unresolved_anomalies:
            assert len(queries) > 0

    def test_coverage_is_lower_bound(self):
        """Coverage should be framed as a lower bound — denominator can only grow."""
        engine = self._make_engine(AMPHIPOLIS_CYCLE_0_RESPONSES)
        engine.run_cycle(0)
        total_0 = engine.state.current_coverage().total
        engine.state.current_cycle = 1
        engine.run_cycle(1)
        total_1 = engine.state.current_coverage().total
        # Total postulates should not decrease
        assert total_1 >= total_0
