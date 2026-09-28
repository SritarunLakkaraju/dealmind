"""Ingest agent: interaction -> structured signals -> SQLite records + Hindsight memory."""
from __future__ import annotations

import json
import re

from app import db
from app.agents.common import deal_header, human_date, inr, load_prompt
from app.llm.client import llm
from app.memory.banks import deal_bank
from app.memory.service import memory
from app.models.schemas import ExtractionResult

_PII = re.compile(
    r"[\w.+-]+@[\w-]+\.[\w.]+"                      # email addresses
    r"|\+\d{1,3}[\s-]?\d{2,5}[\s-]?\d{3,5}[\s-]?\d{3,5}"  # international phone numbers
    r"|(?<![\d-])\d{5}[\s-]?\d{5}(?![\d-])"           # 10-digit Indian mobiles
)


def scrub(text: str) -> str:
    """Never retain email addresses or phone numbers."""
    return _PII.sub("[redacted]", text)


async def extract(deal: dict, interaction: dict) -> ExtractionResult:
    known = ", ".join(f"{s['name']} ({s['role']})" for s in db.stakeholders_for(deal["id"])) or "none yet"
    user = (
        f"DEAL: {deal_header(deal)}\nKNOWN STAKEHOLDERS: {known}\n"
        f"INTERACTION TYPE: {interaction['type']} | DATE: {interaction['date'][:10]} | "
        f"TITLE: {interaction.get('title', '')}\n\n---\n{interaction['content']}"
    )
    return await llm.complete_json(load_prompt("extractor"), user, ExtractionResult, temperature=0.1)


def compose_memory(deal: dict, interaction: dict, ex: ExtractionResult) -> str:
    """Turn an extraction into natural-language sentences for Hindsight (never raw JSON)."""
    kind = {"call": "Sales call", "email": "Email", "meeting": "Meeting", "note": "Rep note"}.get(
        interaction["type"], "Interaction"
    )
    when = human_date(interaction["date"])
    lines = [
        f"{kind} on {when} in the {deal['company']} deal (Northwind Analytics selling to {deal['company']}, "
        f"{deal.get('industry', '')}). {interaction.get('title', '')}".strip(),
    ]
    if interaction.get("participants"):
        lines.append(f"Participants: {', '.join(interaction['participants'])}.")
    if ex.summary:
        lines.append(f"Summary: {ex.summary}")
    for o in ex.objections:
        status = "resolved" if o.resolved else "still unresolved"
        handled = f" Our rep responded by: {o.how_handled}." if o.how_handled else ""
        lines.append(
            f"- On {when}, {o.raised_by or 'the prospect'} raised a {o.severity}-severity {o.category} objection: "
            f"\"{o.text}\". It is {status}.{handled}"
        )
    for c in ex.competitors:
        price = f" Their quoted price: {c.their_claimed_price}." if c.their_claimed_price else ""
        lines.append(f"- Competitor {c.name} came up on {when}: {c.context}.{price}")
    for s in ex.stakeholders:
        concerns = f" Concerns: {'; '.join(s.concerns)}." if s.concerns else ""
        new = " They are new to the deal." if s.new_to_deal else ""
        lines.append(f"- Stakeholder {s.name} ({s.role}) acted as a {s.stance} on {when}.{concerns}{new}")
    for p in ex.pricing:
        who = "Northwind (us)" if p.stated_by == "us" else deal["company"]
        lines.append(f"- Pricing on {when}: {who} mentioned {inr(p.amount)} — {p.note}.")
    for c in ex.commitments:
        owner = "Northwind (us)" if c.owner == "us" else deal["company"]
        due = f", due {c.due_date}" if c.due_date else ""
        lines.append(f"- Commitment by {owner} ({c.who}): {c.what}{due}.")
    if ex.next_steps:
        lines.append(f"- Agreed next steps: {'; '.join(ex.next_steps)}.")
    if ex.buying_signals:
        lines.append(f"- Buying signals: {'; '.join(ex.buying_signals)}.")
    if ex.risk_signals:
        lines.append(f"- Risk signals: {'; '.join(ex.risk_signals)}.")
    lines.append(f"- Overall sentiment of this {kind.lower()}: {ex.sentiment}.")
    return scrub("\n".join(lines))


_WORD = re.compile(r"[a-z0-9]+")
_FILLER = {"the", "a", "an", "and", "to", "of", "our", "their", "for", "by", "send", "share", "provide", "report"}


def _similar(a: str, b: str) -> bool:
    ta = set(_WORD.findall(a.lower())) - _FILLER
    tb = set(_WORD.findall(b.lower())) - _FILLER
    if not ta or not tb:
        return a.strip().lower() == b.strip().lower()
    return len(ta & tb) / min(len(ta), len(tb)) >= 0.6


def save_records(deal: dict, interaction: dict, ex: ExtractionResult) -> None:
    db.execute("UPDATE interactions SET extraction=? WHERE id=?", (ex.model_dump_json(), interaction["id"]))
    for s in ex.stakeholders:
        if s.name:
            db.upsert_stakeholder(deal["id"], s.name, s.role, s.stance, s.concerns)
    db.execute("DELETE FROM commitments WHERE interaction_id=?", (interaction["id"],))
    existing = db.rows("SELECT * FROM commitments WHERE deal_id=?", (deal["id"],))
    for c in ex.commitments:
        # The same promise is often restated in later calls/emails; keep the original (earliest) one.
        if c.what and not any(e["owner"] == c.owner and _similar(e["what"], c.what) for e in existing):
            existing.append({"owner": c.owner, "what": c.what})
            db.execute(
                "INSERT INTO commitments (deal_id, interaction_id, owner, who, what, due_date) VALUES (?,?,?,?,?,?)",
                (deal["id"], interaction["id"], c.owner, c.who, c.what, c.due_date),
            )


async def ingest(deal: dict, interaction: dict, extraction: ExtractionResult | None = None) -> ExtractionResult:
    """Full ingest pipeline. `extraction` may be supplied from a cache (seeding)."""
    ex = extraction or await extract(deal, interaction)
    save_records(deal, interaction, ex)
    ok = await memory.retain(
        deal_bank(deal["id"]),
        compose_memory(deal, interaction, ex),
        context=f"sales_{interaction['type']}",
        timestamp=interaction["date"],
        document_id=interaction["id"],
        metadata={
            "deal_id": deal["id"], "stage": deal.get("stage"), "persona": deal.get("persona"),
            "competitor": deal.get("primary_competitor"), "industry": deal.get("industry"),
            "interaction_id": interaction["id"], "interaction_type": interaction["type"],
        },
    )
    db.execute("UPDATE interactions SET retained=? WHERE id=?", (1 if ok else 0, interaction["id"]))
    return ex


def extraction_of(interaction: dict) -> dict | None:
    raw = interaction.get("extraction")
    return json.loads(raw) if raw else None
