import argparse
import os
from uuid import uuid4

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

from src.agent import build_agent_graph
from src.database import check_db


def create_application():
    """Initialize the database-backed shopping assistant graph."""
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


def run_chat(user_id: str) -> None:
    """Run a terminal conversation for an existing service user."""
    agent = create_application()
    config = {
        "configurable": {
            "user_id": user_id,
            "thread_id": str(uuid4()),
        }
    }

    print("Shopping assistant ready. Type 'exit' to end the conversation.")
    while True:
        request = input("You: ").strip()
        if request.casefold() in {"exit", "quit"}:
            break
        if not request:
            continue

        result = agent.invoke({"messages": [("human", request)]}, config=config)
        response = result["messages"][-1].content
        if isinstance(response, list):
            response = "\n".join(
                part["text"]
                for part in response
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            )
        print(f"Assistant: {response}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Shopping mall agent application")
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Start a terminal conversation instead of running the database check",
    )
    parser.add_argument("--user-id", help="Service user ID required with --chat")
    args = parser.parse_args()

    if args.chat:
        if not args.user_id:
            parser.error("--user-id is required with --chat")
        run_chat(args.user_id)
        return

    load_dotenv()
    check_db()
    print("Application started, database reachable")


if __name__ == "__main__":
    main()