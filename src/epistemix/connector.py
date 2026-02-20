"""API connector — abstracts the AI provider.

BaseConnector (ABC) → MockConnector (for tests) and ClaudeConnector (for production).
The connector abstraction means you can develop and test with zero API cost,
then flip one env var to go live.
"""

from __future__ import annotations

import json
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConnectorResponse:
    """Standardized response from any connector."""
    text: str
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    raw: Any = None


class BaseConnector(ABC):
    """Abstract base class for AI connectors."""

    @abstractmethod
    def query(self, prompt: str, system: str = "") -> ConnectorResponse:
        """Send a query and return a response."""

    @abstractmethod
    def search(self, query: str) -> ConnectorResponse:
        """Perform a web search query and return results."""

    @property
    @abstractmethod
    def total_cost(self) -> float:
        """Total cost of all API calls so far."""


class MockConnector(BaseConnector):
    """Pattern-matched canned responses for testing.

    Matches query text against registered patterns (case-insensitive substring match).
    Falls back to a default response if no pattern matches.
    Logs all calls for test assertions.
    """

    def __init__(self, responses: dict[str, str] | None = None) -> None:
        self._responses: dict[str, str] = responses or {}
        self._default_response: str = (
            "No specific information found for this query."
        )
        self._call_log: list[dict[str, str]] = []
        self._search_log: list[str] = []

    def register_response(self, pattern: str, response: str) -> None:
        """Register a pattern → response mapping."""
        self._responses[pattern.lower()] = response

    def register_responses(self, responses: dict[str, str]) -> None:
        """Register multiple pattern → response mappings."""
        for pattern, response in responses.items():
            self.register_response(pattern, response)

    def set_default_response(self, response: str) -> None:
        self._default_response = response

    def query(self, prompt: str, system: str = "") -> ConnectorResponse:
        prompt_lower = prompt.lower()
        self._call_log.append({"prompt": prompt, "system": system})

        # Try pattern matching
        for pattern, response in self._responses.items():
            if pattern in prompt_lower:
                return ConnectorResponse(text=response, model="mock")

        return ConnectorResponse(text=self._default_response, model="mock")

    def search(self, query: str) -> ConnectorResponse:
        self._search_log.append(query)
        query_lower = query.lower()

        for pattern, response in self._responses.items():
            if pattern in query_lower:
                return ConnectorResponse(text=response, model="mock-search")

        return ConnectorResponse(text=self._default_response, model="mock-search")

    @property
    def total_cost(self) -> float:
        return 0.0

    @property
    def call_count(self) -> int:
        return len(self._call_log)

    @property
    def search_count(self) -> int:
        return len(self._search_log)

    @property
    def call_log(self) -> list[dict[str, str]]:
        return self._call_log

    @property
    def search_log(self) -> list[str]:
        return self._search_log


class ClaudeConnector(BaseConnector):
    """Production connector using the Anthropic API.

    Features:
    - Web search via tool use
    - Budget tracking (stop before exceeding budget)
    - Rate limiting with exponential backoff
    - Structured JSON parsing from responses
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
                "Install it with: pip install 'epistemix[live]'"
            )

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._max_budget = max_budget
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._call_count = 0

    def query(self, prompt: str, system: str = "") -> ConnectorResponse:
        if self.total_cost >= self._max_budget:
            return ConnectorResponse(
                text="[BUDGET EXCEEDED — no more API calls allowed]",
                model=self._model,
            )

        messages = [{"role": "user", "content": prompt}]
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": 4096,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        response = self._call_with_retry(kwargs)
        self._call_count += 1
        return self._parse_response(response)

    def search(self, query: str) -> ConnectorResponse:
        if self.total_cost >= self._max_budget:
            return ConnectorResponse(
                text="[BUDGET EXCEEDED]",
                model=self._model,
            )

        prompt = (
            f"Search the web for: {query}\n\n"
            "Return a comprehensive summary of what you find, including "
            "names of researchers, institutions, theories, and publications."
        )
        messages = [{"role": "user", "content": prompt}]
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": 4096,
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
        return self._parse_response(response)

    def _call_with_retry(
        self, kwargs: dict[str, Any], max_retries: int = 3
    ) -> Any:
        """Call the API with exponential backoff on rate limit errors."""
        import anthropic

        for attempt in range(max_retries + 1):
            try:
                return self._client.messages.create(**kwargs)
            except anthropic.RateLimitError:
                if attempt == max_retries:
                    raise
                wait = 2 ** (attempt + 1)
                time.sleep(wait)
            except anthropic.APIStatusError as e:
                if e.status_code == 529 and attempt < max_retries:
                    wait = 2 ** (attempt + 1)
                    time.sleep(wait)
                else:
                    raise

    def _parse_response(self, response: Any) -> ConnectorResponse:
        """Extract text from an Anthropic API response."""
        text_parts = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)

        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
        self._total_input_tokens += response.usage.input_tokens
        self._total_output_tokens += response.usage.output_tokens

        return ConnectorResponse(
            text="\n".join(text_parts),
            model=response.model,
            usage=usage,
            raw=response,
        )

    @property
    def total_cost(self) -> float:
        # Approximate costs per 1K tokens (Claude Sonnet)
        input_cost = (self._total_input_tokens / 1000) * 0.003
        output_cost = (self._total_output_tokens / 1000) * 0.015
        return round(input_cost + output_cost, 4)

    @property
    def call_count(self) -> int:
        return self._call_count


def extract_json(text: str) -> dict[str, Any] | list[Any] | None:
    """Try to extract JSON from a text response.

    Looks for JSON blocks (```json ... ```) or bare JSON objects/arrays.
    """
    # Try ```json blocks first
    json_block = re.search(r"```json\s*\n(.*?)\n\s*```", text, re.DOTALL)
    if json_block:
        try:
            return json.loads(json_block.group(1))
        except json.JSONDecodeError:
            pass

    # Try bare JSON
    for pattern in [r"\{.*\}", r"\[.*\]"]:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                continue

    return None
