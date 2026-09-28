"""LLM client: OpenAI-compatible chat (Groq by default) with robust JSON output.

Function calling on the recommended Groq models is unreliable, so every structured call goes
through `complete_json`: JSON mode -> Pydantic validation -> one repair call -> fallback model ->
schema-valid degraded object.
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
import re
import time
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.config import settings

log = logging.getLogger("dealmind.llm")
T = TypeVar("T", bound=BaseModel)

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class LLMError(RuntimeError):
    pass


def _clean(text: str) -> str:
    """Strip reasoning blocks and markdown fences, then isolate the outermost JSON object."""
    text = _THINK_RE.sub("", text or "").strip()
    text = _FENCE_RE.sub("", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return text[start : end + 1]
    return text


class LLMClient:
    def __init__(self) -> None:
        self._http = httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0))

    @property
    def configured(self) -> bool:
        return bool(settings.llm_api_key)

    async def chat(
        self,
        messages: list[dict],
        *,
        model: str | None = None,
        json_mode: bool = False,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Single chat completion with 429/5xx backoff. Returns the message text."""
        if not self.configured:
            raise LLMError("GROQ_API_KEY is not set")
        model = model or settings.llm_model
        payload: dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {settings.llm_api_key}"}

        for attempt in range(8):
            started = time.perf_counter()
            resp = await self._http.post(
                f"{settings.llm_base_url}/chat/completions", json=payload, headers=headers
            )
            if resp.status_code == 429 or resp.status_code >= 500:
                wait = min(30.0, (2**attempt) + random.random())
                retry_after = resp.headers.get("retry-after")
                if retry_after:
                    try:
                        wait = min(60.0, float(retry_after) + 0.5 + random.random())
                    except ValueError:
                        pass
                log.warning("LLM %s on %s, retrying in %.1fs", resp.status_code, model, wait)
                await asyncio.sleep(wait)
                continue
            if resp.status_code == 400 and json_mode and "json" in resp.text.lower():
                # Model rejected JSON mode or failed JSON validation server-side; retry without it.
                payload.pop("response_format", None)
                json_mode = False
                continue
            if resp.status_code >= 400:
                raise LLMError(f"{model} HTTP {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            usage = data.get("usage", {})
            log.info(
                "LLM %s ok in %.2fs (in=%s out=%s)",
                model,
                time.perf_counter() - started,
                usage.get("prompt_tokens"),
                usage.get("completion_tokens"),
            )
            return data["choices"][0]["message"].get("content") or ""
        raise LLMError(f"{model}: exhausted retries")

    async def complete_text(self, system: str, user: str, **kw) -> str:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        try:
            return _THINK_RE.sub("", await self.chat(messages, **kw)).strip()
        except LLMError:
            return _THINK_RE.sub(
                "", await self.chat(messages, model=settings.llm_fallback_model, **kw)
            ).strip()

    async def complete_json(self, system: str, user: str, schema: type[T], **kw) -> T:
        """Return a validated `schema` instance; never raises on bad model output."""
        schema_hint = json.dumps(schema.model_json_schema(), separators=(",", ":"))
        sys_prompt = (
            f"{system}\n\nRespond with a single JSON object that validates against this JSON "
            f"schema. No prose, no markdown.\nSCHEMA: {schema_hint}"
        )
        base = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user}]

        last_error = "unknown"
        for model in (settings.llm_model, settings.llm_fallback_model):
            messages = list(base)
            for attempt in range(2):  # first try, then one repair
                try:
                    raw = await self.chat(messages, model=model, json_mode=True, **kw)
                except LLMError as exc:
                    last_error = str(exc)
                    break  # go to fallback model
                try:
                    return schema.model_validate(json.loads(_clean(raw)))
                except (json.JSONDecodeError, ValidationError) as exc:
                    last_error = str(exc)[:800]
                    log.warning("JSON invalid from %s (attempt %d): %s", model, attempt, last_error)
                    messages = base + [
                        {"role": "assistant", "content": raw[:6000]},
                        {
                            "role": "user",
                            "content": "Your previous output was invalid:\n"
                            f"{last_error}\nReturn the corrected JSON object only.",
                        },
                    ]
        log.error("complete_json degraded for %s: %s", schema.__name__, last_error)
        return schema.model_validate({"partial": True, "error": last_error[:300]})

    async def aclose(self) -> None:
        await self._http.aclose()


llm = LLMClient()
