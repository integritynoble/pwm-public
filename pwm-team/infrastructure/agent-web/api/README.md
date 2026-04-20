# PWM REST API

FastAPI service that serves `/api/*` — read-only JSON view of PWM on-chain
state (via the indexer DB) joined with off-chain genesis JSONs.

See the top-level [README](../README.md) for architecture, endpoints, and run
instructions. Run from the `infrastructure/agent-web/` directory with
`PYTHONPATH=. uvicorn api.main:app --reload`.
