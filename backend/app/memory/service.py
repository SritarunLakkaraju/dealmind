"""MemoryService — the ONLY module that talks to Hindsight.

Uses the SDK's native async methods (aretain/arecall/areflect): its sync wrappers drive their own
event loop and break when several calls run concurrently from threads.

Two backends share one interface:
  * HindsightBackend — the real thing (required for the hackathon).
  * LocalBackend     — keyword/recency search over SQLite, used only for offline development
                       or when Hindsight is unreachable in MEMORY_BACKEND=auto mode. The UI
                       shows a clear banner whenever it is active.
"""
from __future__ import annotations

import asyncio
import json
import logging
import math
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


import httpx

from app import db
from app.config import settings
from app.memory.banks import BankSpec

log = logging.getLogger("dealmind.memory")


@dataclass
class Memory:
    id: str
    text: str
    type: str = "world"
    date: str | None = None
    context: str | None = None
    bank: str = ""
    label: str = ""  # short citation id shown to the LLM and UI, e.g. D3 / P1

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Reflection:
    text: str
    based_on: list[Memory] = field(default_factory=list)


def _g(obj: Any, *names: str, default: Any = None) -> Any:
    """Read the first present attribute/key from an SDK object or dict."""
    for name in names:
        if isinstance(obj, dict) and obj.get(name) is not None:
            return obj[name]
        value = getattr(obj, name, None)
        if value is not None:
            return value
    return default


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _to_memory(item: Any, bank: str) -> Memory:
    return Memory(
        id=str(_g(item, "id", "memory_id", "uuid", default="")),
        text=str(_g(item, "text", "content", "fact", default="")),
        type=str(_g(item, "type", "fact_type", default="world")),
        date=_iso(_g(item, "occurred_start", "event_date", "mentioned_at", "timestamp", "created_at")),
        context=_g(item, "context"),
        bank=bank,
    )


def _parse_ts(ts: str | datetime | None) -> datetime | None:
    if ts is None or isinstance(ts, datetime):
        return ts
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# --------------------------------------------------------------------------- Hindsight

class HindsightBackend:
    name = "hindsight"

    def __init__(self) -> None:
        from hindsight_client import Hindsight  # imported lazily so local mode works without it

        kwargs: dict[str, Any] = {"base_url": settings.hindsight_url}
        if settings.hindsight_api_key:
            kwargs["api_key"] = settings.hindsight_api_key
        try:
            self.client = Hindsight(timeout=180.0, **kwargs)
        except TypeError:
            self.client = Hindsight(**kwargs)
        self._banks: set[str] = set()

    async def health(self) -> tuple[bool, str | None]:
        """Reachable AND authenticated (a cloud instance answers /version without a key)."""
        base = settings.hindsight_url.rstrip("/")
        headers = {"Authorization": f"Bearer {settings.hindsight_api_key}"} if settings.hindsight_api_key else {}
        r = None
        for attempt in range(2):  # cloud cold starts can be slow; retry once
            try:
                async with httpx.AsyncClient(timeout=20) as c:
                    if (await c.get(f"{base}/version")).status_code >= 400:
                        return False, f"Hindsight not reachable at {base}"
                    r = await c.get(f"{base}/v1/default/banks", headers=headers)
                break
            except httpx.HTTPError as exc:
                if attempt == 1:
                    return False, f"Hindsight not reachable at {base} ({exc.__class__.__name__})"
                await asyncio.sleep(2)
        if r.status_code in (401, 403):
            return False, "Hindsight rejected the API key — set HINDSIGHT_API_KEY in .env"
        return r.status_code < 500, None if r.status_code < 500 else f"Hindsight error {r.status_code}"

    async def ensure_bank(self, spec: BankSpec) -> None:
        if spec.bank_id in self._banks:
            return

        try:
            await self.client.acreate_bank(
                bank_id=spec.bank_id, name=spec.name, mission=spec.mission,
                disposition_skepticism=spec.disposition.get("skepticism"),
                disposition_literalism=spec.disposition.get("literalism"),
                disposition_empathy=spec.disposition.get("empathy"),
            )
        except Exception as exc:  # already exists, or server auto-creates banks
            log.debug("create_bank(%s): %s", spec.bank_id, exc)
        self._banks.add(spec.bank_id)

    async def retain(self, bank_id: str, content: str, *, context: str, timestamp: datetime | None,
                     document_id: str | None, metadata: dict[str, str]) -> None:
        await self.client.aretain(
            bank_id=bank_id, content=content, context=context, timestamp=timestamp,
            document_id=document_id, metadata=metadata,
        )

    async def recall(self, bank_id: str, query: str, *, budget: str, max_tokens: int) -> list[Memory]:
        resp = await self.client.arecall(
            bank_id=bank_id, query=query, budget=budget, max_tokens=max_tokens
        )
        items = _g(resp, "results", "memories", default=resp if isinstance(resp, list) else [])
        return [m for m in (_to_memory(i, bank_id) for i in items) if m.text]

    async def reflect(self, bank_id: str, query: str, *, budget: str, context: str | None) -> Reflection:
        resp = await self.client.areflect(
            bank_id=bank_id, query=query, budget=budget, context=context,
            include_facts=True,
        )
        based = _g(resp, "based_on")
        facts = _g(based, "memories", default=[]) or [] if based is not None else []
        return Reflection(text=str(_g(resp, "text", default="")), based_on=[_to_memory(f, bank_id) for f in facts][:12])

    async def delete_bank(self, bank_id: str) -> None:
        try:
            await self.client.adelete_bank(bank_id=bank_id)
        except Exception as exc:
            log.warning("delete_bank(%s) failed: %s", bank_id, exc)
        self._banks.discard(bank_id)


