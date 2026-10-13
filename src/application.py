import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

from src.agent import build_agent_graph
from src.database import check_db


def create_application():
    """Initialize shared dependencies and build the shopping assistant graph."""
    load_dotenv()
    check_db()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY to run the shopping assistant.")

    model = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=api_key,
        temperature=0,
    )
    return build_agent_graph(model, checkpointer=MemorySaver())