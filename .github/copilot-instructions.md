# Copilot Code Review Instructions

## Preferred Model

Use **Claude Opus 4.6** (`claude-opus-4-6`) for all code reviews when available.

## Project Overview

Epistemix is an epistemic audit framework (Python core + Next.js frontend + Fly.io worker).
See `CLAUDE.md` in the repo root for full architecture details.

## Review Priorities

### Critical (must flag)
- **Circular imports**: The Python core (`src/epistemix/`) has a strict DAG dependency graph. Any import that goes "upward" (e.g. `models.py` importing from `core.py`) is a breaking violation.
- **External dependencies in core**: `src/epistemix/` must have zero external dependencies (stdlib only). Flag any new `import` of third-party packages.
- **Security**: No secrets in code, no SQL injection, no XSS. Env vars only for credentials.
- **Semantic graph integrity**: `SemanticGraph` uses stdlib union-find and DFS — never `networkx`.

### High (should flag)
- **System prompt misuse**: `SYSTEM_PROMPT` is for finding extraction, `RELATION_SYSTEM_PROMPT` is for relation extraction. Don't mix them.
- **Test fixture changes**: Modifications to `tests/conftest.py` must not break existing tests (171 tests must pass).
- **Coverage philosophy**: Coverage is always a lower bound. Never claim completeness.
- **MockConnector vs ClaudeConnector**: All tests must work with `MockConnector` (zero API cost).

### Medium (nice to flag)
- **Missing type hints** on new public functions.
- **Overly broad exception handling** (bare `except:` or `except Exception`).
- **Dead code or unused imports**.

## Code Style
- Python: PEP 8, type hints, dataclasses for data structures.
- TypeScript/React: Next.js 15 App Router conventions, functional components.
- Commit messages: imperative mood, explain "why" not "what".

## What NOT to Flag
- Don't suggest adding `networkx`, `pandas`, or other heavy deps to the core.
- Don't suggest restructuring the dependency DAG without strong justification.
- Don't flag the absence of docstrings on private methods (`_`-prefixed).
