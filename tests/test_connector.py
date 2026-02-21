"""Tests for the connector module."""

from epistemix.connector import MockConnector, extract_json
from epistemix.models import Finding, GapType, RelationType, SearchQuery, SemanticRelation, Severity


class TestMockConnector:
    def test_register_and_execute(self):
        connector = MockConnector()
        connector.register_findings("amphipolis", [
            Finding(source="Paper A", language="en", author="Alice"),
        ])
        query = SearchQuery(
            query="Amphipolis tomb research",
            language="en",
        )
        findings = connector.execute_query(query)
        assert len(findings) == 1
        assert findings[0].author == "Alice"
        assert query.executed is True

    def test_no_match_returns_empty(self):
        connector = MockConnector()
        query = SearchQuery(query="unrelated topic", language="en")
        findings = connector.execute_query(query)
        assert len(findings) == 0

    def test_case_insensitive_matching(self):
        connector = MockConnector()
        connector.register_findings("AMPHIPOLIS", [
            Finding(source="Paper", language="en"),
        ])
        query = SearchQuery(query="amphipolis research", language="en")
        findings = connector.execute_query(query)
        assert len(findings) == 1

    def test_execute_batch(self):
        connector = MockConnector()
        connector.register_findings("topic", [
            Finding(source="P1", language="en"),
        ])
        queries = [
            SearchQuery(query="topic one", language="en"),
            SearchQuery(query="topic two", language="en"),
        ]
        findings = connector.execute_batch(queries)
        assert len(findings) == 2

    def test_batch_with_limit(self):
        connector = MockConnector()
        connector.register_findings("topic", [
            Finding(source="P", language="en"),
        ])
        queries = [
            SearchQuery(query="topic 1", language="en"),
            SearchQuery(query="topic 2", language="en"),
            SearchQuery(query="topic 3", language="en"),
        ]
        findings = connector.execute_batch(queries, limit=2)
        assert connector.call_count == 2

    def test_total_cost_is_zero(self):
        connector = MockConnector()
        assert connector.total_cost == 0.0

    def test_call_log(self):
        connector = MockConnector()
        q = SearchQuery(query="test", language="en")
        connector.execute_query(q)
        assert len(connector.call_log) == 1


class TestMockConnectorRelations:
    def test_extract_relations_returns_registered(self):
        connector = MockConnector()
        relations = [
            SemanticRelation(
                source="Alice", target="Bob",
                relation=RelationType.CITES, confidence=0.9,
                evidence="Alice cites Bob", language="en",
            ),
        ]
        connector.register_relations(relations)
        result = connector.extract_relations([])
        assert len(result) == 1
        assert result[0].source == "Alice"

    def test_extract_relations_empty_by_default(self):
        connector = MockConnector()
        result = connector.extract_relations([])
        assert result == []


class TestExtractJson:
    def test_json_block(self):
        text = '```json\n[{"key": "value"}]\n```'
        result = extract_json(text)
        assert result == [{"key": "value"}]

    def test_bare_json_object(self):
        text = 'Some text {"key": "value"} more text'
        result = extract_json(text)
        assert result == {"key": "value"}

    def test_bare_json_array(self):
        text = 'Text [1, 2, 3] more'
        result = extract_json(text)
        assert result == [1, 2, 3]

    def test_no_json(self):
        text = "No json here at all"
        result = extract_json(text)
        assert result is None

    def test_invalid_json(self):
        text = "```json\n{invalid}\n```"
        result = extract_json(text)
        assert result is None


class TestMockConnectorLocalizedQueries:
    def test_register_and_generate(self):
        connector = MockConnector()
        connector.register_localized_queries("ar", [
            "\u0628\u062d\u062b \u0623\u062b\u0631\u064a",
            "\u062f\u0631\u0627\u0633\u0629 \u0639\u0644\u0645 \u0627\u0644\u0622\u062b\u0627\u0631",
        ])
        queries = connector.generate_localized_queries(
            "archaeology", "ar", "archaeology",
        )
        assert len(queries) == 2
        assert "\u0628\u062d\u062b \u0623\u062b\u0631\u064a" in queries

    def test_unregistered_language_returns_empty(self):
        connector = MockConnector()
        queries = connector.generate_localized_queries(
            "archaeology", "zh", "archaeology",
        )
        assert queries == []
