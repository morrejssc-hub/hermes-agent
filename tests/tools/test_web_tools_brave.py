"""Tests for Brave Search web backend integration."""

import asyncio
import json
import os
from unittest.mock import MagicMock, patch

import pytest


class TestBraveRequest:
    def test_raises_without_api_key(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BRAVE_SEARCH_API_KEY", None)
            os.environ.pop("BRAVE_API_KEY", None)
            from tools.web_tools import _brave_request
            with pytest.raises(ValueError, match="BRAVE_SEARCH_API_KEY"):
                _brave_request("test", 3)

    def test_gets_with_subscription_header(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"web": {"results": []}}
        mock_response.raise_for_status = MagicMock()

        with patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "brave-test-key"}):
            with patch("tools.web_tools.httpx.get", return_value=mock_response) as mock_get:
                from tools.web_tools import _brave_request
                result = _brave_request("hello", 7)

                assert result == {"web": {"results": []}}
                mock_get.assert_called_once()
                call = mock_get.call_args
                assert call.args[0] == "https://api.search.brave.com/res/v1/web/search"
                assert call.kwargs["headers"]["X-Subscription-Token"] == "brave-test-key"
                assert call.kwargs["params"]["q"] == "hello"
                assert call.kwargs["params"]["count"] == 7

    def test_uses_official_alias_env_var(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"web": {"results": []}}
        mock_response.raise_for_status = MagicMock()

        with patch.dict(os.environ, {"BRAVE_API_KEY": "brave-docs-key"}):
            with patch("tools.web_tools.httpx.get", return_value=mock_response) as mock_get:
                from tools.web_tools import _brave_request
                _brave_request("hello", 3)
                assert mock_get.call_args.kwargs["headers"]["X-Subscription-Token"] == "brave-docs-key"


class TestNormalizeBraveSearchResults:
    def test_basic_normalization(self):
        from tools.web_tools import _normalize_brave_search_results

        raw = {
            "web": {
                "results": [
                    {
                        "title": "Python Docs",
                        "url": "https://docs.python.org",
                        "description": "Official documentation",
                    },
                    {
                        "title": "Tutorial",
                        "url": "https://example.com/tutorial",
                        "extra_snippets": ["Snippet one.", "Snippet two."],
                    },
                ]
            }
        }
        result = _normalize_brave_search_results(raw)
        web = result["data"]["web"]
        assert result["success"] is True
        assert len(web) == 2
        assert web[0]["description"] == "Official documentation"
        assert web[1]["description"] == "Snippet one. Snippet two."
        assert web[1]["position"] == 2


class TestWebSearchBrave:
    def test_search_dispatches_to_brave(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {"title": "Result", "url": "https://r.com", "description": "desc"}
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("tools.web_tools._get_backend", return_value="brave"), \
             patch.dict(os.environ, {"BRAVE_SEARCH_API_KEY": "brave-test"}), \
             patch("tools.web_tools.httpx.get", return_value=mock_response), \
             patch("tools.interrupt.is_interrupted", return_value=False):
            from tools.web_tools import web_search_tool
            result = json.loads(web_search_tool("test query", limit=3))
            assert result["success"] is True
            assert len(result["data"]["web"]) == 1
            assert result["data"]["web"][0]["title"] == "Result"


class TestWebExtractBrave:
    def test_extract_returns_explicit_unsupported_error(self):
        with patch("tools.web_tools._get_backend", return_value="brave"):
            from tools.web_tools import web_extract_tool
            result = json.loads(asyncio.get_event_loop().run_until_complete(
                web_extract_tool(["https://example.com"], use_llm_processing=False)
            ))
            assert result["success"] is False
            assert "not supported by the Brave Search backend" in result["error"]


class TestWebCrawlBrave:
    def test_crawl_returns_explicit_unsupported_error(self):
        with patch("tools.web_tools._get_backend", return_value="brave"):
            from tools.web_tools import web_crawl_tool
            result = json.loads(asyncio.get_event_loop().run_until_complete(
                web_crawl_tool("https://example.com", use_llm_processing=False)
            ))
            assert result["success"] is False
            assert "not supported by the Brave Search backend" in result["error"]
