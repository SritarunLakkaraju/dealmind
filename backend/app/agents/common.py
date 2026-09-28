"""Helpers shared by the agents."""
from __future__ import annotations

from datetime import date, datetime
from functools import lru_cache

from app.config import settings
from app.memory.service import Memory


@lru_cache
def load_prompt(name: str) -> str:
    return (settings.prompts_dir / f"{name}.md").read_text()


def inr(amount: float | None) -> str:
    """Format rupees the way Indian sales teams talk: ₹38L, ₹1.2Cr."""
    if not amount:
        return "—"
    if amount >= 1e7:
        return f"₹{amount / 1e7:.2g}Cr" if amount % 1e6 else f"₹{amount / 1e7:g}Cr"
    return f"₹{amount / 1e5:g}L"


def human_date(value: str | None) -> str:
    if not value:
        return "undated"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d %b %Y")
    except ValueError:
        return value[:10]


def today() -> str:
    return date.today().isoformat()


def format_memories(mems: list[Memory], empty: str = "(none)") -> str:
    if not mems:
        return empty
    return "\n".join(f"[{m.label}] ({human_date(m.date)}) {m.text}" for m in mems)


def deal_header(deal: dict) -> str:
    return (
        f"Company: {deal['company']} | Deal: {deal['name']} | Industry: {deal.get('industry') or '—'} | "
        f"Stage: {deal.get('stage')} | ARR: {inr(deal.get('amount'))} | "
        f"Primary competitor: {deal.get('primary_competitor') or 'unknown'} | "
        f"Economic buyer persona: {deal.get('persona') or 'unknown'} | "
        f"Next meeting: {human_date(deal.get('next_meeting'))} | Today: {human_date(today())}"
    )
