"""Learning agent: tactic outcomes and deal post-mortems flow into the shared playbook bank."""
from __future__ import annotations

from collections import defaultdict

from app import db
from app.agents.common import human_date, inr
from app.llm.client import llm
from app.memory.banks import deal_bank, playbook_bank
from app.memory.service import memory

POSTMORTEM_QUERY = (
    "This deal just closed as {result}. Using everything that happened in this deal, explain: "
    "1) the 2-3 turning points, with dates and who was involved; 2) which of our tactics helped and which "
    "hurt; 3) how the objections evolved over time; 4) one lesson for future deals with a similar persona "
    "({persona}), competitor ({competitor}) and industry ({industry}). Be specific and evidence-based. "
    "Do not speculate beyond the recorded interactions. Keep it under 250 words."
)


def outcome_text(deal: dict, category: str, objection: str, persona: str, tactic: str,
                 worked: bool, note: str, when: str) -> str:
    verdict = "WORKED" if worked else "FAILED"
    return (
        f"Tactic outcome on {human_date(when)}: In the {deal['company']} deal ({deal.get('industry')}, competing "
        f"against {deal.get('primary_competitor') or 'no named competitor'}), the {persona or 'buyer'} raised a "
        f"{category} objection: \"{objection}\". The rep used the tactic \"{tactic}\". Result: it {verdict}. {note}"
    ).strip()


async def record_tactic_outcome(deal: dict, *, category: str, objection: str, persona: str, tactic: str,
                                worked: bool, note: str, when: str, document_id: str) -> None:
    db.execute(
        "INSERT INTO tactic_outcomes (deal_id, deal_name, category, persona, competitor, tactic, worked, note, date) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (deal["id"], deal["company"], category, persona, deal.get("primary_competitor"), tactic, int(worked),
         note, when),
    )
    await memory.retain(
        playbook_bank(),
        outcome_text(deal, category, objection, persona, tactic, worked, note, when),
        context="tactic_outcome", timestamp=when, document_id=document_id,
        metadata={"deal_id": deal["id"], "category": category, "tactic": tactic,
                  "worked": str(worked).lower(), "competitor": deal.get("primary_competitor")},
    )


async def outcome_for_suggestion(suggestion_id: str, worked: bool, note: str) -> dict:
    s = db.row("SELECT * FROM suggestions WHERE id=?", (suggestion_id,))
    if not s:
        raise KeyError(suggestion_id)
    deal = db.get_deal(s["deal_id"])
    db.execute("UPDATE suggestions SET outcome=? WHERE id=?", ("worked" if worked else "failed", suggestion_id))
    await record_tactic_outcome(
        deal, category=s["category"] or "other", objection=s["objection"], persona=deal.get("persona") or "",
        tactic=s["tactic"] or "unnamed tactic", worked=worked, note=note, when=db.now_iso(),
        document_id=f"outcome-{suggestion_id}",
    )
    return {"ok": True, "stats": playbook_stats()}


async def close_deal(deal_id: str, result: str, reason: str, when: str | None = None) -> dict:
    deal = db.get_deal(deal_id)
    if not deal:
        raise KeyError(deal_id)
    when = when or db.now_iso()
    db.execute("UPDATE deals SET status=?, stage=?, closed_at=?, close_reason=? WHERE id=?",
               (result, "Closed Won" if result == "won" else "Closed Lost", when, reason, deal_id))

    reflection = await memory.reflect(
        deal_bank(deal_id),
        POSTMORTEM_QUERY.format(result=result.upper(), persona=deal.get("persona") or "unknown",
                                competitor=deal.get("primary_competitor") or "none",
                                industry=deal.get("industry") or "unknown"),
        budget="high",
    )
    analysis = reflection.text.strip() or f"No analysis available. Rep's reason: {reason}"
    text = (
        f"Deal post-mortem: the {deal['company']} deal ({deal.get('industry')}, {inr(deal.get('amount'))} ARR) "
        f"was {result.upper()} on {human_date(when)}. Primary competitor: {deal.get('primary_competitor') or 'none'}. "
        f"Economic buyer persona: {deal.get('persona')}. Rep's stated reason: {reason}.\n\n{analysis}"
    )
    db.execute("INSERT OR REPLACE INTO postmortems (deal_id, result, text, created_at) VALUES (?,?,?,?)",
               (deal_id, result, analysis, when))
    await memory.retain(playbook_bank(), text, context="deal_postmortem", timestamp=when,
                        document_id=f"postmortem-{deal_id}",
                        metadata={"deal_id": deal_id, "result": result,
                                  "competitor": deal.get("primary_competitor"), "industry": deal.get("industry")})
    return {"deal_id": deal_id, "result": result, "analysis": analysis,
            "based_on": [m.as_dict() for m in reflection.based_on]}


async def ask_playbook(question: str) -> dict:
    reflection = await memory.reflect(
        playbook_bank(),
        f'Question from the sales team: "{question}". Answer using only recorded tactic outcomes and deal '
        "post-mortems. For each recommendation, state how many times it worked vs failed and in which deals. "
        "If the evidence is thin (fewer than 2 outcomes), say so. Use short markdown bullets.",
        budget="mid",
    )
    text = reflection.text
    if not text:
        text = await llm.complete_text(
            "You are a sales enablement coach.", f"Memory is unavailable. Briefly answer: {question}"
        )
    return {"answer": text, "based_on": [m.as_dict() for m in reflection.based_on]}


def playbook_stats() -> dict:
    """Tactic x objection-category matrix with Laplace-smoothed win rates."""
    grouped: dict[tuple[str, str], dict] = defaultdict(lambda: {"wins": 0, "losses": 0, "deals": set(), "last": ""})
    for r in db.rows("SELECT * FROM tactic_outcomes ORDER BY date"):
        g = grouped[(r["tactic"], r["category"])]
        g["wins" if r["worked"] else "losses"] += 1
        g["deals"].add(r["deal_name"])
        g["last"] = max(g["last"], r["date"] or "")
        g.setdefault("competitors", set()).add(r["competitor"] or "")
    tactics = []
    for (tactic, category), g in grouped.items():
        n = g["wins"] + g["losses"]
        tactics.append({
            "tactic": tactic, "category": category, "wins": g["wins"], "losses": g["losses"],
            "win_rate": round((g["wins"] + 1) / (n + 2), 2), "deals": sorted(g["deals"]),
            "competitors": sorted(c for c in g.get("competitors", set()) if c), "last": g["last"],
        })
    tactics.sort(key=lambda t: (-t["win_rate"], -(t["wins"] + t["losses"])))
    recent = db.rows("SELECT * FROM tactic_outcomes ORDER BY id DESC LIMIT 8")
    totals = db.row("SELECT COUNT(*) n, SUM(worked) w FROM tactic_outcomes") or {"n": 0, "w": 0}
    return {"tactics": tactics, "recent": recent, "total_outcomes": totals["n"] or 0, "total_wins": totals["w"] or 0,
            "postmortems": db.rows("SELECT p.*, d.company FROM postmortems p JOIN deals d ON d.id=p.deal_id ORDER BY p.created_at DESC")}
