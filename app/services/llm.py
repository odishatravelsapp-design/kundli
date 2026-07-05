"""Multi-provider LLM adapter — entirely optional.

Zero-cost default: no key configured -> generate() returns None and the app
falls back to the rule engine. Drop a key in .env and the matching provider
goes live without code changes. Anthropic uses the official SDK; the other
providers use plain HTTP so no extra dependencies are needed.
"""
from __future__ import annotations

import base64

import httpx

from ..config import get_settings

TIMEOUT = 90.0


async def generate(prompt: str, system: str | None = None,
                   image_jpeg_b64: str | None = None) -> str | None:
    s = get_settings()
    provider = s.resolve_provider()
    try:
        if provider == "anthropic":
            return await _anthropic(prompt, system, image_jpeg_b64)
        if provider == "openai":
            return await _openai(prompt, system, image_jpeg_b64)
        if provider == "gemini":
            return await _gemini(prompt, system, image_jpeg_b64)
        if provider == "ollama":
            return await _ollama(prompt, system)
    except Exception as e:  # degrade gracefully to rule engine
        return f"(AI narrative unavailable: {e})"
    return None


def provider_status() -> dict:
    s = get_settings()
    p = s.resolve_provider()
    return {"provider": p, "ai_enabled": p != "none"}


async def _anthropic(prompt: str, system: str | None,
                     image_b64: str | None) -> str:
    from anthropic import AsyncAnthropic
    s = get_settings()
    client = AsyncAnthropic(api_key=s.anthropic_api_key)
    content: list = []
    if image_b64:
        content.append({"type": "image", "source": {
            "type": "base64", "media_type": "image/jpeg", "data": image_b64}})
    content.append({"type": "text", "text": prompt})
    msg = await client.messages.create(
        model=s.anthropic_model,
        max_tokens=2048,
        system=system or "",
        messages=[{"role": "user", "content": content}],
    )
    return "".join(b.text for b in msg.content if b.type == "text")


async def _openai(prompt: str, system: str | None,
                  image_b64: str | None) -> str:
    s = get_settings()
    user_content: list | str = prompt
    if image_b64:
        user_content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {
                "url": f"data:image/jpeg;base64,{image_b64}"}},
        ]
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user_content})
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {s.openai_api_key}"},
            json={"model": s.openai_model, "messages": messages,
                  "max_tokens": 2048},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


async def _gemini(prompt: str, system: str | None,
                  image_b64: str | None) -> str:
    s = get_settings()
    parts: list = [{"text": prompt}]
    if image_b64:
        parts.append({"inline_data": {"mime_type": "image/jpeg",
                                      "data": image_b64}})
    body: dict = {"contents": [{"parts": parts}]}
    if system:
        body["system_instruction"] = {"parts": [{"text": system}]}
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{s.gemini_model}:generateContent?key={s.gemini_api_key}")
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.post(url, json=body)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]


async def _ollama(prompt: str, system: str | None) -> str:
    s = get_settings()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    async with httpx.AsyncClient(timeout=180.0) as c:
        r = await c.post(f"{s.ollama_base_url}/api/chat",
                         json={"model": s.ollama_model,
                               "messages": messages, "stream": False})
        r.raise_for_status()
        return r.json()["message"]["content"]
