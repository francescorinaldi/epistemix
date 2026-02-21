---
applyTo: "src/epistemix/**/*.py"
---

# Python Core Library Rules

This is the zero-dependency core of Epistemix. Every module here uses stdlib only.

## Dependency DAG (strict — violations break the build)

```
meta_axioms.py ──┐
                 │
models.py ───────┤
                 ├──► semantic_graph.py ──┐
                 ├──► disciplines.py ─────┤
                 ├──► content_analysis.py ┤
                 │                        │
                 ├──► connector.py        │
                 │       │                │
                 │       ▼                ▼
                 └──► core.py ──────► multi_agent.py
                                          │
                                          ▼
                                       run.py
```

Never import upward. `models.py` imports nothing from the project. `core.py` imports from everything above it.

## Constraints

- Zero external dependencies: Python standard library only (for example: `dataclasses`, `enum`, `collections`, `re`, `json`, `time`, `abc`, `typing`)
- Never add `networkx`, `pandas`, `numpy`, or any third-party package
- `SemanticGraph` uses stdlib union-find and DFS
- `SYSTEM_PROMPT` is for finding extraction only; `RELATION_SYSTEM_PROMPT` is for relation extraction only
- All data structures live in `models.py` to prevent circular imports
- Coverage is always a lower bound — never claim completeness
- All tests must work with `MockConnector` (zero API cost)
