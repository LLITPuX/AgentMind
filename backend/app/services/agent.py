"""Agent service using Google Generative Language REST API (async)."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping

import httpx

from ..core.config import settings


GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


def _build_headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


async def _post_json(url: str, payload: Mapping[str, object]) -> Dict[str, Any]:
    if not settings.google_api_key:
        # Fallback: no external call when key is missing
        return {}

    timeout = httpx.Timeout(15.0, connect=5.0)
    params = {"key": settings.google_api_key}

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, params=params, headers=_build_headers(), json=payload)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]


async def run_conversation(messages: List[Mapping[str, str]]) -> str:
    """Call Gemini chat model with full message history.

    messages: list of dicts with keys: role ('user'|'model'), parts: [{'text': str}] is the API shape
    """

    url = f"{GEMINI_BASE_URL}/models/{settings.gemini_chat_model}:generateContent"
    payload: Dict[str, object] = {"contents": messages}

    data = await _post_json(url, payload)
    if not data:
        # Simple local heuristic response when no API key is configured
        last_user = next((m for m in reversed(messages) if m.get("role") == "user"), None)
        base = str((last_user or {}).get("parts", [{}])[0].get("text", ""))
        return ("Echo: " + base)[:1024]
    # Extract text
    try:
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return str(parts[0].get("text", ""))
    except Exception:  # noqa: BLE001
        pass
    return ""


async def run_analysis(content_text: str, system_prompt: str, json_schema: Mapping[str, object]) -> Mapping[str, object]:
    """Call Gemini analysis model expecting JSON output per provided schema."""

    url = f"{GEMINI_BASE_URL}/models/{settings.gemini_analysis_model}:generateContent"
    payload: Dict[str, object] = {
        "contents": [{"role": "user", "parts": [{"text": content_text}]}],
        "generation_config": {
            "response_mime_type": "application/json",
            "response_schema": json_schema,
        },
    }
    if system_prompt:
        payload["system_instruction"] = {"role": "system", "parts": [{"text": system_prompt}]}

    data = await _post_json(url, payload)
    if not data:
        # Fallback: naive sentiment and structure when no API key
        sentiment = "positive" if any(w in content_text.lower() for w in ["good", "great", ":)", "thanks"]) else (
            "negative" if any(w in content_text.lower() for w in ["bad", "terrible", ":(", "fuck"]) else "neutral"
        )
        return {"sentiment": sentiment}
    # Parse first candidate text as JSON
    try:
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                import json

                return json.loads(str(parts[0].get("text", "{}")))
    except Exception:  # noqa: BLE001
        pass
    return {}


