# Shopping Mall Agents

Run the database check with:

```bash
python -m src.main
```

Start an interactive shopping assistant session for a service user with:

```bash
python -m src.main --chat --user-id USER_ID
```

Set `DATABASE_URL` and `OPENAI_API_KEY` in the environment (or in `.env`). The
optional `OPENAI_MODEL` setting defaults to `gpt-4o-mini`. The graph routes
customer recommendations and orders to the Purchase Specialist, and seller
records, restocking, and shipping updates to the Sales Specialist.

## HTTP API

Start the API locally with:

```bash
uv run --frozen uvicorn src.api.main:app --reload
```

Or run the full Docker Compose stack with `docker compose up --build`. The API
is available at `http://localhost:8000`; interactive documentation is at
`http://localhost:8000/docs`.

Send a message with `POST /api/v1/chat`:

```json
{
	"user_id": "customer-id",
	"message": "Recommend a blue shirt"
}
```

The response contains `response` and `thread_id`. Send that `thread_id` with
the next request to continue the same conversation. Conversation memory is
in-process and is lost when the API restarts. Set `CORS_ORIGINS` to a
comma-separated list of frontend origins; it defaults to localhost ports 5500.

The current API accepts `user_id` in the request body for development and
validates that it exists. This is not authentication; add authenticated user
identity before exposing the API to untrusted clients.

Generate the graph's Mermaid source without connecting to the database or calling
the model with:

```bash
uv run --frozen python -m src.agent.diagram --output docs/agent-graph.md
```
