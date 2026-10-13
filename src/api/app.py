import os
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.chat import router as chat_router
from src.application import create_application


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
    app.include_router(chat_router)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
