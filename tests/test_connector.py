"""Tests for the connector module."""

from epistemix.connector import MockConnector, ConnectorResponse, extract_json


class TestMockConnector:
    def test_pattern_matching(self):
        mc = MockConnector()
        mc.register_response("amphipolis", "Found the tomb!")
        resp = mc.query("Tell me about Amphipolis tomb")
        assert "Found the tomb!" in resp.text

    def test_default_response(self):
        mc = MockConnector()
        resp = mc.query("something random")
        assert "No specific information" in resp.text

    def test_search(self):
        mc = MockConnector()
        mc.register_response("amphipolis", "Tomb excavation results")
        resp = mc.search("Amphipolis tomb research")
        assert "Tomb excavation" in resp.text

    def test_call_logging(self):
        mc = MockConnector()
        mc.query("first query")
        mc.query("second query")
        assert mc.call_count == 2
        assert mc.call_log[0]["prompt"] == "first query"

    def test_search_logging(self):
        mc = MockConnector()
        mc.search("query one")
        mc.search("query two")
        assert mc.search_count == 2

    def test_zero_cost(self):
        mc = MockConnector()
        mc.query("test")
        assert mc.total_cost == 0.0

    def test_register_responses_bulk(self):
        mc = MockConnector()
        mc.register_responses({
            "topic a": "response a",
            "topic b": "response b",
        })
        assert "response a" in mc.query("topic a question").text
        assert "response b" in mc.query("topic b question").text

    def test_case_insensitive_matching(self):
        mc = MockConnector()
        mc.register_response("AMPHIPOLIS", "Found it!")
        resp = mc.query("amphipolis tomb")
        assert "Found it!" in resp.text

    def test_custom_default(self):
        mc = MockConnector()
        mc.set_default_response("Nothing here")
        resp = mc.query("random")
        assert resp.text == "Nothing here"


class TestConnectorResponse:
    def test_basic(self):
        resp = ConnectorResponse(text="hello", model="test")
        assert resp.text == "hello"
        assert resp.model == "test"
        assert resp.usage == {}


class TestExtractJson:
    def test_json_block(self):
        text = 'Here is the data:\n```json\n{"name": "test", "value": 42}\n```'
        result = extract_json(text)
        assert result == {"name": "test", "value": 42}

    def test_bare_json(self):
        text = 'The result is {"scholars": ["Alice", "Bob"]}'
        result = extract_json(text)
        assert result == {"scholars": ["Alice", "Bob"]}

    def test_json_array(self):
        text = 'Found: [1, 2, 3]'
        result = extract_json(text)
        assert result == [1, 2, 3]

    def test_no_json(self):
        text = "Just plain text with no JSON"
        result = extract_json(text)
        assert result is None

    def test_malformed_json(self):
        text = '{"broken": incomplete'
        result = extract_json(text)
        assert result is None
