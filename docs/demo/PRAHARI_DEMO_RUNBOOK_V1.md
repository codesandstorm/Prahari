# PRAHARI Demo Runbook V1

**Owner:** PRAHARI integration team
**Status:** APPROVED WITH LIMITATIONS
**Document type:** RUNBOOK

Use Windows CMD. Never commit credentials.

```bat
cd C:\Users\ASUS\Documents\Projects\PRAHARI-final-prediction
.venv\Scripts\activate
set "DATABASE_URL=postgresql+psycopg://USER:URL_ENCODED_PASSWORD@localhost:5432/prahari"
set "APP_ENV=demo"
set "CORS_ORIGINS=http://localhost:3000,http://localhost:5173"
set "LLM_ENABLED=true"
ollama list
sc query postgresql-x64-18
python -m alembic upgrade head
python -m backend.load_data
python scripts\run_prototype_acceptance.py
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In another CMD window with the same environment:

```bat
curl http://127.0.0.1:8000/api/v1/health
start http://127.0.0.1:8000/docs
curl http://127.0.0.1:8000/api/v1/review-queue
curl -X POST http://127.0.0.1:8000/api/v1/assistant/query -H "Content-Type: application/json" -d "{\"request_id\":\"demo-project\",\"question\":\"Why is this project prediction withheld?\",\"canonical_project_id\":\"PRH-400010\"}"
curl -X POST http://127.0.0.1:8000/api/v1/assistant/query -H "Content-Type: application/json" -d "{\"request_id\":\"demo-rag\",\"question\":\"What is PAIMANA?\"}"
```

Expected current state: model release and probabilities withheld, risk-driven reviews zero, no alerts. Never paste a password into a committed file or screenshot.