# --------------------------------------------------------------------------- Local fallback

_TOKEN = re.compile(r"[a-z0-9₹]+")
_STOP = set("the a an and or of to in on for with at by is are was were be it this that we they you "
            "our their from as has have had not but if so do did about what who when how which".split())


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOP and len(t) > 1]


class LocalBackend:
    """Offline stand-in. Not a replacement for Hindsight — no entity graph or learned observations."""

    name = "local"

    def __init__(self) -> None:
        db.execute(
            "CREATE TABLE IF NOT EXISTS local_memories (id INTEGER PRIMARY KEY AUTOINCREMENT, bank_id TEXT, "
            "document_id TEXT, text TEXT, context TEXT, date TEXT, metadata TEXT)"
        )

    async def health(self) -> tuple[bool, str | None]:
        return True, None

    async def ensure_bank(self, spec: BankSpec) -> None:
        return None

    async def retain(self, bank_id: str, content: str, *, context: str, timestamp: datetime | None,
                     document_id: str | None, metadata: dict[str, str]) -> None:
        if document_id:
            db.execute("DELETE FROM local_memories WHERE bank_id=? AND document_id=?", (bank_id, document_id))
        # Split into paragraph-sized "facts" so recall returns focused snippets.
        for chunk in [p.strip() for p in re.split(r"\n\s*\n|\n- ", content) if p.strip()]:
            db.execute(
                "INSERT INTO local_memories (bank_id, document_id, text, context, date, metadata) VALUES (?,?,?,?,?,?)",
                (bank_id, document_id, chunk, context, timestamp.isoformat() if timestamp else db.now_iso(),
                 json.dumps(metadata)),
            )

    async def recall(self, bank_id: str, query: str, *, budget: str, max_tokens: int) -> list[Memory]:
        docs = db.rows("SELECT * FROM local_memories WHERE bank_id=?", (bank_id,))
        if not docs:
            return []
        q = Counter(_tokens(query))
        df: Counter = Counter()
        toks = []
        for d in docs:
            t = set(_tokens(d["text"]))
            toks.append(t)
            df.update(t)
        n = len(docs)
        newest = max(d["date"] for d in docs)
        scored = []
        for d, t in zip(docs, toks):
            score = sum(math.log(1 + n / df[w]) for w in q if w in t)
            if d["date"] == newest:
                score += 0.2
            scored.append((score, d))
        scored.sort(key=lambda x: (x[0], x[1]["date"]), reverse=True)
        limit = {"low": 8, "mid": 14, "high": 22}.get(budget, 14)
        out, used = [], 0
        for score, d in scored[:limit]:
            used += len(d["text"]) // 4
            if used > max_tokens:
                break
            kind = "experience" if d["context"] in ("tactic_outcome", "tactic_suggested") else "world"
            out.append(Memory(id=f"local-{d['id']}", text=d["text"], type=kind, date=d["date"],
                              context=d["context"], bank=bank_id))
        return out

    async def reflect(self, bank_id: str, query: str, *, budget: str, context: str | None) -> Reflection:
        from app.llm.client import llm

        mems = await self.recall(bank_id, query, budget="high", max_tokens=6000)
        facts = "\n".join(f"- [{(m.date or '')[:10]}] {m.text}" for m in mems)
        text = await llm.complete_text(
            "Answer strictly from the provided memories. Be specific, cite dates and names, and say "
            "when evidence is thin.",
            f"MEMORIES:\n{facts or '(none)'}\n\nCONTEXT: {context or ''}\n\nQUESTION: {query}",
        )
        return Reflection(text=text, based_on=mems[:10])

    async def delete_bank(self, bank_id: str) -> None:
        db.execute("DELETE FROM local_memories WHERE bank_id=?", (bank_id,))


