# Copilot Instructions

## Project

Build a multi-agent shopping mall system with Python, LangChain, and LangGraph.

The intended architecture is:

```text
User
  -> Manager / Supervisor
       -> Purchase Specialist
       -> Sales Specialist
```

The manager validates or logs in the user, understands intent, and routes each request. The purchase specialist recommends items, purchases items, cancels eligible purchases, and checks order status. The sales specialist checks sales history, restocks inventory, and updates order or shipping status.

## Working Rules

- Treat this as a learning project: favor clarity and understanding over abstraction.
- Make small, focused changes. Do not generate the entire project unless explicitly requested.
- Explain the concept and reasoning before major implementation changes.
- Preserve the existing architecture and avoid unnecessary dependencies or frameworks.
- Use current LangChain and LangGraph APIs.
- Keep business rules in Python tools, not in LLM prompts.
- Keep graph state explicit and minimal, with clear typed state, nodes, edges, and conditional routing.
- Give each specialist only the tools relevant to its domain.
- Keep database logic separate from agent reasoning.

## Preferred Learning Flow

Implement and explain concepts in this order:

```text
Database -> Tools -> Specialist Agents -> Manager/Supervisor -> LangGraph -> Testing
```

When multiple implementations are reasonable, choose the one that makes the underlying LangChain or LangGraph concept easiest to understand.

## Debugging

When fixing an error:

1. Explain the cause.
2. Identify the relevant code.
3. Apply the smallest practical fix.
4. Explain why the fix works.

Do not rewrite unrelated code.

## Current Repository

- Python compatibility starts at 3.12; preserve it unless `pyproject.toml` changes.
- `main.py` is currently the empty starting point for application code.
- Dependencies, tests, linting, formatting, CI, and build commands are not configured yet. Add them only when the project needs them and document the choice.
- Validate focused changes with the narrowest available check. Until tests exist, at minimum run `python main.py` or an appropriate targeted import/type check.