"""
EPISTEMIX v2 — API Connector

Bridges the framework to the real world via Claude API
with web search tool enabled.

Flow:
  SearchQuery (from Epistemix)
    → prompt for Claude
    → Claude searches the web
    → structured JSON response
    → Finding objects (back to Epistemix)

Requirements:
  - anthropic Python package: pip install anthropic
  - ANTHROPIC_API_KEY environment variable set
"""

from __future__ import annotations
import json
import time
import os
from dataclasses import dataclass, field
from typing import Optional

try:
    import anthropic
except ImportError:
    anthropic = None

from core import Finding, SearchQuery, Severity, GapType
from content_analysis import QueryResult


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class ConnectorConfig:
    """Configuration for the API connector."""
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 4096
    delay_between_calls: float = 1.0  # seconds
    max_retries: int = 3
    budget_per_cycle: int = 15    # max API calls per cycle
    total_budget: int = 80        # max API calls total
    verify_urls: bool = True      # require URL in findings
    min_mentions_to_trust: int = 1  # entity seen in N sources

    def estimate_cost_per_call(self) -> float:
        """Rough cost estimate in USD per call."""
        costs = {
            "claude-sonnet-4-5-20250929": 0.015,
            "claude-haiku-4-5-20251001": 0.003,
        }
        return costs.get(self.model, 0.02)


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """You are a research assistant helping an epistemic framework 
gather structured information about an academic topic.

For each search query you receive, use the web_search tool to find relevant 
results, then return a JSON array of findings.

CRITICAL RULES:
1. Return ONLY a valid JSON array, no other text.
2. Each finding must have a real URL from the search results.
3. Do NOT invent or hallucinate any information.
4. If a search returns no useful results, return an empty array: []
5. Extract ALL scholar names mentioned in each source.
6. Identify the theory or position supported, if any.
7. Classify each entity as: scholar, institution, historical_figure, 
   ancient_source, site, or unknown.

JSON format for each finding:
{
  "source": "Title or description of the source",
  "url": "https://...",
  "language": "en",
  "author": "Last name of primary author, or empty string",
  "institution": "Author's institution, or empty string",
  "theory_supported": "Brief description of theory/position, or empty string",
  "source_type": "peer_reviewed|journalistic|institutional|encyclopedic|blog",
  "year": 2024,
  "entities_mentioned": [
    {"name": "Scholar Name", "type": "scholar"},
    {"name": "Place Name", "type": "site"},
    {"name": "Historical Person", "type": "historical_figure"}
  ]
}
"""


# ============================================================
# CONNECTOR
# ============================================================

