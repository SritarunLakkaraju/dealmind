"""Pydantic models for LLM outputs and API payloads.

Every LLM output model has defaults on every field so a degraded (`partial=True`) instance can
always be constructed when the model misbehaves.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LLMOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    partial: bool = False
    error: Optional[str] = None


def _lower(v):
    return v.lower().strip() if isinstance(v, str) else v


# ---------- Extraction ----------

class Objection(BaseModel):
    model_config = ConfigDict(extra="ignore")
    text: str = ""
    category: str = "other"
    raised_by: str = ""
    severity: str = "medium"
    resolved: bool = False
    how_handled: Optional[str] = None

    _norm = field_validator("category", "severity", mode="before")(_lower)


class Competitor(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = ""
    context: str = ""
    their_claimed_price: Optional[str] = None


class Stakeholder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = ""
    role: str = ""
    stance: str = "neutral"
    concerns: list[str] = Field(default_factory=list)
    new_to_deal: bool = False

    _norm = field_validator("stance", mode="before")(_lower)


class PricePoint(BaseModel):
    model_config = ConfigDict(extra="ignore")
    amount: Optional[float] = None
    currency: str = "INR"
    stated_by: str = "them"
    note: str = ""

    @field_validator("amount", mode="before")
    @classmethod
    def _num(cls, v):
        if isinstance(v, str):
            digits = "".join(ch for ch in v if ch.isdigit() or ch == ".")
            return float(digits) if digits else None
        return v


class Commitment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    owner: str = "us"
    who: str = ""
    what: str = ""
    due_date: Optional[str] = None

    _norm = field_validator("owner", mode="before")(_lower)


class ExtractionResult(LLMOut):
    summary: str = ""
    objections: list[Objection] = Field(default_factory=list)
    competitors: list[Competitor] = Field(default_factory=list)
    stakeholders: list[Stakeholder] = Field(default_factory=list)
    pricing: list[PricePoint] = Field(default_factory=list)
    commitments: list[Commitment] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    buying_signals: list[str] = Field(default_factory=list)
    risk_signals: list[str] = Field(default_factory=list)
    sentiment: str = "neutral"
    confidence: str = "medium"


# ---------- Brief ----------

class Evidence(BaseModel):
    model_config = ConfigDict(extra="ignore")
    evidence_ids: list[str] = Field(default_factory=list)

    @field_validator("evidence_ids", mode="before")
    @classmethod
    def _ids(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.replace(";", ",").split(",") if s.strip()]
        return v or []


class Risk(Evidence):
    risk: str = ""


class OpenCommitment(Evidence):
    owner: str = "us"
    what: str = ""
    due: str = ""
    overdue: bool = False


class StakeholderNote(Evidence):
    name: str = ""
    role: str = ""
    stance: str = "neutral"
    what_they_care_about: str = ""


class LikelyObjection(Evidence):
    objection: str = ""
    recommended_tactic: str = ""
    why: str = ""
    confidence: str = "medium"


class Brief(LLMOut):
    headline: str = ""
    deal_health: int = 50
    health_reason: str = ""
    key_risks: list[Risk] = Field(default_factory=list)
    open_commitments: list[OpenCommitment] = Field(default_factory=list)
    stakeholder_notes: list[StakeholderNote] = Field(default_factory=list)
    likely_objections: list[LikelyObjection] = Field(default_factory=list)
    pattern_alert: Optional[str] = None
    pattern_alert_ids: list[str] = Field(default_factory=list)
    questions_to_ask: list[str] = Field(default_factory=list)
    do_not: list[str] = Field(default_factory=list)

    @field_validator("deal_health", mode="before")
    @classmethod
    def _health(cls, v):
        try:
            return max(0, min(100, int(float(v))))
        except (TypeError, ValueError):
            return 50


# ---------- Coach ----------

class CoachEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")
    memory_id: str = ""
    deal: str = ""
    outcome: str = ""
    summary: str = ""


class CoachResponse(LLMOut):
    response_script: str = ""
    follow_up_question: str = ""
    tactic_name: str = ""
    objection_category: str = "other"
    why_this_works: str = ""
    evidence: list[CoachEvidence] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    confidence: str = "low"


# ---------- API payloads ----------

class DealCreate(BaseModel):
    name: str
    company: str
    industry: str = ""
    amount: float = 0
    stage: str = "Discovery"
    primary_competitor: str = ""
    next_meeting: Optional[str] = None


class InteractionCreate(BaseModel):
    type: Literal["call", "email", "meeting", "note"] = "call"
    title: str = ""
    date: Optional[str] = None
    participants: list[str] = Field(default_factory=list)
    content: str


class CoachRequest(BaseModel):
    objection: str
    speaker: str = ""


class OutcomeRequest(BaseModel):
    worked: bool
    note: str = ""


class CloseRequest(BaseModel):
    result: Literal["won", "lost"]
    reason: str = ""


class AskRequest(BaseModel):
    question: str
