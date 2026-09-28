"""DealMind API."""
from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app import db
from app.agents import briefing, coach, extractor, learning
from app.agents.extractor import extraction_of
from app.config import ROOT, settings
from app.llm.client import llm
from app.memory.banks import deal_bank, playbook_bank, rep_bank
from app.memory.service import memory
from app.models.schemas import (AskRequest, CloseRequest, CoachRequest, DealCreate, InteractionCreate,
                                OutcomeRequest)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    await memory.start()
    yield
    await llm.aclose()
    await memory.aclose()


app = FastAPI(title="DealMind", version="1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _deal_or_404(deal_id: str) -> dict:
    deal = db.get_deal(deal_id)
    if not deal:
        raise HTTPException(404, "Deal not found")
    return deal


def _health_score(deal_id: str) -> int | None:
    cached = briefing.cached_brief(deal_id, True)
    return cached["brief"]["deal_health"] if cached else None


# ---------------------------------------------------------------- meta

@app.get("/api/health")
async def health() -> dict:
    return {"memory": memory.status, "llm": {"configured": llm.configured, "model": settings.llm_model},
            "pending_retains": (db.row("SELECT COUNT(*) n FROM pending_retains") or {"n": 0})["n"]}


# ---------------------------------------------------------------- deals

@app.get("/api/deals")
async def list_deals() -> list[dict]:
    deals = db.rows("SELECT * FROM deals ORDER BY status='open' DESC, COALESCE(next_meeting, closed_at) DESC")
    for d in deals:
        last = db.row("SELECT date, type FROM interactions WHERE deal_id=? ORDER BY date DESC LIMIT 1", (d["id"],))
        d["last_touch"] = last["date"] if last else None
        d["interaction_count"] = (db.row("SELECT COUNT(*) n FROM interactions WHERE deal_id=?", (d["id"],)) or {})["n"]
        d["health"] = _health_score(d["id"])
        d["stakeholder_count"] = len(db.stakeholders_for(d["id"]))
    return deals


@app.post("/api/deals")
async def create_deal(body: DealCreate) -> dict:
    deal_id = db.new_id("deal")
    db.execute(
        "INSERT INTO deals (id, name, company, industry, amount, stage, primary_competitor, next_meeting, owner, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (deal_id, body.name, body.company, body.industry, body.amount, body.stage, body.primary_competitor,
         body.next_meeting, settings.rep_id, db.now_iso()),
    )
    await memory.ensure_bank(deal_bank(deal_id))
    return _deal_or_404(deal_id)


@app.get("/api/deals/{deal_id}")
async def get_deal(deal_id: str) -> dict:
    deal = _deal_or_404(deal_id)
    interactions = db.rows("SELECT * FROM interactions WHERE deal_id=? ORDER BY date DESC", (deal_id,))
    for i in interactions:
        i["participants"] = json.loads(i["participants"] or "[]")
        i["extraction"] = extraction_of(i)
    return {
        **deal,
        "stakeholders": db.stakeholders_for(deal_id),
        "interactions": interactions,
        "commitments": db.rows("SELECT * FROM commitments WHERE deal_id=? ORDER BY due_date", (deal_id,)),
        "suggestions": coach.recent_suggestions(deal_id),
        "postmortem": db.row("SELECT * FROM postmortems WHERE deal_id=?", (deal_id,)),
        "brief": briefing.cached_brief(deal_id, True),
        "brief_off": briefing.cached_brief(deal_id, False),
    }


@app.post("/api/deals/{deal_id}/interactions")
async def add_interaction(deal_id: str, body: InteractionCreate) -> dict:
    deal = _deal_or_404(deal_id)
    interaction = {
        "id": db.new_id("int"), "deal_id": deal_id, "type": body.type,
        "title": body.title or f"{body.type.title()} with {deal['company']}",
        "date": body.date or db.now_iso(), "participants": body.participants, "content": body.content,
    }
    db.execute(
        "INSERT INTO interactions (id, deal_id, type, title, date, participants, content) VALUES (?,?,?,?,?,?,?)",
        (interaction["id"], deal_id, interaction["type"], interaction["title"], interaction["date"],
         json.dumps(body.participants), body.content),
    )
    ex = await extractor.ingest(deal, interaction)
    if ex.partial:
        raise HTTPException(502, f"Extraction degraded: {ex.error}")
    return {"interaction_id": interaction["id"], "extraction": ex.model_dump(),
            "memory_text": extractor.compose_memory(deal, interaction, ex)}