# --------------------------------------------------------------------------- Facade

class MemoryService:
    def __init__(self) -> None:
        self.backend: HindsightBackend | LocalBackend | None = None
        self.degraded_reason: str | None = None

    async def start(self) -> None:
        mode = settings.memory_backend.lower()
        if mode in ("hindsight", "auto"):
            try:
                backend = HindsightBackend()
                ok, reason = await backend.health()
                if ok:
                    self.backend = backend
                    log.info("Memory backend: Hindsight at %s", settings.hindsight_url)
                    await self.flush_pending()
                    return
                self.degraded_reason = reason
            except ImportError:
                self.degraded_reason = "hindsight-client not installed"
            if mode == "hindsight":
                raise RuntimeError(self.degraded_reason)
        self.backend = LocalBackend()
        log.warning("Memory backend: LOCAL fallback (%s)", self.degraded_reason or "configured")

    @property
    def status(self) -> dict:
        return {
            "backend": self.backend.name if self.backend else "none",
            "url": settings.hindsight_url if isinstance(self.backend, HindsightBackend) else None,
            "degraded_reason": self.degraded_reason,
        }

    def _b(self) -> HindsightBackend | LocalBackend:
        if self.backend is None:
            raise RuntimeError("MemoryService.start() not called")
        return self.backend

    async def ensure_bank(self, spec: BankSpec) -> None:
        await self._b().ensure_bank(spec)

    async def retain(self, spec: BankSpec, content: str, *, context: str, timestamp: str | datetime | None = None,
                     document_id: str | None = None, metadata: dict[str, Any] | None = None) -> bool:
        """Retain natural-language content. On failure, queue it for retry and return False."""
        meta = {k: str(v) for k, v in (metadata or {}).items() if v not in (None, "")}
        ts = _parse_ts(timestamp)
        try:
            await self.ensure_bank(spec)
            await self._b().retain(spec.bank_id, content, context=context, timestamp=ts,
                                   document_id=document_id, metadata=meta)
            return True
        except Exception as exc:
            log.error("retain failed on %s: %s — queued", spec.bank_id, exc)
            db.execute(
                "INSERT INTO pending_retains (payload, created_at) VALUES (?,?)",
                (json.dumps({"spec": asdict(spec), "content": content, "context": context,
                             "timestamp": ts.isoformat() if ts else None, "document_id": document_id,
                             "metadata": meta}), db.now_iso()),
            )
            return False

    async def flush_pending(self) -> int:
        done = 0
        for item in db.rows("SELECT * FROM pending_retains ORDER BY id"):
            p = json.loads(item["payload"])
            spec = BankSpec(**p["spec"])
            try:
                await self.ensure_bank(spec)
                await self._b().retain(spec.bank_id, p["content"], context=p["context"],
                                       timestamp=_parse_ts(p["timestamp"]), document_id=p["document_id"],
                                       metadata=p["metadata"])
                db.execute("DELETE FROM pending_retains WHERE id=?", (item["id"],))
                done += 1
            except Exception as exc:
                log.warning("pending retain still failing: %s", exc)
                break
        return done

    async def recall(self, spec: BankSpec, query: str, *, budget: str = "mid", max_tokens: int = 4096,
                     label_prefix: str = "M", limit: int | None = None) -> list[Memory]:
        try:
            await self.ensure_bank(spec)
            mems = await self._b().recall(spec.bank_id, query, budget=budget, max_tokens=max_tokens)
        except Exception as exc:
            log.error("recall failed on %s: %s", spec.bank_id, exc)
            return []
        mems = mems[:limit] if limit else mems  # results come back ranked; keep prompts inside LLM rate limits
        for i, m in enumerate(mems, 1):
            m.label = f"{label_prefix}{i}"
        return mems

    async def reflect(self, spec: BankSpec, query: str, *, budget: str = "mid", context: str | None = None) -> Reflection:
        try:
            await self.ensure_bank(spec)
            return await self._b().reflect(spec.bank_id, query, budget=budget, context=context)
        except Exception as exc:
            log.error("reflect failed on %s: %s", spec.bank_id, exc)
            return Reflection(text="")

    async def delete_bank(self, spec: BankSpec) -> None:
        await self._b().delete_bank(spec.bank_id)

    async def aclose(self) -> None:
        client = getattr(self.backend, "client", None)
        if client is not None:
            try:
                await client.aclose()
            except Exception:
                pass


memory = MemoryService()
