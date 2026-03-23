"""Shared API-mode detection helpers.

These helpers keep custom endpoint routing consistent across the main agent,
CLI/runtime provider resolution, and auxiliary clients.
"""

from __future__ import annotations

from typing import Optional


CHAT_COMPLETIONS_API_MODE = "chat_completions"
RESPONSES_API_MODE = "codex_responses"
ANTHROPIC_MESSAGES_API_MODE = "anthropic_messages"


def normalize_base_url(base_url: Optional[str]) -> str:
    """Return a trimmed base URL without a trailing slash."""
    return str(base_url or "").strip().rstrip("/")


def is_direct_openai_url(base_url: Optional[str]) -> bool:
    """Return True when a base URL targets OpenAI's native API."""
    normalized = normalize_base_url(base_url).lower()
    return "api.openai.com" in normalized and "openrouter" not in normalized


def is_anthropic_compatible_base_url(base_url: Optional[str]) -> bool:
    """Return True for native or Anthropic-compatible custom endpoints."""
    normalized = normalize_base_url(base_url).lower()
    if not normalized:
        return False
    if "api.anthropic.com" in normalized:
        return True
    return normalized.endswith("/anthropic") or "/anthropic/" in normalized


def is_openai_compatible_v1_base_url(base_url: Optional[str]) -> bool:
    """Return True when the URL clearly targets an OpenAI-compatible /v1 root."""
    normalized = normalize_base_url(base_url).lower()
    return normalized.endswith("/v1") or "/v1/" in normalized


def detect_custom_api_mode(base_url: Optional[str]) -> Optional[str]:
    """Infer the API mode for custom endpoints from their base URL.

    Heuristic:
    - URLs containing an Anthropic-compatible path use Messages API
    - Native api.openai.com continues to use the Responses API
    - Explicit /responses paths use the Responses API
    - URLs rooted at /v1 use OpenAI-compatible chat completions
    - Other custom roots default to the Responses API
    """
    normalized = normalize_base_url(base_url).lower()
    if not normalized:
        return None

    if is_anthropic_compatible_base_url(normalized):
        return ANTHROPIC_MESSAGES_API_MODE
    if is_direct_openai_url(normalized):
        return RESPONSES_API_MODE
    if normalized.endswith("/responses") or "/responses/" in normalized:
        return RESPONSES_API_MODE
    if is_openai_compatible_v1_base_url(normalized):
        return CHAT_COMPLETIONS_API_MODE
    return RESPONSES_API_MODE