class APIConnector:
    """
    Handles communication with Claude API.
    Converts Epistemix SearchQuery objects to API calls,
    and API responses to Finding objects.
    """

    def __init__(self, config: ConnectorConfig | None = None):
        self.config = config or ConnectorConfig()
        self.calls_made = 0
        self.calls_this_cycle = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.errors: list[str] = []
        self.query_results: list[QueryResult] = []

        # Initialize client
        self.client = None
        if anthropic is not None:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                self.client = anthropic.Anthropic(api_key=api_key)

    @property
    def is_connected(self) -> bool:
        return self.client is not None

    @property
    def budget_remaining(self) -> int:
        return self.config.total_budget - self.calls_made

    @property
    def estimated_cost(self) -> float:
        return self.calls_made * self.config.estimate_cost_per_call()

    def reset_cycle_counter(self):
        self.calls_this_cycle = 0

    def execute_query(
        self, query: SearchQuery
    ) -> tuple[list[Finding], QueryResult]:
        """
        Execute a single search query via Claude API.
        Returns parsed findings and a QueryResult for
        the empty-query analyzer.
        """
        if not self.is_connected:
            return self._simulate_empty(query)

        if self.calls_made >= self.config.total_budget:
            self.errors.append(
                f"Total budget exhausted ({self.config.total_budget})"
            )
            return self._simulate_empty(query)

        if self.calls_this_cycle >= self.config.budget_per_cycle:
            self.errors.append(
                f"Cycle budget exhausted ({self.config.budget_per_cycle})"
            )
            return self._simulate_empty(query)

        # Build the user message
        user_msg = self._build_user_message(query)

        # Call the API
        findings = []
        n_results = 0

        for attempt in range(self.config.max_retries):
            try:
                response = self.client.messages.create(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    system=SYSTEM_PROMPT,
                    tools=[{
                        "type": "web_search_20250305",
                        "name": "web_search",
                    }],
                    messages=[{"role": "user", "content": user_msg}],
                )

                self.calls_made += 1
                self.calls_this_cycle += 1
                self.total_input_tokens += response.usage.input_tokens
                self.total_output_tokens += response.usage.output_tokens

                # Extract text content from response
                text_content = self._extract_text(response)

                # Parse JSON findings
                findings = self._parse_findings(
                    text_content, query
                )
                n_results = len(findings)

                # Delay between calls
                time.sleep(self.config.delay_between_calls)
                break

            except Exception as e:
                self.errors.append(
                    f"API error (attempt {attempt+1}): {e}"
                )
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)  # exponential backoff
                else:
                    return self._simulate_empty(query)

        # Record query result for empty-query analyzer
        qr = QueryResult(
            query=query,
            n_results=n_results,
            useful_results=len([
                f for f in findings if f.author or f.theory_supported
            ]),
        )
        self.query_results.append(qr)

        query.executed = True

        return findings, qr

    def execute_batch(
        self, queries: list[SearchQuery],
        max_queries: int | None = None,
    ) -> tuple[list[Finding], list[QueryResult]]:
        """
        Execute multiple queries, respecting budget limits.
        Prioritizes higher-severity queries first.
        """
        # Sort by priority (highest first)
        sorted_queries = sorted(
            queries,
            key=lambda q: q.priority.value,
            reverse=True,
        )

        limit = max_queries or self.config.budget_per_cycle
        to_execute = sorted_queries[:limit]

        all_findings = []
        all_results = []

        for query in to_execute:
            if self.budget_remaining <= 0:
                break

            findings, qr = self.execute_query(query)
            all_findings.extend(findings)
            all_results.append(qr)

        return all_findings, all_results

    # ── Internal helpers ──

    def _build_user_message(self, query: SearchQuery) -> str:
        """Build the user message for the API call."""
        return (
            f"Search for: {query.query}\n"
            f"Language: {query.language}\n"
            f"Context: {query.rationale}\n\n"
            f"Use web_search to find relevant academic and "
            f"journalistic sources, then return results as "
            f"a JSON array of findings."
        )

    def _extract_text(self, response) -> str:
        """Extract text content from API response."""
        parts = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts)

    def _parse_findings(
        self, text: str, query: SearchQuery
    ) -> list[Finding]:
        """Parse JSON response into Finding objects."""
        # Try to extract JSON from response
        json_str = self._extract_json(text)
        if not json_str:
            return []

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            self.errors.append(
                f"JSON parse error for query: {query.query}"
            )
            return []

        if not isinstance(data, list):
            data = [data]

        findings = []
        for item in data:
            if not isinstance(item, dict):
                continue

            # Extract entity names as flat list
            entities = []
            raw_entities = item.get("entities_mentioned", [])
            for e in raw_entities:
                if isinstance(e, dict):
                    entities.append(e.get("name", ""))
                elif isinstance(e, str):
                    entities.append(e)

            # Filter empty strings
            entities = [e for e in entities if e]

            # Validate: must have source
            source = item.get("source", "")
            if not source:
                continue

            # Optional URL validation
            url = item.get("url", "")
            if self.config.verify_urls and not url:
                # Still accept but mark as unverified
                source = f"[unverified] {source}"

            finding = Finding(
                source=source,
                language=item.get("language", query.language),
                author=item.get("author", ""),
                institution=item.get("institution", ""),
                theory_supported=item.get(
                    "theory_supported", ""
                ),
                source_type=item.get("source_type", ""),
                year=item.get("year", 0),
                entities_mentioned=entities,
                search_query_used=query.query,
            )
            findings.append(finding)

        return findings

    def _extract_json(self, text: str) -> str | None:
        """
        Extract JSON array from text that may contain
        markdown code blocks or other wrapping.
        """
        # Try raw parse first
        stripped = text.strip()
        if stripped.startswith("["):
            return stripped

        # Try extracting from code block
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            return text[start:end].strip()

        if "```" in text:
            start = text.index("```") + 3
            end = text.index("```", start)
            candidate = text[start:end].strip()
            if candidate.startswith("["):
                return candidate

        # Try finding array brackets
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]

        return None

    def _simulate_empty(
        self, query: SearchQuery
    ) -> tuple[list[Finding], QueryResult]:
        """Return empty results when API is unavailable."""
        qr = QueryResult(
            query=query, n_results=0, useful_results=0
        )
        self.query_results.append(qr)
        return [], qr

    def status(self) -> str:
        """Human-readable status summary."""
        lines = [
            f"Connected: {'yes' if self.is_connected else 'NO'}",
            f"Model: {self.config.model}",
            f"Calls made: {self.calls_made}/{self.config.total_budget}",
            f"This cycle: {self.calls_this_cycle}/{self.config.budget_per_cycle}",
            f"Tokens: {self.total_input_tokens} in, "
            f"{self.total_output_tokens} out",
            f"Est. cost: ${self.estimated_cost:.2f}",
            f"Errors: {len(self.errors)}",
        ]
        if self.errors:
            for e in self.errors[-3:]:
                lines.append(f"  ! {e}")
        return "\n".join(lines)
