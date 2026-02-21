---
applyTo: "tests/**/*.py"
---

# Test Suite Rules

171 tests, all must pass. Test runner: `pytest tests/ -v`

## Fixtures

- `tests/conftest.py` contains shared fixtures and Amphipolis mock data
- Modifying fixtures risks breaking many tests — run the full suite after any change
- All tests use `MockConnector` (zero API cost, pattern-matched responses)

## Conventions

- Reference scenario: Amphipolis tomb excavation (Greece, archaeology)
- Use `MockConnector.register_findings()` for test data, never real API calls
- Use `MockConnector.register_relations()` for semantic graph test data
- Test file naming: `test_<module>.py` mirrors `src/epistemix/<module>.py`