@app.post("/api/deals/{deal_id}/commitments/{cid}/toggle")
async def toggle_commitment(deal_id: str, cid: int) -> dict:
    deal = _deal_or_404(deal_id)
    c = db.row("SELECT * FROM commitments WHERE id=? AND deal_id=?", (cid, deal_id))
    if not c:
        raise HTTPException(404, "Commitment not found")
    done = 0 if c["done"] else 1
    db.execute("UPDATE commitments SET done=? WHERE id=?", (done, cid))
    if done:
        await memory.retain(deal_bank(deal_id), f"On {db.now_iso()[:10]}, the commitment \"{c['what']}\" "
                            f"({'Northwind' if c['owner'] == 'us' else deal['company']}, {c['who']}) was completed.",
                            context="commitment_update", document_id=f"commit-done-{cid}")
    return {"id": cid, "done": done}


@app.get("/api/deals/{deal_id}/brief")
async def brief(deal_id: str, memory_on: str = Query("on", alias="memory")) -> StreamingResponse:
    _deal_or_404(deal_id)
    use = memory_on != "off"

    async def events():
        try:
            async for ev in briefing.build_brief(deal_id, use):
                yield f"data: {json.dumps(ev, default=str)}\n\n"
        except Exception as exc:  # surface failures to the UI instead of a hung stream
            logging.exception("brief failed")
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/deals/{deal_id}/coach")
async def coach_endpoint(deal_id: str, body: CoachRequest) -> dict:
    _deal_or_404(deal_id)
    if not body.objection.strip():
        raise HTTPException(400, "Objection text is required")
    return await coach.coach(deal_id, body.objection.strip(), body.speaker)


@app.post("/api/suggestions/{suggestion_id}/outcome")
async def suggestion_outcome(suggestion_id: str, body: OutcomeRequest) -> dict:
    try:
        return await learning.outcome_for_suggestion(suggestion_id, body.worked, body.note)
    except KeyError:
        raise HTTPException(404, "Suggestion not found")


@app.post("/api/deals/{deal_id}/close")
async def close(deal_id: str, body: CloseRequest) -> dict:
    _deal_or_404(deal_id)
    return await learning.close_deal(deal_id, body.result, body.reason)


@app.get("/api/deals/{deal_id}/memories")
async def deal_memories(deal_id: str, q: str = "Everything important about this deal") -> dict:
    _deal_or_404(deal_id)
    mems = await memory.recall(deal_bank(deal_id), q, budget="mid", max_tokens=6000, label_prefix="M")
    return {"bank": deal_bank(deal_id).bank_id, "query": q, "memories": [m.as_dict() for m in mems]}


# ---------------------------------------------------------------- playbook

@app.get("/api/playbook/stats")
async def stats() -> dict:
    return learning.playbook_stats()


@app.post("/api/playbook/ask")
async def ask(body: AskRequest) -> dict:
    return await learning.ask_playbook(body.question)


@app.get("/api/playbook/memories")
async def playbook_memories(q: str = "What have we learned about handling objections?") -> dict:
    mems = await memory.recall(playbook_bank(), q, budget="mid", max_tokens=6000, label_prefix="P")
    return {"bank": playbook_bank().bank_id, "query": q, "memories": [m.as_dict() for m in mems]}


@app.get("/api/banks")
async def banks() -> dict:
    return {"playbook": playbook_bank().bank_id, "rep": rep_bank().bank_id}


# ---------------------------------------------------------------- frontend (production build)

_dist = ROOT / "frontend" / "dist"
if _dist.exists():
    app.mount("/assets", StaticFiles(directory=_dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str) -> FileResponse:
        target = _dist / path
        return FileResponse(target if path and target.is_file() else _dist / "index.html")
