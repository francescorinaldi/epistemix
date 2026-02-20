# Epistemix

Epistemic audit framework — detect unknown unknowns in research.

Epistemix predicts what knowledge *should* exist about a topic, then verifies whether it does. The gap between expectation and reality reveals blind spots: missing languages, absent disciplines, overlooked scholars, and unexamined theories.

## How it works

1. **Meta-axioms** generate predictions about what any well-studied topic should have (multiple languages, competing theories, diverse institutions, etc.)
2. **Multilingual queries** search across language barriers
3. **Entity extraction** identifies scholars, institutions, theories, and evidence
4. **Anomaly detection** flags gaps — missing disciplines, citation islands, convergence excess
5. **Multi-agent audit** — two agents with different weightings independently audit, then an arbiter identifies where they disagree ("known unknowns")

## Install

```bash
pip install -e ".[dev]"        # development (mock mode, tests)
pip install -e ".[live]"       # production (Claude API)
```

## Usage

```bash
# Mock mode (no API calls, for testing)
epistemix --topic "Amphipolis tomb excavation" --country Greece --discipline archaeology -v

# Live mode (requires ANTHROPIC_API_KEY)
epistemix --topic "CRISPR gene editing" --country USA --discipline biology --live --budget 5.0 -v

# Output to file
epistemix --topic "Amphipolis tomb" --country Greece --discipline archaeology -o report.json
```

## Python API

```python
from epistemix.connector import MockConnector
from epistemix.core import EpistemicEngine
from epistemix.models import ResearchState
from epistemix.multi_agent import MultiAgentSystem

# Single engine audit
connector = MockConnector()
state = ResearchState(topic="Amphipolis tomb", country="Greece", discipline="archaeology")
engine = EpistemicEngine(connector=connector, state=state)
coverage = engine.run_all_cycles(max_cycles=4)

# Multi-agent audit
mas = MultiAgentSystem(
    connector=connector,
    topic="Amphipolis tomb",
    country="Greece",
    discipline="archaeology",
)
result = mas.run()
print(f"Blindness gap: {result['combined']['blindness_gap']} points")
```

## Test

```bash
pytest -v
```

## Architecture

```
models.py           Data structures (Finding, Postulate, Anomaly, Query, etc.)
meta_axioms.py      7 Level 0 meta-axioms (domain-independent research truths)
citation_graph.py   Citation network analysis (schools, islands, priority ranking)
disciplines.py      Evidence → expected discipline mapping
content_analysis.py Structural absence, convergence, empty query pattern detection
connector.py        MockConnector (tests) / ClaudeConnector (production)
core.py             EpistemicEngine — the main audit cycle orchestrator
multi_agent.py      Dual-agent system (α institutional / β theoretical) + arbiter
run.py              CLI entry point
```
