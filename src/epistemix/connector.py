"""API connector — abstracts the AI provider.

BaseConnector (ABC) → MockConnector (for tests) and ClaudeConnector (for production).
The connector abstraction means you can develop and test with zero API cost,
then flip one env var to go live.

The connector's job is to execute SearchQuery objects and return Finding objects.
MockConnector returns pre-configured findings; ClaudeConnector calls the API
and parses responses into structured findings.
"""

from __future__ import annotations

import json
import re
import time
from abc import ABC, abstractmethod
from typing import Any

from epistemix.models import Finding, SearchQuery


# ============================================================
# SYSTEM PROMPT (for Claude API)
# ============================================================

SYSTEM_PROMPT = """You are a research assistant helping with an epistemic audit.
For each search query, return structured findings as a JSON array.

Each finding should be a JSON object with these fields:
- "source": title/name of the source (string, required)
- "language": ISO 639-1 language code (string, required)
- "author": author name if known (string)
- "institution": affiliated institution if known (string)
- "theory_supported": which theory this finding supports, if any (string)
- "source_type": one of "peer_reviewed", "institutional", "news", "journalistic" (string)
- "year": publication year if known (integer)
- "entities_mentioned": list of entity names mentioned (array of strings)

Return ONLY a JSON array of findings. No other text."""


# ============================================================
# BASE CONNECTOR
# ============================================================

class BaseConnector(ABC):
    """Abstract base class for AI connectors."""

    @abstractmethod
    def execute_query(self, query: SearchQuery) -> list[Finding]:
        """Execute a search query and return parsed findings."""

    @abstractmethod
    def execute_batch(
        self, queries: list[SearchQuery], limit: int = 0
    ) -> list[Finding]:
        """Execute multiple queries, return all findings."""

    @property
    @abstractmethod
    def total_cost(self) -> float:
        """Total cost of all API calls so far."""

    @property
    @abstractmethod
    def call_count(self) -> int:
        """Number of API calls made."""


# ============================================================
# MOCK CONNECTOR (for tests)
# ============================================================

class MockConnector(BaseConnector):
    """Pattern-matched mock connector that returns pre-configured findings.

    Register findings for specific query patterns. When a query matches,
    those findings are returned. Falls back to empty list.
    """

    def __init__(self) -> None:
        self._responses: dict[str, list[Finding]] = {}
        self._call_log: list[SearchQuery] = []

    def register_findings(
        self, pattern: str, findings: list[Finding]
    ) -> None:
        """Register findings for a query pattern (case-insensitive)."""
        self._responses[pattern.lower()] = findings

    def register_findings_map(
        self, mapping: dict[str, list[Finding]]
    ) -> None:
        """Register multiple pattern → findings mappings."""
        for pattern, findings in mapping.items():
            self.register_findings(pattern, findings)

    def execute_query(self, query: SearchQuery) -> list[Finding]:
        """Match query against patterns and return findings."""
        self._call_log.append(query)
        query.executed = True
        query_lower = query.query.lower()

        for pattern, findings in self._responses.items():
            if pattern in query_lower:
                # Set cycle and language on findings
                for f in findings:
                    if not f.language:
                        f.language = query.language
                return findings

        return []

    def execute_batch(
        self, queries: list[SearchQuery], limit: int = 0
    ) -> list[Finding]:
        """Execute all queries (or up to limit)."""
        all_findings: list[Finding] = []
        batch = queries[:limit] if limit > 0 else queries
        for q in batch:
            all_findings.extend(self.execute_query(q))
        return all_findings

    @property
    def total_cost(self) -> float:
        return 0.0

    @property
    def call_count(self) -> int:
        return len(self._call_log)

    @property
    def call_log(self) -> list[SearchQuery]:
        return self._call_log


# ============================================================
# CLAUDE CONNECTOR (for production)
# ============================================================

