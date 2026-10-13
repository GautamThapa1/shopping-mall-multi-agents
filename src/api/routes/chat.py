from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request

from src.api.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/v1", tags=["chat"])


def get_agent_graph(request: Request) -> Any:
    graph = getattr(request.app.state, "agent_graph", None)
    if graph is None:
        raise HTTPException(status_code=503, detail="The assistant is not ready.")
    return graph


def _message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            part["text"]
            for part in content
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        )
    return str(content)


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    graph: Any = Depends(get_agent_graph),
) -> ChatResponse:
    thread_id = payload.thread_id or str(uuid4())
    result = graph.invoke(
        {"messages": [("human", payload.message)]},
        config={
            "configurable": {
                "user_id": payload.user_id,
                "thread_id": thread_id,
            }
        },
    )
    messages = result.get("messages", [])
    if not messages:
        raise HTTPException(status_code=502, detail="The assistant returned no response.")

    return ChatResponse(
        thread_id=thread_id,
        response=_message_text(messages[-1].content),
    )
