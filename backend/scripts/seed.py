"""Seed DealMind: replay the synthetic deal history into SQLite + Hindsight in chronological order.

    python -m scripts.seed            # idempotent (document_id keeps Hindsight free of duplicates)
    python -m scripts.seed --reset    # wipe the DB and the Hindsight banks first
    python -m scripts.seed --briefs   # also pre-generate the live deal's briefs (memory on and off)

LLM extractions are cached in data/synthetic/.cache so re-seeding is fast and deterministic.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "data" / "synthetic"))

from seed_data import DEALS, REP_MEMORIES  # noqa: E402

from app import db  # noqa: E402
from app.agents import briefing, extractor, learning  # noqa: E402
from app.config import settings  # noqa: E402
from app.llm.client import llm  # noqa: E402
from app.memory.banks import deal_bank, playbook_bank, rep_bank  # noqa: E402
from app.memory.service import memory  # noqa: E402
from app.models.schemas import ExtractionResult  # noqa: E402

CACHE = settings.data_dir / ".cache"
log = logging.getLogger("seed")


def say(msg: str) -> None:
    print(f"  {msg}", flush=True)


async def reset() -> None:
    say("Resetting database and memory banks…")
    for spec in [deal_bank(d["id"]) for d in DEALS] + [playbook_bank(), rep_bank()]:
        await memory.delete_bank(spec)
    for table in ("deals", "stakeholders", "interactions", "commitments", "suggestions", "tactic_outcomes",
                  "briefs", "postmortems", "pending_retains"):
        db.execute(f"DELETE FROM {table}")


def insert_deal(d: dict) -> dict:
    db.execute(
        "INSERT OR REPLACE INTO deals (id, name, company, industry, amount, stage, status, primary_competitor, persona, "
        "next_meeting, owner, created_at, description) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (d["id"], d["name"], d["company"], d["industry"], d["amount"], d["stage"], "open", d["primary_competitor"],
         d["persona"], d.get("next_meeting"), settings.rep_id, d["interactions"][0]["date"], d["description"]),
    )
    for name, role, stance in d["stakeholders"]:
        db.upsert_stakeholder(d["id"], name, role, stance, [])
    for it in d["interactions"]:
        db.execute(
            "INSERT OR REPLACE INTO interactions (id, deal_id, type, title, date, participants, content) VALUES (?,?,?,?,?,?,?)",
            (it["id"], d["id"], it["type"], it["title"], it["date"], json.dumps(it["participants"]), it["content"]),
        )
    return db.get_deal(d["id"])


async def cached_extraction(deal: dict, it: dict, sem: asyncio.Semaphore) -> ExtractionResult:
    path = CACHE / f"{it['id']}.json"
    if path.exists():
        return ExtractionResult.model_validate_json(path.read_text())
    for attempt in range(3):
        async with sem:
            ex = await extractor.extract(deal, it)
        if not ex.partial:
            break
        say(f"extraction of {it['id']} degraded ({(ex.error or '')[:80]}), retrying in 30s…")
        await asyncio.sleep(30)
    else:
        # Never write an empty extraction into memory; fix the LLM setup and re-run (cache keeps progress).
        raise SystemExit(f"Extraction failed for {it['id']}: {ex.error}")
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(ex.model_dump_json(indent=2))
    say(f"extracted {it['id']:<6} {len(ex.objections)} objections, {len(ex.commitments)} commitments")
    return ex


async def main(args: argparse.Namespace) -> None:
    t0 = time.perf_counter()
    db.init_db()
    await memory.start()
    print(f"Memory backend: {memory.status['backend']}  ({memory.status.get('degraded_reason') or settings.hindsight_url})")
    if memory.status["backend"] != "hindsight":
        print("  ⚠  Not using Hindsight. Set HINDSIGHT_URL/HINDSIGHT_API_KEY for the real thing.")
    if args.reset:
        await reset()

    print("1/5 Creating deals and banks")
    deals = {d["id"]: insert_deal(d) for d in DEALS}
    for spec in [deal_bank(i) for i in deals] + [playbook_bank(), rep_bank()]:
        await memory.ensure_bank(spec)

    print("2/5 Extracting signals from interactions (LLM, cached)")
    timeline = sorted(((d, it) for d in DEALS for it in d["interactions"]), key=lambda x: x[1]["date"])
    sem = asyncio.Semaphore(1)  # Groq free tier has tight tokens-per-minute limits
    extractions = await asyncio.gather(*(cached_extraction(deals[d["id"]], it, sem) for d, it in timeline))

    print(f"3/5 Retaining {len(timeline)} interactions into Hindsight in chronological order")
    for (d, it), ex in zip(timeline, extractions):
        await extractor.ingest(deals[d["id"]], it, ex)
        say(f"retained {it['date'][:10]} {d['company']:<18} {it['title']}")

    print("4/5 Retaining rep memories and tactic outcomes into the playbook")
    for when, text in REP_MEMORIES:
        await memory.retain(rep_bank(), text, context="rep_profile", timestamp=when, document_id=f"rep-{when}")
    outcomes = sorted(((d, o) for d in DEALS for o in d["tactic_outcomes"]), key=lambda x: x[1]["date"])
    for i, (d, o) in enumerate(outcomes):
        await learning.record_tactic_outcome(
            deals[d["id"]], category=o["category"], objection=o["objection"], persona=o["persona"],
            tactic=o["tactic"], worked=o["worked"], note=o["note"], when=o["date"],
            document_id=f"seed-outcome-{d['id']}-{i}",
        )
        say(f"{'✓' if o['worked'] else '✗'} {d['company']:<18} {o['tactic']}")

    print("5/5 Closing historical deals and writing post-mortems (Hindsight reflect)")
    for d in DEALS:
        if d["close"]:
            res = await learning.close_deal(d["id"], d["close"]["result"], d["close"]["reason"], d["close"]["date"])
            say(f"{d['company']:<18} {res['result'].upper():<5} post-mortem: {len(res['analysis'])} chars")

    if args.briefs:
        print("Pre-generating briefs for live deals")
        for d in DEALS:
            if not d["close"]:
                for use in (True, False):
                    async for ev in briefing.build_brief(d["id"], use):
                        if ev["type"] == "brief":
                            say(f"{d['company']} brief (memory {'on' if use else 'off'}): health {ev['brief']['deal_health']}")

    await llm.aclose()
    await memory.aclose()
    print(f"Done in {time.perf_counter() - t0:.0f}s.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--briefs", action="store_true")
    asyncio.run(main(parser.parse_args()))
