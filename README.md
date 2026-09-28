# DealMind: a deal intelligence agent that learns

> **A sales co-pilot that remembers every call, email and objection in a deal, briefs the rep in seconds before the next call, and learns across deals which objection-handling tactics actually win.**
> Built for HackWithHyderabad 3.0 on **[Hindsight](https://hindsight.vectorize.io)** memory.

Sales reps waste hours re-reading CRM notes before calls, and every team keeps re-learning the same lessons. DealMind remembers the whole deal and the whole team's history:

- **Pre-call brief with citations:** risks, overdue promises, who's in the room, likely objections, and the tactic that won in a similar past deal. Every claim links to the memory behind it.
- **Pattern alerts:** *"This deal mirrors Meridian Payments (lost to Stratify): CFO price anchoring plus a late SOC2 report."*
- **Live objection coach:** type what the prospect just said and get a speakable response grounded in past wins, plus what to avoid.
- **Learning loop:** 👍/👎 on a tactic, or closing a deal, writes the outcome and a Hindsight-reflected post-mortem into a shared **playbook** memory. The next recommendation changes.
- **Memory ON/OFF toggle:** the same brief with and without memory, side by side.

## Quick start

```bash
cd dealmind
make install                     # Python venv + npm packages
cp .env.example .env             # then fill in the two keys (see below)
make seed                        # replays 4 deals / 22 interactions into Hindsight (~5–10 min the first time)
make build && make api           # open http://localhost:8000
# or, for development with hot reload:  make dev   → http://localhost:5173
```

### Getting the keys

**1. Groq (LLM, free):**
1. Go to <https://console.groq.com> and sign in with Google or GitHub.
2. In the left menu, open **API Keys**, click **Create API Key**, name it `dealmind`, and copy it (it starts with `gsk_`).
3. In `.env`, set `GROQ_API_KEY=gsk_...`

**2. Hindsight Cloud (memory, $50 free credits):**
1. Sign up at <https://ui.hindsight.vectorize.io/signup>.
2. Open **Billing** and apply the promo code **`MEMHACK99`**.
3. Create an API key in the dashboard (API keys / Settings) and copy it.
4. In `.env`, set `HINDSIGHT_URL=https://api.hindsight.vectorize.io` and `HINDSIGHT_API_KEY=<your key>`.

The sidebar shows **"Hindsight connected"** in green when both keys work. If it shows *Local memory (offline)*, the reason appears underneath it.

<details><summary>Self-hosted Hindsight instead (Docker)</summary>

```bash
docker run -d --name hindsight -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_PROVIDER=groq -e HINDSIGHT_API_LLM_API_KEY=$GROQ_API_KEY \
  -e HINDSIGHT_API_LLM_MODEL=openai/gpt-oss-20b \
  -v $HOME/.hindsight-docker:/home/hindsight/.pg0 ghcr.io/vectorize-io/hindsight:latest
```
Then set `HINDSIGHT_URL=http://localhost:8888` and leave `HINDSIGHT_API_KEY` empty. The Hindsight UI runs at <http://localhost:9999>.
</details>

## Architecture

```
React (Vite + Tailwind)  ──REST/SSE──►  FastAPI
                                          │
          ┌──────────────┬───────────────┼────────────────┬───────────────┐
    Extractor agent  Briefing agent  Live coach      Learning agent
    (call→signals)   (recall+reflect) (fast recall)  (outcomes, post-mortems)
          └──────────────┴───────┬───────┴────────────────┘
                          MemoryService  ── the only Hindsight client
                ┌────────────────┼──────────────────┐
         deal-<id> banks    playbook bank       rep bank
        (what happened)   (what works, team)   (how the rep works)

   SQLite = records the UI renders · Groq gpt-oss-120b (fallback qwen3-32b) = reasoning
```

- **LLM robustness:** no dependence on function calling. JSON mode goes through Pydantic validation, then one repair call, then the fallback model, then a schema-valid degraded result (`backend/app/llm/client.py`).
- **Grounding:** the server drops any citation the model invents, so claims about the deal need recalled evidence.
- **Edge cases:** empty deal bank (the brief falls back to the playbook), Hindsight down (retains are queued and retried, and the UI shows a banner), restated promises deduplicated, partial names merged ("Priya" → "Priya Menon"), idempotent re-ingest via `document_id`, emails and phone numbers scrubbed before retain.

## How Hindsight memory is used

All memory access goes through `backend/app/memory/service.py`, the only module that imports `hindsight_client`.

| Bank | Holds |
|---|---|
| `dealmind-deal-<id>` | One per deal: objections, competitors, pricing, promises and stakeholder stances, with real timestamps |
| `dealmind-playbook-northwind` | Shared by the team: tactic → outcome pairs and win/loss post-mortems |
| `dealmind-rep-rahul` | The rep's preferences and coaching notes |

| Operation | Where | Why |
|---|---|---|
| `retain` → deal bank | `agents/extractor.py` | Each call or email is stored as natural-language facts (`document_id` = interaction id, so re-ingesting is idempotent) |
| `recall` ×3 + `reflect` (in parallel) | `agents/briefing.py` | The pre-call brief: deal facts, lessons from similar past deals, rep preferences, and the biggest current risk |
| `recall` (budget low) | `agents/coach.py` | Fast live objection coaching from this deal and the playbook |
| `retain` → playbook | `agents/learning.py` | 👍/👎 tactic outcomes. **This is the learning loop.** |
| `reflect` → `retain` → playbook | `agents/learning.py` | When a deal closes, Hindsight writes the post-mortem into team memory |
| `reflect` → playbook | `agents/learning.py` | "Ask the playbook" questions |

Failed retains are queued in SQLite and replayed on the next startup.

## The demo story (3 min)

1. **Pipeline:** Tarang Payments, call #4 in 2 days. Three closed deals sit below it; their post-mortems trained the playbook.
2. **Memory OFF brief:** generic advice.
3. **Memory ON brief:** the CFO's ₹38L ceiling vs Stratify's ₹31L, the **SOC2 promise overdue since 9 Sep**, and a pattern alert that this deal looks like Meridian, which was lost. Hover the citation chips to see the source memories.
4. **Live coach:** "Can you just match Stratify's price?" returns the TCO + paid pilot tactic that won Kestrel, and warns that discounting early lost Meridian.
5. Click **👍 Worked**. The playbook record updates, and **Ask the playbook** now cites it.
6. **Close a deal:** Hindsight reflects over the whole deal and writes the post-mortem into team memory.

## Data

`data/synthetic/seed_data.py` contains 4 fictional deals (Meridian Payments *lost*, Kestrel Health *won*, Orbitra Logistics *won*, Tarang Payments *live*) with 22 speaker-labelled calls and emails in Indian-market ₹ figures. The lessons are planted in the conversations and are never stated outright; the agent has to learn them.

## Tests

```bash
make test     # pipeline tests with a fake LLM and the local memory backend
```

## Layout

```
backend/app/
  memory/   service.py (Hindsight + local fallback), banks.py (missions, dispositions)
  agents/   extractor.py, briefing.py, coach.py, learning.py
  llm/      client.py (Groq, JSON repair, fallback)
  prompts/  extractor.md, briefing.md, coach.md
  main.py   FastAPI routes (+ serves the built UI)
backend/scripts/seed.py
frontend/src/  pages (Pipeline, DealRoom, Playbook), components
```
