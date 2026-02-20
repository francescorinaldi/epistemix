# Contributing to Epistemix

This guide is written for both human developers and Claude Code instances collaborating on this repository. If you are a Claude instance, read `CLAUDE.md` first — it has the essential project context.

---

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 20+ (for the web app)
- Docker (for local Supabase, optional)

### Install and Test

```bash
# Clone
git clone <repo-url>
cd epistemix

# Install Python core in dev mode
pip install -e ".[dev]"

# Run all 138 tests (should take <1 second)
pytest tests/ -v

# Install web app (optional — only if working on frontend)
cd web && npm install && cd ..
```

### Local Development

```bash
# Terminal 1: Python core (CLI)
epistemix --topic "Amphipolis tomb excavation" --country Greece --discipline archaeology -v

# Terminal 2: Web app
cd web && npm run dev   # http://localhost:3000

# Terminal 3: Local Supabase (optional)
docker-compose up supabase-db
```

---

## Project Rules

### Python Core Rules

1. **Zero external dependencies.** The `src/epistemix/` package uses only Python stdlib (dataclasses, enum, collections, re, json, abc, time). The only optional dependency is `anthropic` for live mode.

2. **Strict DAG imports.** Never import upward in the dependency graph. The order is:
   ```
   models → meta_axioms → citation_graph/disciplines/content_analysis → connector → core → multi_agent → run
   ```
   If you need a type from `core.py` in `models.py`, you're doing it wrong — restructure.

3. **All data structures in `models.py`.** No dataclass definitions in any other file. This prevents circular imports.

4. **Coverage is always a lower bound.** The denominator (total postulates) grows as we discover more. Never claim "100% coverage."

5. **MockConnector for all tests.** No test should require an API key or network access. Use pattern-matched canned responses.

6. **Tests must pass before commits.** Run `pytest tests/ -v` and ensure 138/138 pass (or more, if you add tests).

### Web App Rules

1. **App Router only.** Use Next.js App Router (`src/app/`), not Pages Router.
2. **Supabase for all state.** No separate state management library. Auth via Supabase Auth, data via Supabase client, real-time via Supabase Realtime.
3. **Dark theme.** All components use the dark color palette (bg: `#030712`/`#0f172a`, text: `#e2e8f0`/`#f1f5f9`, accent: `#6366f1`).
4. **Inline styles with `<style jsx>`.** No Tailwind, no CSS modules. Keep styles colocated with components.

### Worker Rules

1. **One-shot execution.** Worker boots, processes one audit, writes results, exits. No persistent connections or queues.
2. **Progress after every cycle.** Write coverage, findings, and anomalies to Supabase after each cycle (not just at the end). This powers real-time updates.
3. **Graceful failure.** On any exception, set `status='failed'` with `error_message` before exiting.

### Git Rules

1. **Never force-push to main.**
2. **Descriptive commit messages.** State what changed and why, not just "update."
3. **One logical change per commit.** Don't mix unrelated changes.

---

## How to Add Things

### Adding a New Meta-Axiom

1. Edit `src/epistemix/meta_axioms.py`:
   - Add a new `MetaAxiom` constant (e.g., `MA_08_METHODOLOGY`)
   - Add it to the `META_AXIOMS` tuple
   - Include postulate templates

2. Update `src/epistemix/core.py`:
   - Add confirmation logic in `_try_confirm_postulate()` for the new axiom ID

3. Add tests in `tests/test_core.py` verifying postulate generation and confirmation.

4. Update `CLAUDE.md` meta-axiom table.

### Adding a New Anomaly Type

1. Add the enum value in `src/epistemix/models.py` → `AnomalyType`
2. Add detection logic in the appropriate module:
   - Language/institution/theory gaps → `core.py`
   - Citation patterns → `citation_graph.py`
   - Discipline gaps → `disciplines.py`
   - Content patterns → `content_analysis.py`
3. Add a test for the new anomaly type.
4. Update `web/src/components/AnomalyPanel.tsx` → `TYPE_LABELS` dict.

### Adding a New Connector (e.g., OpenAI)

1. Create a new class in `src/epistemix/connector.py` that implements `BaseConnector`:
   ```python
   class OpenAIConnector(BaseConnector):
       def query(self, prompt: str, system: str = "") -> ConnectorResponse: ...
       def search(self, query: str) -> ConnectorResponse: ...
       @property
       def total_cost(self) -> float: ...
   ```
2. Add the optional dependency to `pyproject.toml` under `[project.optional-dependencies]`.
3. Update `worker/main.py` → `create_connector()` to support the new provider.

### Adding a New Web Component

1. Create the component in `web/src/components/NewComponent.tsx`.
2. Use inline `<style jsx>` with the dark theme palette.
3. Import and use in the appropriate page.
4. Type props using interfaces from `web/src/lib/types.ts`.

### Adding a New API Endpoint

1. Create the route file under `web/src/app/api/v1/...`.
2. Always authenticate with `supabase.auth.getUser()`.
3. Return proper HTTP status codes (401, 400, 404, 500).
4. Document in `API.md`.

### Adding a New Database Table

1. Create a new migration file in `supabase/migrations/` with the next sequence number.
2. Always add RLS policies.
3. Update `web/src/lib/types.ts` with the new table types.
4. Update `ARCHITECTURE.md` schema section.

---

## Testing

### Test Organization

| Test file | What it covers |
|-----------|---------------|
| `test_models.py` | Data structures: dedup, serialization, coverage calculation |
| `test_citation_graph.py` | School detection, citation islands, case-insensitivity |
| `test_disciplines.py` | Evidence→discipline mapping, gap detection, severity |
| `test_content_analysis.py` | Structural absence, convergence, empty query patterns |
| `test_connector.py` | MockConnector pattern matching, logging, JSON extraction |
| `test_core.py` | EpistemicEngine: postulates, queries, ingestion, cycles |
| `test_multi_agent.py` | Agent perspectives, arbiter comparison, blindness gap |
| `test_integrated.py` | Full pipeline with rich mock data |
| `test_amphipolis.py` | 4-cycle Amphipolis simulation (reference scenario) |

### Running Tests

```bash
pytest tests/ -v                     # All tests
pytest tests/test_core.py -v         # One module
pytest tests/test_core.py::TestEpistemicEngine::test_run_cycle_0 -v  # One test
pytest tests/ -v --tb=long           # Verbose tracebacks
pytest tests/ -v -x                  # Stop on first failure
```

### Writing Tests

- Use the fixtures in `conftest.py` (`amphipolis_state`, `sample_findings`, etc.)
- Use `MockConnector` with domain-specific responses
- Assert specific behavior, not implementation details
- Test edge cases (empty inputs, duplicates, zero coverage)

---

## File Ownership

When in doubt about where to make a change:

| Change type | File(s) to modify |
|-------------|-------------------|
| New data structure | `src/epistemix/models.py` |
| New axiom | `src/epistemix/meta_axioms.py` + `core.py` |
| Anomaly detection logic | `citation_graph.py` or `disciplines.py` or `content_analysis.py` |
| How queries are generated | `src/epistemix/core.py` |
| How results are parsed | `src/epistemix/core.py` → `extract_entities()` |
| AI provider | `src/epistemix/connector.py` |
| CLI flags | `src/epistemix/run.py` |
| Agent perspectives | `src/epistemix/multi_agent.py` |
| Frontend component | `web/src/components/` |
| API endpoint | `web/src/app/api/` |
| Database schema | `supabase/migrations/` |
| Worker behavior | `worker/main.py` |
| How worker writes to DB | `worker/supabase_writer.py` |
