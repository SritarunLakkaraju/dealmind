import json

import pytest

from app.llm import client as client_mod
from app.llm.client import LLMClient, _clean
from app.models.schemas import Brief


def test_clean_strips_think_and_fences():
    raw = '<think>hmm</think>\n```json\n{"headline": "x"}\n```'
    assert json.loads(_clean(raw)) == {"headline": "x"}


@pytest.mark.asyncio
async def test_repair_then_fallback_then_degraded(monkeypatch):
    calls = []

    async def fake_chat(self, messages, model=None, **kw):
        calls.append(model)
        if len(calls) == 1:
            return "not json at all"
        if len(calls) == 2:
            return '{"deal_health": "abc", "headline": "ok"}'  # repaired answer
        raise client_mod.LLMError("down")

    monkeypatch.setattr(LLMClient, "chat", fake_chat)
    out = await LLMClient().complete_json("sys", "user", Brief)
    # repair answer validates; unparseable health falls back to 50
    assert out.deal_health == 50 and not out.partial
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_fully_degraded(monkeypatch):
    async def fake_chat(self, messages, model=None, **kw):
        return "{broken"

    monkeypatch.setattr(LLMClient, "chat", fake_chat)
    out = await LLMClient().complete_json("sys", "user", Brief)
    assert out.partial and out.error
