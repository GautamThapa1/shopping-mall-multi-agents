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
