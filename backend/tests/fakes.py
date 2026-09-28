"""Deterministic fake LLM so the pipeline can be tested without network access."""
from app.models.schemas import Brief, CoachResponse, ExtractionResult


async def fake_complete_json(system, user, schema, **kw):
    if schema is ExtractionResult:
        return ExtractionResult.model_validate({
            "summary": "CFO pushed on price versus Stratify.",
            "objections": [{"text": "Stratify quoted 32 lakh", "category": "Price", "raised_by": "Priya Menon (CFO)",
                            "severity": "high", "resolved": False}],
            "competitors": [{"name": "Stratify", "context": "cheaper quote"}],
            "stakeholders": [{"name": "Priya Menon", "role": "CFO", "stance": "Skeptic", "concerns": ["price"]}],
            "pricing": [{"amount": "3,200,000", "stated_by": "them", "note": "Stratify quote"}],
            "commitments": [{"owner": "us", "who": "Rahul", "what": "Send SOC2 report", "due_date": "2026-09-09"}],
            "sentiment": "mixed",
        })
    if schema is Brief:
        return Brief.model_validate({
            "headline": "Price pressure vs Stratify", "deal_health": "55",
            "key_risks": [{"risk": "CFO price anchor", "evidence_ids": ["D1", "X99"]},
                          {"risk": "Invented risk", "evidence_ids": ["Z1"]}],
            "likely_objections": [{"objection": "Too expensive", "recommended_tactic": "TCO + pilot",
                                   "evidence_ids": "P1, P2"}],
            "pattern_alert": "Looks like Meridian", "pattern_alert_ids": ["P1"],
        })
    if schema is CoachResponse:
        return CoachResponse.model_validate({
            "response_script": "Let's compare total cost.", "tactic_name": "TCO reframe + pilot",
            "objection_category": "price", "evidence": [{"memory_id": "P1", "deal": "Kestrel", "outcome": "won"},
                                                       {"memory_id": "P77", "deal": "Fake", "outcome": "won"}],
            "confidence": "high",
        })
    return schema()


async def fake_complete_text(system, user, **kw):
    return "Reflection: the CFO is anchored on Stratify's price."
