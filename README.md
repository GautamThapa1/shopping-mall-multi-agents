# 🛍️ Shopping Mall Agents

**A role-aware multi-agent shopping assistant** for customers and shopkeepers, built with LangGraph, FastAPI, and PostgreSQL + pgvector.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-multi--agent-1C3C3C)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

**Repository:** [GautamThapa1/shopping-mall-multi-agents](https://github.com/GautamThapa1/shopping-mall-multi-agents)

---

## TL;DR

- A **manager agent** reads the verified account role and routes each request to a **Purchase Specialist** (customers) or a **Sales Specialist** (shopkeepers).
- Each specialist only has access to the **tools for its own domain**, so customers can never reach seller operations.
- Product recommendations use **semantic vector search** (pgvector) over seller listing descriptions.
- Ships as a **full-stack app**: FastAPI backend, Bootstrap frontend, Alembic migrations, one-command Docker Compose setup.

## What It Does

| Workspace | Who it's for | What you can do |
| --- | --- | --- |
| **Shop** | Customers | Get product recommendations, place and cancel purchases, check order status |
| **Shopkeeper** | Sellers | View inventory and stock, review sales and customer orders, restock listings, update purchase status |

The app is served at `/` and interactive API docs at `/docs`. See the generated [agent graph](docs/agent-graph.md) for the routing workflow.

## Key Design Decisions

| Decision | Why it matters |
| --- | --- |
| **Role-based routing** using the verified account role, not the user's message | Prevents a customer from prompting their way into seller tools |
| **Tool scoping per agent** | Smaller tool surface per agent means fewer wrong tool calls and a clear security boundary |
| **pgvector inside PostgreSQL** instead of a separate vector DB | One datastore for orders, inventory, and embeddings keeps the stack simple |
| **Alembic migrations** | Reproducible schema from a clean database |

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

| Layer | Tools |
| --- | --- |
| Agents | LangChain, LangGraph, OpenAI chat + embeddings |
| Backend | Python 3.12+, FastAPI, Uvicorn |
| Data | PostgreSQL 16, pgvector, Alembic |
| Frontend | Bootstrap 5, HTML, CSS, JavaScript |
| Tooling | uv, Docker Compose, Make |

## Quick Start

**Prerequisites:** [uv](https://docs.astral.sh/uv/), Docker, and an OpenAI API key.

**1. Create a `.env` file** in the repo root (it is git-ignored):

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

**2. Start everything:**

```bash
docker compose up --build
```

**3. Open** [http://localhost:8000](http://localhost:8000) (API docs at [/docs](http://localhost:8000/docs)).

<details>
<summary><b>Run without Docker for the app (local development)</b></summary>

```bash
docker compose up -d postgres
uv sync --frozen
set -a; . ./.env; set +a
uv run --frozen alembic upgrade head
make api
```

CLI options:

```bash
uv run python -m src.main                              # check DB connectivity
uv run python -m src.main --chat --user-id USER_ID     # terminal conversation
```

</details>

## Load Demo Data

**1. Import the product catalog:**

```bash
uv run --frozen python -m src.data_preperation.import_products
```

**2. Try the Shop workspace.** A guest customer is created automatically.

**3. Try the Shopkeeper workspace.** Create a demo vendor, then generate its inventory and embeddings (uses your OpenAI key):

```bash
set -a; . ./.env; set +a
psql "$DATABASE_URL" -c "INSERT INTO service_user (id, name, type) VALUES ('demo-vendor', 'Demo Shop', 'vendor') ON CONFLICT (id) DO NOTHING"
uv run --frozen python -m src.data_preperation.seller_products
```

Connect to Shopkeeper with the ID `demo-vendor`.

> **Note:** This creates inventory, not purchases. Sales history stays empty until a shopper orders from one of the vendor's listings.

## API Reference

| Endpoint | Purpose |
| --- | --- |
| `POST /api/v1/sessions` | Create a guest customer session |
| `POST /api/v1/sessions/shopkeeper` | Verify an existing vendor, body: `{"user_id": "demo-vendor"}` |
| `POST /api/v1/chat` | Send a message; reuse the returned `thread_id` to continue the conversation |
| `GET /health` | Service health check |

Example chat request:

```http
POST /api/v1/chat
Content-Type: application/json

{
  "user_id": "generated-user-id",
  "message": "Recommend Puma shoes",
  "thread_id": null
}
```

The response contains `response` and `thread_id`. In deployment, all `/api/v1`
endpoints share a limit of **6 requests per client IP per minute**; excess
requests receive HTTP `429 Too Many Requests`. `/health` and frontend assets are
not included. The limit is enabled by default for direct Uvicorn launches and
can be set with `RATE_LIMIT_ENABLED=true`; `make api` and Docker Compose disable
it by default for local development. The default limiter storage is in-memory;
configure `RATELIMIT_STORAGE_URI` with shared storage such as Redis when running
multiple workers or replicas.

## Regenerating the Agent Graph

```bash
make diagram
```

Output is saved to `docs/agent-graph.md` (viewable with VS Code's Markdown Preview).

## Known Limitations and Next Steps

This is a prototype, and these boundaries are deliberate and documented:

| Area | Current state | Production path |
| --- | --- | --- |
| Authentication | Shopkeeper access checks a vendor ID only; IDs are identifiers, not credentials | Add real authN/authZ before exposing to untrusted users |
| Conversation memory | Checkpoints are in-memory and lost on restart | Move to a persistent Postgres checkpointer |
| Data requirements | Recommendations and seller workflows need loaded data | Add seed data to the startup flow |
| CORS | Defaults to local dev origins | Configure `CORS_ORIGINS` per environment |