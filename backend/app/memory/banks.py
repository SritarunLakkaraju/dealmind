"""Memory bank identities, missions and dispositions (ARCHITECTURE.md §4.1)."""
from __future__ import annotations

from dataclasses import dataclass

from app.config import settings


@dataclass(frozen=True)
class BankSpec:
    bank_id: str
    name: str
    mission: str
    disposition: dict[str, int]


def deal_bank(deal_id: str) -> BankSpec:
    return BankSpec(
        bank_id=f"{settings.bank_prefix}-deal-{deal_id}",
        name=f"Deal {deal_id}",
        mission=(
            "You track a single B2B sales deal for Northwind Analytics: every stakeholder, their "
            "concerns and stance, every objection, competitor mention, pricing statement and "
            "commitment made by either side, with dates. Be precise about who said what and when."
        ),
        disposition={"skepticism": 4, "literalism": 4, "empathy": 3},
    )


def playbook_bank() -> BankSpec:
    return BankSpec(
        bank_id=f"{settings.bank_prefix}-playbook-{settings.org_id}",
        name="Team Playbook",
        mission=(
            "You are a sales enablement coach for Northwind Analytics. You learn, across all "
            "deals, which objection-handling tactics lead to deals advancing or closing, broken "
            "down by buyer persona, competitor and industry. You weigh recorded outcomes over "
            "opinions and say when evidence is thin."
        ),
        disposition={"skepticism": 4, "literalism": 2, "empathy": 3},
    )


def rep_bank(rep_id: str | None = None) -> BankSpec:
    rep = rep_id or settings.rep_id
    return BankSpec(
        bank_id=f"{settings.bank_prefix}-rep-{rep}",
        name=f"Rep {rep}",
        mission="You learn how this sales rep prefers to work and where they need coaching.",
        disposition={"skepticism": 2, "literalism": 2, "empathy": 4},
    )
