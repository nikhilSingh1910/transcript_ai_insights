
[![CI](https://github.com/nikhilSingh1910/transcript_ai_insights/actions/workflows/ci.yml/badge.svg)](https://github.com/nikhilSingh1910/transcript_ai_insights/actions/workflows/ci.yml)


# Call Analytics Microservice: Steps to Run with docker
---

## 1) Put your OPENAI_API_KEY and DATABASE_URL in .env (as in your README)
    eg, 
    DATABASE_URL: postgresql://nikhilsingh:new_password@db:5432/transcript_ai_insights
    OPENAI_API_KEY: sk-proj-f2CkMJaG9itfrD_NaxLjauxaRFmCo...
---

## 2) Build and Start
````markdown
docker compose up -d --build
````
---

## 3) (first run) Seed Data and Populate AI Insights inside the container's DB:
````markdown
docker compose exec api bash -lc "PYTHONPATH=. python3 scripts/synthetic_transcript_generator.py && \
                                  PYTHONPATH=. python3 scripts/load_transcripts.py && \
                                  PYTHONPATH=. python3 scripts/ai_insights_populator.py"
````
---

## 4) Verify
````markdown
Visit: http://localhost:8000/docs
````
---

# Call Analytics Microservice: Steps to Run without docker
````markdown
An asynchronous pipeline with PostgreSQL and FastAPI that ingests sales-call transcripts, stores them durably, and serves actionable conversation analytics (embeddings, sentiment, talk ratio) via REST APIs and WebSockets.
````
---

## 1. Install Dependencies
```bash
pip3 install -r requirements.txt
```

---

## 2. Create a `.env` File for Local Development

Create a `.env` file in the project root with the following values:

```env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://<user>@localhost:5432/transcript_ai_insights
```

---

## 3. Prepare PostgreSQL

Create databases (one for the application and optionally one for tests):

```sql
CREATE DATABASE transcript_ai_insights;
CREATE DATABASE transcript_ai_insights_test;
```

Enable trigram search extension for the application database:

```sql
\c transcript_ai_insights
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

---

## 4. Run Alembic Migrations

```bash
alembic upgrade head
```

---

## 5. Generate Synthetic Transcripts

Generate mock customer service calls:

```bash
PYTHONPATH=. python3 scripts/synthetic_transcript_generator.py
```

---

## 6. Load Transcripts into the Database

```bash
PYTHONPATH=. python3 scripts/load_transcripts.py
```

---

## 7. Populate Insights and Embeddings

Generates:

* **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
* **Sentiment**: Hugging Face sentiment pipeline (mapped to −1..+1)
* **Talk ratio**: `(agent words) / (total words)`

Re-running is safe: rows already enriched are skipped.

```bash
PYTHONPATH=. python3 scripts/ai_insights_populator.py
```

---

## 8. Run API and WebSocket Server

Start the FastAPI app:

```bash
export PYTHONPATH=.
uvicorn main:app --reload --port 8000
```

### REST API Endpoints

* `GET /api/v1/calls?limit=20&agent_id=A3&min_sentiment=0`
* `GET /api/v1/calls/{call_id}`
* `GET /api/v1/calls/{call_id}/recommendations`
* `GET /api/v1/analytics/agents`
* Health check: `GET /healthz`

### WebSocket Endpoint

Path:

```
ws://localhost:8000/ws/sentiment/{call_id}
```

Example using `wscat`:

```bash
# Install wscat (Node >= 18 recommended)
npm i -g wscat
wscat -c ws://localhost:8000/ws/sentiment/<call_id>
```

Streams a simulated per-second sentiment value (bounded random walk) for approximately 2 minutes.

---

## 9. Run Tests and Check Coverage

Use a PostgreSQL test database (embedding arrays are not portable to SQLite):

```bash
export TEST_DATABASE_URL="postgresql://nikhilsingh@localhost:5432/transcript_ai_insights_test"
PYTHONPATH=. venv/bin/pytest -q
```

To check coverage:

```bash
PYTHONPATH=. venv/bin/pytest --cov=app --cov=main --cov-report=term-missing
```

---
