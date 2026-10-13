import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from src.application import create_application
from src.database import get_connection

FRONTEND_DIRECTORY = Path(__file__).resolve().parents[1] / "frontend"


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=10_000)
    thread_id: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("user_id", "message", "thread_id")
    @classmethod
    def strip_nonempty_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Value must not be blank.")
        return value


class ChatResponse(BaseModel):
    thread_id: str
    response: str


class GuestSessionResponse(BaseModel):
    user_id: str


class VendorSessionRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)

    @field_validator("user_id")
    @classmethod
    def strip_user_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("User ID must not be blank.")
        return value


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


def create_api_app(agent_graph: Any | None = None) -> FastAPI:
    """Create the HTTP app; an injected graph keeps route tests self-contained."""
    load_dotenv()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.agent_graph is None:
            app.state.agent_graph = create_application()
        yield
        app.state.agent_graph = None

    app = FastAPI(
        title="Shopping Mall Assistant API",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.agent_graph = agent_graph

    cors_origins = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5500,http://127.0.0.1:5500",
        ).split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.post(
        "/api/v1/sessions",
        response_model=GuestSessionResponse,
        status_code=201,
        tags=["chat"],
    )
    def create_guest_session() -> GuestSessionResponse:
        user_id = str(uuid4())
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO service_user (id, name, type) VALUES (%s, %s, %s)",
                (user_id, "Guest", "customer"),
            )
        return GuestSessionResponse(user_id=user_id)

    @app.post(
        "/api/v1/sessions/shopkeeper",
        response_model=GuestSessionResponse,
        tags=["chat"],
    )
    def create_shopkeeper_session(payload: VendorSessionRequest) -> GuestSessionResponse:
        with get_connection() as conn:
            vendor = conn.execute(
                "SELECT id FROM service_user WHERE id = %s AND type = %s",
                (payload.user_id, "vendor"),
            ).fetchone()
        if vendor is None:
            raise HTTPException(status_code=403, detail="Shopkeeper account was not found.")
        return GuestSessionResponse(user_id=vendor[0])

    @app.post("/api/v1/chat", response_model=ChatResponse, tags=["chat"])
    def chat(
        payload: ChatRequest,
        graph: Annotated[Any, Depends(get_agent_graph)],
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
            raise HTTPException(
                status_code=502,
                detail="The assistant returned no response.",
            )

        return ChatResponse(
            thread_id=thread_id,
            response=_message_text(messages[-1].content),
        )

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.mount(
        "/",
        StaticFiles(directory=FRONTEND_DIRECTORY, html=True),
        name="frontend",
    )
    return app


app = create_api_app()