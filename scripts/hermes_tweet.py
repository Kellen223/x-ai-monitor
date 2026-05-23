"""
Hermes Tweet / Xquik optional read backend.

Keeps x-ai-monitor's default Jina Reader workflow intact while offering an
authenticated X read route for accounts that need more structured tweet data.
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote, urlencode

import requests

DEFAULT_BASE_URL = "https://xquik.com"
BACKEND_ALIASES = {"hermes-tweet", "hermes_tweet", "xquik"}


class HermesTweetError(Exception):
    """Raised when Hermes Tweet cannot complete a read request."""


def normalize_backend(value: str | None) -> str:
    """Normalize backend aliases."""
    normalized = (value or "").strip().lower().replace("_", "-")
    if normalized in BACKEND_ALIASES:
        return "hermes-tweet"
    if normalized in {"", "jina", "default", "native"}:
        return "jina"
    return normalized


def backend_enabled(value: str | None = None) -> bool:
    """Return true when Hermes Tweet should be used."""
    selected = value or os.environ.get("X_MONITOR_BACKEND") or os.environ.get("TWITTER_BACKEND")
    return normalize_backend(selected) == "hermes-tweet"


def get_base_url() -> str:
    """Read Xquik base URL from environment."""
    return os.environ.get("XQUIK_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def get_api_key() -> str:
    """Read Xquik API key from environment."""
    return os.environ.get("XQUIK_API_KEY") or os.environ.get("HERMES_TWEET_API_KEY") or ""


def build_headers(api_key: str) -> dict[str, str]:
    """Build the authentication headers accepted by Xquik."""
    if not api_key:
        raise HermesTweetError("XQUIK_API_KEY is required when X_MONITOR_BACKEND=hermes-tweet.")
    headers = {"User-Agent": "x-ai-monitor/hermes-tweet"}
    if api_key.startswith("xq_"):
        headers["x-api-key"] = api_key
    else:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def build_url(username: str, *, limit: int, base_url: str | None = None) -> str:
    """Build a user timeline URL."""
    safe_username = quote(username.strip().lstrip("@"))
    query = urlencode({"limit": limit})
    return f"{(base_url or get_base_url()).rstrip('/')}/api/v1/x/users/{safe_username}/tweets?{query}"


def extract_items(payload: Any) -> list[dict[str, Any]]:
    """Extract tweet rows from common response envelopes."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("tweets", "items", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    data = payload.get("data")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return extract_items(data)
    return []


def first_present(mapping: dict[str, Any], names: tuple[str, ...], default: Any = "") -> Any:
    """Return the first present value in a mapping."""
    for name in names:
        value = mapping.get(name)
        if value not in (None, ""):
            return value
    return default


def normalize_tweet(tweet: dict[str, Any]) -> dict[str, str]:
    """Normalize a tweet into monitor.py's parser-friendly shape."""
    legacy = tweet.get("legacy") if isinstance(tweet.get("legacy"), dict) else {}
    text = first_present(tweet, ("text", "full_text", "content"), legacy.get("full_text") or legacy.get("text", ""))
    tweet_id = str(first_present(tweet, ("id", "id_str", "tweet_id", "rest_id"), legacy.get("id_str", "")))
    created_at = str(first_present(tweet, ("created_at", "createdAt"), legacy.get("created_at", "")))
    return {
        "raw_content": str(text).strip(),
        "date_hint": created_at,
        "id": tweet_id,
        "url": str(tweet.get("url") or ""),
    }


def fetch_account_tweets(
    username: str,
    *,
    limit: int,
    api_key: str | None = None,
    base_url: str | None = None,
    session: Any = requests,
) -> list[dict[str, str]]:
    """Fetch and normalize tweets for one account."""
    resolved_key = api_key or get_api_key()
    url = build_url(username, limit=limit, base_url=base_url)
    response = session.get(url, headers=build_headers(resolved_key), timeout=30)
    response.raise_for_status()
    payload = response.json()
    tweets = []
    for item in extract_items(payload):
        normalized = normalize_tweet(item)
        if normalized.get("raw_content"):
            tweets.append(normalized)
    return tweets
