# Concierge Agent

Concierge is a small FastAPI-based service that implements a multi-step "concierge" agent. It coordinates AI adapters (registered via the project's DI layer) and third-party adapters (search, browsing, email) to perform a research-and-optional-email workflow.

This README documents how to run the service locally, the main configuration options, and the HTTP endpoints exposed by the application.

## Overview
- Python FastAPI app exposed by `concierge.main:app`.
- Core behavior is implemented in `service.impl.concierge_agent_service.ConciergeAgentService`.
- Controller routes live in `controller/concierge_agent_controller.py` and include:
  - `POST /concierge/query` — run the concierge flow
  - `GET /health/third_party` — checks connectivity to search/ollama/browser adapters
  - Agents CRUD under `/agents`
  - Root health `GET /` returning a simple status object
- Adapter registration and configuration are handled by `startup.register_configured_adapters()` and `service.di`.

## Prerequisites
- Python 3.10+ (the repository's venv uses 3.13 in the exercise environment)
- pip

Dependencies are listed in `requirements.txt` at the project root. Example dependencies include FastAPI, Uvicorn, Pydantic, and common HTTP libraries.

## Setup
Create and activate a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you prefer, run inside the provided virtualenv in the workspace.

## Configuration
The service reads configuration from environment variables, `.env` files (root and `concierge/.env`), or the `config.properties` file in the `concierge` folder.

Important environment variables:
- `DEFAULT_AI_ADAPTER` — adapter key used as the default for model calls (falls back to `gemma3:4b` or `gemma`).
- `ADAPTERS` — comma-separated adapter mappings. Format: `name=module.path:callable` or `name=module.path`.
  Example: `ADAPTERS=openai=concierge.adapters.openai_adapter:call,search=concierge.adapters.search_adapter:search_web`
- `LOG_LEVEL` — logging level (default: `INFO`).
- `LOG_FORMAT` — set to `json` to enable JSON logging (if `pythonjsonlogger` is available).

Adapter registration happens on startup; see `startup.py` and `service/di.py` for wiring details.

## Run (development)
Run the app with Uvicorn from the project root:

```bash
uvicorn concierge.main:app --reload --host 0.0.0.0 --port 8000
```

The FastAPI interactive docs (if running) will be available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints
Summary of the main endpoints implemented by the service:

- GET /
  - Returns: {"status": "ok", "service": "concierge"}

- POST /concierge/query
  - Request JSON: {"goal": "user request text", "history": ["previous messages"]}
  - Response JSON: {"result": "summary text"}
  - Errors: may return 503 if a third-party adapter fails, or 500 for unexpected errors.

- GET /health/third_party
  - Runs lightweight pings against configured adapters (search, ollama, browse).
  - Returns 200 with a services map when all adapters respond; returns 503 with details when any dependency is degraded.

- Agents CRUD (in-memory store)
  - POST /agents — create an agent. Body: {"name": "...", "type": "...", "config": {...}}
  - GET /agents — list all agents
  - GET /agents/{agent_id} — fetch a single agent
  - PUT /agents/{agent_id} — update an agent partially
  - DELETE /agents/{agent_id} — delete an agent

The agents implementation is an in-memory store (`service.impl.ai_agent_service_impl.AiAgentServiceImpl`). It's intended as an example; for production you should replace with a persistence-backed implementation.

## Examples
Run a concierge query with curl:

```bash
curl -X POST http://localhost:8000/concierge/query \
  -H "Content-Type: application/json" \
  -d '{"goal": "Find a good Italian restaurant in San Francisco and a contact email", "history": []}'
```

Create an agent:

```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "research-bot", "type": "gemma", "config": {}}'
```

## API documentation
A local OpenAPI spec is included at `swagger.yaml`. You can preview it with the online editor (https://editor.swagger.io) or serve it with Swagger UI.

## Notes and implementation details
- The core orchestration lives in `ConciergeAgentService.run_concierge_agent` and calls adapters in this order: model->search->model->browse->model->(email adapter)
- The DI module `service.di` provides singletons for the AI adapter registry and an http client used by adapters.
- The project registers a fallback `gemma3:4b` adapter if not explicitly provided.

## Contributing
If you extend this project, add tests, keep the DI wiring clear, and document any new adapter interfaces.

## License
Add your project's license here.