class ClaudeConnector(BaseConnector):
    """Production connector using the Anthropic API.

    Features:
    - Web search via tool use
    - Budget tracking
    - Exponential backoff retry
    - Structured JSON → Finding parsing
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
        max_budget: float = 10.0,
    ) -> None:
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "The 'anthropic' package is required for ClaudeConnector. "
                "Install with: pip install 'epistemix[live]'"
            )

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._max_budget = max_budget
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._call_count = 0

    def execute_query(self, query: SearchQuery) -> list[Finding]:
        """Execute a query via Claude API with web search."""
        if self.total_cost >= self._max_budget:
            return []

        prompt = (
            f"Search for: {query.query}\n"
            f"Language: {query.language}\n"
            f"Rationale: {query.rationale}\n\n"
            "Return findings as a JSON array."
        )

        messages = [{"role": "user", "content": prompt}]
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": 4096,
            "system": SYSTEM_PROMPT,
            "messages": messages,
            "tools": [
                {
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 3,
                }
            ],
        }

        response = self._call_with_retry(kwargs)
        self._call_count += 1
        query.executed = True

        # Parse response
        text = self._extract_text(response)
        self._track_usage(response)
        return self._parse_findings(text, query)

    def execute_batch(
        self, queries: list[SearchQuery], limit: int = 0
    ) -> list[Finding]:
        """Execute queries in priority order."""
        sorted_queries = sorted(
            queries, key=lambda q: q.priority.weight, reverse=True
        )
        batch = sorted_queries[:limit] if limit > 0 else sorted_queries
        all_findings: list[Finding] = []
        for q in batch:
            if self.total_cost >= self._max_budget:
                break
            findings = self.execute_query(q)
            all_findings.extend(findings)
        return all_findings

    def _call_with_retry(
        self, kwargs: dict[str, Any], max_retries: int = 3
    ) -> Any:
        """Call API with exponential backoff."""
        import anthropic

        for attempt in range(max_retries + 1):
            try:
                return self._client.messages.create(**kwargs)
            except anthropic.RateLimitError:
                if attempt == max_retries:
                    raise
                time.sleep(2 ** (attempt + 1))
            except anthropic.APIStatusError as e:
                if e.status_code == 529 and attempt < max_retries:
                    time.sleep(2 ** (attempt + 1))
                else:
                    raise

    def _extract_text(self, response: Any) -> str:
        """Extract text from API response."""
        parts = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts)

    def _track_usage(self, response: Any) -> None:
        """Track token usage."""
        self._total_input_tokens += response.usage.input_tokens
        self._total_output_tokens += response.usage.output_tokens

    def _parse_findings(
        self, text: str, query: SearchQuery
    ) -> list[Finding]:
        """Parse JSON response into Finding objects."""
        json_data = extract_json(text)
        if not json_data or not isinstance(json_data, list):
            return []

        findings: list[Finding] = []
        for item in json_data:
            if not isinstance(item, dict):
                continue
            findings.append(Finding(
                source=item.get("source", ""),
                language=item.get("language", query.language),
                author=item.get("author", ""),
                institution=item.get("institution", ""),
                theory_supported=item.get("theory_supported", ""),
                source_type=item.get("source_type", ""),
                year=item.get("year", 0),
                entities_mentioned=item.get("entities_mentioned", []),
                search_query_used=query.query,
            ))
        return findings

    @property
    def total_cost(self) -> float:
        input_cost = (self._total_input_tokens / 1000) * 0.003
        output_cost = (self._total_output_tokens / 1000) * 0.015
        return round(input_cost + output_cost, 4)

    @property
    def call_count(self) -> int:
        return self._call_count


# ============================================================
# UTILITIES
# ============================================================

def extract_json(text: str) -> dict[str, Any] | list[Any] | None:
    """Extract JSON from a text response.

    Looks for ```json blocks, bare JSON objects/arrays, or bracket scanning.
    """
    # Try ```json blocks
    json_block = re.search(r"```json\s*\n(.*?)\n\s*```", text, re.DOTALL)
    if json_block:
        try:
            return json.loads(json_block.group(1))
        except json.JSONDecodeError:
            pass

    # Try bare JSON
    for pattern in [r"\[.*\]", r"\{.*\}"]:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                continue

    return None
