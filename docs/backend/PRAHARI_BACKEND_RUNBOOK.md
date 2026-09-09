# PRAHARI Backend Runbook

**Owner:** PRAHARI Team
**Area:** Backend
**Document Type:** OPERATIONS
**Status:** APPROVED PROTOTYPE
**Last Updated:** 2026-09-09
**Canonical:** YES

From Windows CMD in the repository root:

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements-lock.txt
set DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/prahari
set APP_ENV=development
set CORS_ORIGINS=http://localhost:5173
python -m alembic upgrade head
python scripts\load_backend_data.py
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In a second CMD window, run `python -m pytest -m "not integration" -v`. Check `http://127.0.0.1:8000/api/v1/health`. A live assistant smoke requires Ollama and `LLM_ENABLED=true`; normal tests use a fake and never contact Ollama. Stop with Ctrl+C. Run `python -m alembic downgrade base` only on an expendable development database.

The loader requires `project_master.csv`, source-backed `project_month.csv`, and `report_month.csv` in `PROCESSED_DATA_DIR`. It deliberately rejects substitution of the ML-ready research table.
