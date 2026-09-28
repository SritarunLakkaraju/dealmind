"""Briefing agent: recalls deal + playbook + rep memory, reflects on risk, writes a cited brief."""
from __future__ import annotations

import asyncio
import json
import time
from collections import Counter
from typing import AsyncIterator

from app import db
from app.agents.common import deal_header, format_memories, load_prompt
from app.llm.client import llm
from app.memory.banks import deal_bank, playbook_bank, rep_bank
from app.memory.service import Memory, memory
from app.models.schemas import Brief


def _objection_profile(deal_id: str) -> list[str]:
    """Most common objection categories in this deal, from stored extractions."""
    counts: Counter = Counter()
    for r in db.rows("SELECT extraction FROM interactions WHERE deal_id=? AND extraction IS NOT NULL", (deal_id,)):
        for o in json.loads(r["extraction"]).get("objections", []):
            counts[o.get("category", "other")] += 1
    return [c for c, _ in counts.most_common(3)]


def _validate(brief: Brief, known: set[str], memory_on: bool) -> Brief:
    """Drop citations the model invented; drop deal claims left with no evidence."""
    def clean(items: list, required: bool) -> list:
        kept = []
        for it in items:
            it.evidence_ids = [e for e in (x.strip("[] ") for x in it.evidence_ids) if e in known]
            if it.evidence_ids or not (required and memory_on):
                kept.append(it)
        return kept

    brief.key_risks = clean(brief.key_risks, True)
    brief.open_commitments = clean(brief.open_commitments, True)
    brief.stakeholder_notes = clean(brief.stakeholder_notes, True)
    brief.likely_objections = clean(brief.likely_objections, False)
    brief.pattern_alert_ids = [e for e in brief.pattern_alert_ids if e in known]
    if memory_on and brief.pattern_alert and not brief.pattern_alert_ids:
        brief.pattern_alert = None
    if not memory_on:
        brief.pattern_alert, brief.pattern_alert_ids = None, []
    return brief


async def build_brief(deal_id: str, use_memory: bool) -> AsyncIterator[dict]:
    """Yield progress events, then {"type": "brief", ...}. Designed to be streamed over SSE."""
    started = time.perf_counter()
    deal = db.get_deal(deal_id)
    if not deal:
        yield {"type": "error", "message": "Deal not found"}
        return

    deal_mems: list[Memory] = []
    play_mems: list[Memory] = []
    rep_mems: list[Memory] = []
    reflection_text, refl_mems = "", []

    if use_memory:
        categories = _objection_profile(deal_id) or ["price", "security", "competitor"]
        play_query = (
            f"Which tactics worked or failed for {', '.join(categories)} objections from "
            f"{deal.get('persona') or 'economic buyer'} stakeholders when competing against "
            f"{deal.get('primary_competitor') or 'competitors'} in {deal.get('industry') or 'B2B'} deals? "
            f"Include post-mortems of won and lost deals with similar patterns."
        )
        yield {"type": "step", "key": "recall", "label": "Recalling deal, playbook & rep memory"}
        deal_task = memory.recall(
            deal_bank(deal_id),
            "Open objections and unresolved concerns, each stakeholder's stance, pricing and budget history, "
            "competitor mentions, and commitments or promises made by either side with due dates",
            budget="high", max_tokens=3000, label_prefix="D", limit=30,
        )
        play_task = memory.recall(playbook_bank(), play_query, budget="mid", max_tokens=2500, label_prefix="P", limit=18)
        rep_task = memory.recall(rep_bank(), "How does the rep like briefs, and where do they need coaching?",
                                 budget="low", max_tokens=600, label_prefix="U", limit=4)
        refl_task = memory.reflect(
            deal_bank(deal_id),
            "What is the single biggest risk to this deal right now, and why? Cite who said what and when. "
            "Mention any promise we made that is overdue.",
            budget="mid",
        )
        deal_mems, play_mems, rep_mems, reflection = await asyncio.gather(deal_task, play_task, rep_task, refl_task)
        reflection_text = reflection.text
        refl_mems = reflection.based_on
        for i, m in enumerate(refl_mems, 1):
            m.label = f"R{i}"
        yield {
            "type": "step", "key": "recalled",
            "label": f"Recalled {len(deal_mems)} deal facts · {len(play_mems)} playbook lessons · reflected on risk",
            "counts": {"deal": len(deal_mems), "playbook": len(play_mems), "rep": len(rep_mems)},
        }
    else:
        yield {"type": "step", "key": "recall", "label": "Memory OFF — using deal fields only"}

    yield {"type": "step", "key": "compose", "label": "Writing the brief"}
    user = (
        f"DEAL: {deal_header(deal)}\n\n"
        f"DEAL_MEMORIES:\n{format_memories(deal_mems)}\n\n"
        f"PLAYBOOK_MEMORIES:\n{format_memories(play_mems)}\n\n"
        f"RISK_REFLECTION:\n{reflection_text or '(none)'}\n{format_memories(refl_mems, '')}\n\n"
        f"REP_PREFERENCES:\n{format_memories(rep_mems)}"
    )
    brief = await llm.complete_json(load_prompt("briefing"), user, Brief, temperature=0.2)

    citations = {m.label: m.as_dict() for m in deal_mems + play_mems + refl_mems + rep_mems}
    brief = _validate(brief, set(citations), use_memory)
    payload = {
        "deal_id": deal_id,
        "memory": use_memory,
        "brief": brief.model_dump(),
        "citations": citations,
        "reflection": reflection_text,
        "stats": {
            "deal_memories": len(deal_mems), "playbook_memories": len(play_mems),
            "seconds": round(time.perf_counter() - started, 1),
        },
        "generated_at": db.now_iso(),
    }
    db.execute(
        "INSERT OR REPLACE INTO briefs (deal_id, memory, payload, created_at) VALUES (?,?,?,?)",
        (deal_id, int(use_memory), json.dumps(payload), payload["generated_at"]),
    )
    yield {"type": "brief", **payload}


def cached_brief(deal_id: str, use_memory: bool) -> dict | None:
    r = db.row("SELECT payload FROM briefs WHERE deal_id=? AND memory=?", (deal_id, int(use_memory)))
    return json.loads(r["payload"]) if r else None
