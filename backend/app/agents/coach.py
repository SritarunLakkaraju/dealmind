"""Live objection coach: fast recall (budget=low) + one LLM call."""
from __future__ import annotations

import asyncio
import json
import time

from app import db
from app.agents.common import deal_header, format_memories, load_prompt
from app.llm.client import llm
from app.memory.banks import deal_bank, playbook_bank
from app.memory.service import memory
from app.models.schemas import CoachResponse

_background: set[asyncio.Task] = set()


async def coach(deal_id: str, objection: str, speaker: str = "") -> dict:
    started = time.perf_counter()
    deal = db.get_deal(deal_id)
    if not deal:
        raise KeyError(deal_id)

    deal_mems, play_mems = await asyncio.gather(
        memory.recall(deal_bank(deal_id), f"{speaker} {objection}".strip(), budget="low",
                      max_tokens=1500, label_prefix="D", limit=12),
        memory.recall(
            playbook_bank(),
            f"Tactics that worked or failed when a {speaker or deal.get('persona') or 'buyer'} said: "
            f"\"{objection}\" (competitor {deal.get('primary_competitor') or 'unknown'}, "
            f"{deal.get('industry') or 'B2B'})",
            budget="low", max_tokens=2000, label_prefix="P", limit=12,
        ),
    )
    known = sorted({r["tactic"] for r in db.rows("SELECT DISTINCT tactic FROM tactic_outcomes")})
    user = (
        f"KNOWN_TACTICS: {'; '.join(known) or '(none yet)'}\n"
        f"OBJECTION: \"{objection}\"\nSPEAKER: {speaker or 'unknown'}\nDEAL: {deal_header(deal)}\n\n"
        f"DEAL_MEMORIES:\n{format_memories(deal_mems)}\n\nPLAYBOOK_MEMORIES:\n{format_memories(play_mems)}"
    )
    resp = await llm.complete_json(load_prompt("coach"), user, CoachResponse, temperature=0.3, max_tokens=1500)
    citations = {m.label: m.as_dict() for m in deal_mems + play_mems}
    resp.evidence = [e for e in resp.evidence if e.memory_id.strip("[] ") in citations]
    for e in resp.evidence:
        e.memory_id = e.memory_id.strip("[] ")

    suggestion_id = db.new_id("sug")
    db.execute(
        "INSERT INTO suggestions (id, deal_id, objection, category, tactic, response, created_at) VALUES (?,?,?,?,?,?,?)",
        (suggestion_id, deal_id, objection, resp.objection_category, resp.tactic_name,
         resp.model_dump_json(), db.now_iso()),
    )
    # Log the suggestion into the playbook without blocking the rep.
    task = asyncio.create_task(memory.retain(
        playbook_bank(),
        f"On {db.now_iso()[:10]}, in the {deal['company']} deal ({deal.get('industry')}, competing against "
        f"{deal.get('primary_competitor') or 'unknown'}), {speaker or 'the prospect'} raised a "
        f"{resp.objection_category} objection: \"{objection}\". DealMind suggested the tactic "
        f"\"{resp.tactic_name}\". Outcome not yet known.",
        context="tactic_suggested", document_id=suggestion_id,
        metadata={"deal_id": deal_id, "category": resp.objection_category, "tactic": resp.tactic_name},
    ))
    _background.add(task)
    task.add_done_callback(_background.discard)

    return {
        "suggestion_id": suggestion_id,
        "response": resp.model_dump(),
        "citations": citations,
        "latency_ms": int((time.perf_counter() - started) * 1000),
    }


def recent_suggestions(deal_id: str, limit: int = 10) -> list[dict]:
    out = db.rows("SELECT * FROM suggestions WHERE deal_id=? ORDER BY created_at DESC LIMIT ?", (deal_id, limit))
    for s in out:
        s["response"] = json.loads(s["response"])
    return out
