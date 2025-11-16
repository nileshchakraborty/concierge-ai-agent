# Concierge Agent

Concierge Agent is a modular FastAPI-based assistant that performs web search, browsing, and model-based summarization. It uses an adapter pattern for external services (search providers, browsing, Ollama model server, email) and includes robust retry, circuit-breaker, and diagnostics utilities.

Features
- Async adapters using `httpx` with configurable retries and jitter (via `tenacity`).
- Circuit breaker per adapter to short-circuit repeated failures.
- Health diagnostics endpoint `/health/third_party` to check search, browse, and Ollama availability.
- Swagger UI (OpenAPI) available at `/docs` and Redoc at `/redoc`.
- Simple in-memory metrics helpers (can be replaced with Prometheus client).

Quickstart

1. Create a Python virtualenv and activate it (example with Python 3.11+):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment variables (examples):

```bash
export SERPER_API_KEY="your_serper_api_key"
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="gemma3:4b"
export LOG_LEVEL=INFO
# Optional: enable JSON logs
export LOG_FORMAT=json
```

3. Run the app using Uvicorn:

```bash
uvicorn concierge.main:app --host 127.0.0.1 --port 8000 --reload
```

4. Open Swagger UI in your browser:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

API Endpoints
- `POST /concierge/query` — main concierge flow. Body: `{ "goal": "...", "history": ["..."] }`.
- `GET /health/third_party` — pings search, Ollama and outbound browsing and returns 200 when all healthy or 503 when any dependency is degraded.
- `GET /agents`, `POST /agents`, `GET /agents/{id}`, `PUT /agents/{id}`, `DELETE /agents/{id}` — simple agent CRUD.

Testing

Run the test suite:

```bash
pytest -q
```

CI

This repository includes a GitHub Actions workflow that runs tests on push and pull requests. See `.github/workflows/ci.yml`.

Development notes
- Retry/backoff configuration is environment-driven, see `concierge/adapters/*` and `concierge/utils/retry.py`.
- Circuit breaker thresholds can be configured by env vars like `SEARCH_CB_MAX_FAILURES`, `SEARCH_CB_RESET`, etc.
- To replace in-memory metrics with Prometheus, implement a thin shim in `concierge/utils/metrics.py`.

If you'd like, I can add a `/metrics` endpoint compatible with Prometheus or wire `prometheus_client` directly.
