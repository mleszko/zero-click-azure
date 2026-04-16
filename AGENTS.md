# AGENTS.md

## Cursor Cloud specific instructions

### Overview

Single-service Python FastAPI + LangGraph application — a self-correcting AI agent that generates answers, grades them against required facts, and retries with feedback. No database, no frontend, no external services required for local dev.

### Running services

- **Dev server**: `cd app && uvicorn main:app --reload --host 0.0.0.0 --port 8000`  
  Must be run from the `app/` directory (not the repo root) because of relative imports.
- **API docs**: `http://localhost:8000/docs` (Swagger UI)
- The app uses a built-in rule-based generator by default (no Azure OpenAI key needed).

### Testing

- `pytest tests/ -v` from the repo root — tests use FastAPI TestClient with the rule-based fallback, no external services needed.
- `conftest.py` adds `app/` to `sys.path` automatically.

### Linting

- No linter is configured in the repo. `ruff check app/ tests/` works cleanly.

### Key caveats

- The virtual environment must be created with `python3 -m venv .venv` — the `python3.12-venv` apt package is required on Ubuntu 24.04.
- Settings are loaded via `pydantic-settings` from env vars or `.env` file in the `app/` directory. See `app/core/settings.py` for all config options.
- `get_settings()` is cached with `@lru_cache` — changes to env vars require a process restart (hot-reload picks up code changes but not env var changes loaded at import time).
