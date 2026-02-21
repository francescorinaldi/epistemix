---
applyTo: "tests/**/*.py"
---

# Test Suite Rules

All tests must pass. Run the full suite with: `pytest tests/ -v`

## Fixtures

- `tests/conftest.py` contains shared fixtures and Amphipolis mock data
- Modifying fixtures risks breaking many tests — run the full suite after any change
- All tests use `MockConnector` (zero API cost, pattern-matched responses)

## Conventions

- Reference scenario: Amphipolis tomb excavation (Greece, archaeology)
- Use `MockConnector.register_findings()` for test data, never real API calls
- Use `MockConnector.register_relations()` for semantic graph test data
- Test file naming: most `test_<module>.py` files mirror `src/epistemix/<module>.py` (with a few scenario/utility exceptions)
