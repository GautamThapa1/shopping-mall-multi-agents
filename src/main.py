import argparse
from uuid import uuid4

from dotenv import load_dotenv

from src.application import create_application
from src.database import check_db


# used for running a terminal conversation with the shopping assistant
# python -m src.main --chat --user-id USER_ID
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