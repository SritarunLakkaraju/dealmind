"""End-to-end pipeline on the local memory backend with a fake LLM."""
import json

import pytest

from app import db
from app.agents import briefing, coach, extractor, learning
from app.llm.client import llm
from app.memory.banks import deal_bank, playbook_bank
from app.memory.service import memory
from tests.fakes import fake_complete_json, fake_complete_text


@pytest.fixture(autouse=True)
async def setup(monkeypatch):
    monkeypatch.setattr(llm, "complete_json", fake_complete_json)
    monkeypatch.setattr(llm, "complete_text", fake_complete_text)
    db.init_db()
    for t in ("deals", "interactions", "commitments", "stakeholders", "suggestions", "tactic_outcomes", "briefs", "postmortems"):
        db.execute(f"DELETE FROM {t}")
    await memory.start()
    db.execute(
        "INSERT INTO deals (id, name, company, industry, amount, stage, status, primary_competitor, persona) "
        "VALUES ('d1','Tarang','Tarang Payments','Fintech',4500000,'Evaluation','open','Stratify','CFO')"
    )
    yield


def _interaction(i="i1", content="Priya: call me at +91 98765 43210 or priya@tarang.in"):
    db.execute("INSERT OR REPLACE INTO interactions (id, deal_id, type, title, date, participants, content) VALUES (?,?,?,?,?,?,?)",
               (i, "d1", "call", "CFO call", "2026-09-02T16:00:00+05:30", "[]", content))
    return {"id": i, "deal_id": "d1", "type": "call", "title": "CFO call", "date": "2026-09-02T16:00:00+05:30",
            "participants": ["Priya Menon (CFO)"], "content": content}


@pytest.mark.asyncio
async def test_ingest_writes_records_and_memory():
    deal = db.get_deal("d1")
    ex = await extractor.ingest(deal, _interaction())
    assert ex.objections[0].category == "price"  # normalized to lowercase
    assert ex.pricing[0].amount == 3200000
    assert db.stakeholders_for("d1")[0]["stance"] == "skeptic"
    assert db.rows("SELECT * FROM commitments")[0]["what"] == "Send SOC2 report"
    mems = await memory.recall(deal_bank("d1"), "Stratify price objection", label_prefix="D")
    assert mems and mems[0].label == "D1"
    assert any("Stratify" in m.text for m in mems)


def test_pii_scrubbed():
    assert "[redacted]" in extractor.scrub("mail priya@tarang.in or +91 98765 43210")
    assert "98765" not in extractor.scrub("+91 98765 43210")
    assert "98765" not in extractor.scrub("call 9876543210")
    assert extractor.scrub("due 2026-09-09, ₹45,00,000") == "due 2026-09-09, ₹45,00,000"


@pytest.mark.asyncio
async def test_reingest_is_idempotent():
    deal = db.get_deal("d1")
    await extractor.ingest(deal, _interaction())
    await extractor.ingest(deal, _interaction())
    n = db.row("SELECT COUNT(DISTINCT document_id) n FROM local_memories WHERE bank_id=?", (deal_bank("d1").bank_id,))["n"]
    assert n == 1
    assert len(db.rows("SELECT * FROM commitments")) == 1


@pytest.mark.asyncio
async def test_brief_drops_invented_citations():
    deal = db.get_deal("d1")
    await extractor.ingest(deal, _interaction())
    await memory.retain(playbook_bank(), "TCO reframe worked at Kestrel.", context="tactic_outcome", document_id="p1")
    events = [e async for e in briefing.build_brief("d1", True)]
    final = events[-1]
    assert final["type"] == "brief"
    b = final["brief"]
    assert [r["risk"] for r in b["key_risks"]] == ["CFO price anchor"]  # "Invented risk" dropped
    assert b["key_risks"][0]["evidence_ids"] == ["D1"]  # X99 dropped
    assert b["deal_health"] == 55
    assert briefing.cached_brief("d1", True)["brief"]["headline"]


@pytest.mark.asyncio
async def test_brief_memory_off_has_no_citations():
    events = [e async for e in briefing.build_brief("d1", False)]
    final = events[-1]
    assert final["citations"] == {} and final["brief"]["pattern_alert"] is None


@pytest.mark.asyncio
async def test_coach_and_outcome_loop_updates_playbook():
    await memory.retain(playbook_bank(), "TCO reframe worked at Kestrel.", context="tactic_outcome", document_id="p1")
    res = await coach.coach("d1", "Stratify is cheaper", "Priya Menon (CFO)")
    assert [e["memory_id"] for e in res["response"]["evidence"]] == ["P1"]  # P77 dropped
    out = await learning.outcome_for_suggestion(res["suggestion_id"], True, "")
    t = next(t for t in out["stats"]["tactics"] if t["tactic"] == "TCO reframe + pilot")
    assert t["wins"] == 1 and t["win_rate"] == pytest.approx(0.67, abs=0.01)
    mems = await memory.recall(playbook_bank(), "TCO reframe WORKED Tarang", label_prefix="P")
    assert any("WORKED" in m.text for m in mems)


@pytest.mark.asyncio
async def test_close_deal_writes_postmortem():
    deal = db.get_deal("d1")
    await extractor.ingest(deal, _interaction())
    res = await learning.close_deal("d1", "lost", "Price")
    assert db.get_deal("d1")["status"] == "lost"
    assert "CFO" in res["analysis"]
    mems = await memory.recall(playbook_bank(), "post-mortem Tarang LOST", label_prefix="P")
    assert any("post-mortem" in m.text for m in mems)


@pytest.mark.asyncio
async def test_restated_commitment_and_partial_names_are_deduped():
    deal = db.get_deal("d1")
    await extractor.ingest(deal, _interaction("i1"))
    await extractor.ingest(deal, _interaction("i2"))  # same promise restated in a later interaction
    assert len(db.rows("SELECT * FROM commitments WHERE deal_id='d1'")) == 1
    db.upsert_stakeholder("d1", "Priya", "", "skeptic", ["budget"])
    assert [s["name"] for s in db.stakeholders_for("d1")] == ["Priya Menon"]
