# PRAHARI Demo Startup Checklist

**Owner:** PRAHARI integration team
**Status:** APPROVED WITH LIMITATIONS
**Document type:** RUNBOOK

1. Activate the virtual environment and set `DATABASE_URL` without printing it.
2. Confirm PostgreSQL and run `python -m alembic upgrade head`.
3. Confirm the canonical ingestion run and zero unintended alerts.
4. Confirm `llama3:8b` appears in `ollama list`.
5. Run `python scripts/prepare_demo_environment.py` to check and warm dependencies.
6. Start FastAPI, then request review queue page 1 once to populate the version-keyed cache.
7. Run `python scripts/run_demo_smoke.py`.
8. Confirm Model Release remains `WITHHELD` and risk-driven review remains zero.

Frontend loading text should progress from “Retrieving verified source evidence…” to “Generating grounded explanation…”. For project routes already withheld, show “Prediction withheld — evidence shown below” without waiting for generation. On timeout, preserve deterministic evidence and offer retry; never retain stale probability or risk values.
