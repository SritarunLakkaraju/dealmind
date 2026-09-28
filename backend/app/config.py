"""Runtime configuration loaded from environment variables (and an optional .env file)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # dealmind/


def _load_dotenv() -> None:
    """Minimal .env loader so we don't need python-dotenv."""
    for candidate in (ROOT / ".env", ROOT / "backend" / ".env"):
        if not candidate.exists():
            continue
        for line in candidate.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


@dataclass(frozen=True)
class Settings:
    # LLM (any OpenAI-compatible endpoint; Groq by default)
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    llm_api_key: str = os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    llm_fallback_model: str = os.getenv("LLM_FALLBACK_MODEL", "openai/gpt-oss-20b")

    # Hindsight
    hindsight_url: str = os.getenv("HINDSIGHT_URL", "http://localhost:8888")
    hindsight_api_key: str = os.getenv("HINDSIGHT_API_KEY", "")
    # "hindsight" (required for the hackathon), "local" (offline dev), or "auto" (hindsight, else local)
    memory_backend: str = os.getenv("MEMORY_BACKEND", "auto")
    bank_prefix: str = os.getenv("BANK_PREFIX", "dealmind")
    org_id: str = os.getenv("ORG_ID", "northwind")
    rep_id: str = os.getenv("REP_ID", "rahul")

    db_path: Path = Path(os.getenv("DB_PATH", str(ROOT / "backend" / "dealmind.db")))
    data_dir: Path = ROOT / "data" / "synthetic"
    prompts_dir: Path = ROOT / "backend" / "app" / "prompts"


settings = Settings()
