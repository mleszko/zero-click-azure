# Cloud Agent Starter Skill: Run and Test This Repo

Use this skill when you need to quickly run, test, or validate changes in this codebase on a Cloud agent.

## 1) First 5 minutes (always do this)

1. Confirm tools are available:
   - `python3.11 --version`
   - `az --version`
   - `gh --version`
2. Authenticate if you will touch Azure/GitHub workflows:
   - `az login`
   - `az account set --subscription "<SUBSCRIPTION_ID_OR_NAME>"`
   - `gh auth login`
3. Create and activate a local venv for app + tests:
   - `cd /workspace/app`
   - `python3.11 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`

## 2) Codebase area: `app/` (FastAPI + LangGraph)

### What lives here
- API entrypoint: `app/main.py`
- API routes: `app/api/routes.py`
- Agent loop: `app/agent/*`
- Runtime flags/settings: `app/core/settings.py`

### Practical run workflow
1. Start API locally:
   - `cd /workspace/app`
   - `source .venv/bin/activate`
   - `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
2. Smoke-check endpoints:
   - `curl -s http://localhost:8000/healthz`
   - `curl -s -X POST http://localhost:8000/invoke -H "Content-Type: application/json" -d '{"prompt":"Describe security controls","required_facts":["Managed Identity is used for ACR pull","AcrPull role assignment limits registry access"],"max_correction_loops":3}'`

### Feature-flag setup and mocking
- Default local-safe mode (recommended): rule-based fallback (no Azure OpenAI):
  - `export ENABLE_AZURE_OPENAI=false`
- Enable Azure OpenAI path:
  - `export ENABLE_AZURE_OPENAI=true`
  - `export AZURE_OPENAI_ENDPOINT="https://<resource>.openai.azure.com"`
  - `export AZURE_OPENAI_DEPLOYMENT="<deployment-name>"`
  - Optional:
    - `export AZURE_OPENAI_API_VERSION="2024-06-01"`
    - `export AZURE_OPENAI_MANAGED_IDENTITY_CLIENT_ID="<uami-client-id>"`
- Mock external dependency quickly:
  - Keep `ENABLE_AZURE_OPENAI=false` to force deterministic rule-based generation while testing loop logic.

### Testing workflow for `app/`
1. Start service with desired flags.
2. Run `/healthz` to verify config + boot.
3. Run one `/invoke` request with at least 2 required facts to exercise correction loop behavior.
4. If changing settings/flags logic, repeat `/invoke` with `ENABLE_AZURE_OPENAI=true` and again with `false` to validate both branches.

## 3) Codebase area: `tests/` (pytest suites)

### What lives here
- API behavior tests: `tests/test_api.py`
- Agent-loop correctness tests: `tests/test_agent_loop.py`

### Testing workflow for `tests/`
From repo root:
- `source /workspace/app/.venv/bin/activate`
- `cd /workspace`
- Fast signal full test pass:
  - `pytest tests -q`
- Area-focused runs:
  - `pytest tests/test_api.py -q`
  - `pytest tests/test_agent_loop.py -q`

When to use which:
- Use focused test file runs while iterating.
- Use `pytest tests -q` before commit/PR updates.

## 4) Codebase area: `infra/` + deployment workflow

### What lives here
- Bicep root: `infra/main.bicep`
- Deployment defaults + env vars: `infra/main.parameters.json`
- CI deploy pipeline: `.github/workflows/deploy.yml`

### Practical validation workflow
1. For infra or workflow edits, first run local tests:
   - `source /workspace/app/.venv/bin/activate`
   - `cd /workspace && pytest tests -q`
2. Validate Azure CLI context:
   - `az account show -o table`
3. Trigger or inspect deployment workflow:
   - `gh run list --workflow deploy.yml`
   - `gh run view <run-id> --log`
4. Validate deployed app endpoint (if deployment completed):
   - `curl -s "https://<container-app-fqdn>/healthz"`
   - `curl -s -X POST "https://<container-app-fqdn>/invoke" -H "Content-Type: application/json" -d '{"prompt":"Summarize architecture security","required_facts":["Managed Identity is used for ACR pull","AcrPull role assignment limits registry access"],"max_correction_loops":3}'`

## 5) Common Cloud-agent workflow shortcuts

- If blocked by cloud auth or unavailable Azure resources, still run:
  - local FastAPI smoke checks
  - `pytest tests -q`
  and clearly mark Azure validation as pending due to environment limitations.
- Keep command output concise (`-q`, targeted test files) for fast iteration loops.
- Prefer deterministic fallback (`ENABLE_AZURE_OPENAI=false`) for reproducible CI/local debugging.

## 6) Updating this skill when new runbook knowledge is found

Whenever you discover a new reliable setup/testing trick:

1. Add it to the relevant codebase area section above (not in a generic dump).
2. Include exact command(s), expected signal, and when to use it.
3. Remove stale or duplicate steps in the same edit.
4. In your PR summary, add a one-line note like:
   - `Skill update: added <new trick> under <area> testing workflow.`
5. Re-run at least one command from the updated section before finalizing the PR to confirm the instruction is still valid.
