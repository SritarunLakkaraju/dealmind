# DealMind — common tasks. Run from the dealmind/ folder.
PY := backend/.venv/bin/python

.PHONY: install seed seed-fresh dev api web build test

install:            ## create the venv and install backend + frontend deps
	cd backend && (uv venv -q --python 3.12 .venv || python3 -m venv .venv)
	cd backend && (uv pip install -q --python .venv/bin/python -r requirements.txt || .venv/bin/pip install -q -r requirements.txt)
	cd frontend && npm install --no-audit --no-fund

seed:               ## load the synthetic deal history into Hindsight (idempotent) and pre-build briefs
	cd backend && .venv/bin/python -m scripts.seed --briefs

seed-fresh:         ## wipe DB + memory banks, then seed
	cd backend && .venv/bin/python -m scripts.seed --reset --briefs

api:                ## backend on :8000
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

web:                ## frontend dev server on :5173 (proxies /api to :8000)
	cd frontend && npm run dev

build:              ## production build; the API then serves the UI at http://localhost:8000
	cd frontend && npm run build

dev:                ## api + web together
	$(MAKE) -j2 api web

test:
	cd backend && .venv/bin/python -m pytest -q
