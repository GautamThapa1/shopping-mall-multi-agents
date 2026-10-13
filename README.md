# Shopping Mall Agents

**Repository:** [GautamThapa1/shopping-mall-multi-agents](https://github.com/GautamThapa1/shopping-mall-multi-agents)

A two-sided shopping assistant built with LangGraph, FastAPI, PostgreSQL, and
Bootstrap. Customers can discover products and manage their orders; shopkeepers
can inspect inventory and sales, restock listings, and update purchase status.

The project demonstrates a role-aware multi-agent workflow: a manager routes
requests using the verified account role to focused Purchase and Sales
Specialists, each with only the tools for its domain. Product recommendations
use vector similarity over seller listing descriptions stored in PostgreSQL
with pgvector.

## Product Demo

The browser app has two workspaces:

| Workspace | Capabilities |
| --- | --- |
| Shop | Guest session creation, product recommendations, purchase, cancellation, and order-status checks |
| Shopkeeper | Inventory IDs and stock lookup, sales and customer-order history, listing-specific restocking, and purchase-status updates |

The frontend is served by FastAPI at `/`. OpenAPI documentation is available at
`/docs`. The generated [agent graph](docs/agent-graph.md) shows the routing
workflow.

## Architecture

```mermaid
flowchart LR
		Browser[Bootstrap frontend] --> API[FastAPI]
		API --> Graph[LangGraph workflow]
		Graph --> Manager[Manager / router]
		Manager --> Purchase[Purchase Specialist]
		Manager --> Sales[Sales Specialist]
		Purchase --> CustomerTools[Recommendation and order tools]
		Sales --> SellerTools[Inventory, sales, and shipping tools]
		CustomerTools --> Database[(PostgreSQL + pgvector)]
		SellerTools --> Database
		Purchase --> Models[OpenAI chat and embeddings]
		Sales --> Models
```

## Tech Stack

- Python 3.12+
- LangChain and LangGraph
- FastAPI and Uvicorn
- PostgreSQL 16 with pgvector
- Alembic migrations
- Bootstrap 5, HTML, CSS, and JavaScript
- OpenAI chat and embedding models
- Docker Compose for local services

## Run Locally

Install [uv](https://docs.astral.sh/uv/) and Docker, then create a `.env` file
in the repository root. `.env` is git-ignored.

```dotenv
POSTGRES_USER=mall
POSTGRES_PASSWORD=change-this-local-password
POSTGRES_DB=shopping_mall
POSTGRES_PORT=5432
APP_PORT=8000
DATABASE_URL=postgresql://mall:change-this-local-password@localhost:5432/shopping_mall
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
```

Start the database, run migrations, and launch the API and frontend:

```bash
docker compose up --build
```

Visit `http://localhost:8000/`. The interactive API docs are at
`http://localhost:8000/docs`.

For local development outside Docker, start the database with
`docker compose up -d postgres`, then run:

```bash
uv sync --frozen
set -a
. ./.env
set +a
uv run --frozen alembic upgrade head
make api
```

The existing CLI can check database connectivity with `uv run python -m
src.main` or start a terminal conversation with
`uv run python -m src.main --chat --user-id USER_ID`.

## Demo Data

Load the product catalog after the database is available:

```bash
uv run --frozen python -m src.data_preperation.import_products
```

The Shop workspace creates a guest customer automatically. To demo Shopkeeper,
create a vendor record using the same database URL:

```bash
set -a
. ./.env
set +a
psql "$DATABASE_URL" -c "INSERT INTO service_user (id, name, type) VALUES ('demo-vendor', 'Demo Shop', 'vendor') ON CONFLICT (id) DO NOTHING"
```

Then generate vendor inventory and its recommendation embeddings:

```bash
uv run --frozen python -m src.data_preperation.seller_products
```

This data-generation script uses the configured OpenAI API key. Connect to
Shopkeeper with the ID `demo-vendor`. It creates inventory, not purchases, so
sales history is empty until a shopper places an order from one of the vendor's
listings.

## API

Create a guest customer session:

```http
POST /api/v1/sessions
```

Verify an existing vendor record for the Shopkeeper demo:

```http
POST /api/v1/sessions/shopkeeper
Content-Type: application/json

{"user_id": "demo-vendor"}
```

Send a message; reuse the returned `thread_id` to continue that conversation:

```http
POST /api/v1/chat
Content-Type: application/json

{
	"user_id": "generated-user-id",
	"message": "Recommend Puma shoes",
	"thread_id": null
}
```

The response includes `response` and `thread_id`. `GET /health` is available for
a basic service health check.

## Graph Diagram

Regenerate the Mermaid diagram after changing the graph:

```bash
make diagram
```

The Markdown output is saved to `docs/agent-graph.md` and can be viewed with
VS Code's Markdown Preview.

## Prototype Boundaries

- Shopkeeper access currently checks a vendor service-user ID; it is not password-based authentication. Guest and vendor IDs are identifiers, not credentials.
- Add real authentication and authorization before exposing this API to untrusted users.
- Conversation checkpoints use in-memory storage and are lost when the API process restarts.
- `CORS_ORIGINS` defaults to local frontend development origins and can be set to a comma-separated list.
- Recommendation and seller-inventory data must be loaded before those workflows return useful results.
