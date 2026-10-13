.PHONY: api diagram database

api:
	uv run --frozen uvicorn src.api:app --reload

diagram:
	uv run --frozen python -m src.agent.diagram --output docs/agent-graph.md

database:
	docker compose up -d postgres