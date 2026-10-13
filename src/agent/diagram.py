import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from src.agent import build_agent_graph


def generate_mermaid() -> str:
    """Build the application graph and return its Mermaid representation."""
    load_dotenv()
    model = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY", "diagram-generation-only"),
        temperature=0,
    )
    graph = build_agent_graph(model)
    return graph.get_graph(xray=True).draw_mermaid()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Mermaid diagram of the shopping assistant graph."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write Mermaid source to this file instead of stdout.",
    )
    args = parser.parse_args()
    mermaid = generate_mermaid()

    if args.output is None:
        print(mermaid)
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    content = mermaid
    if args.output.suffix.lower() in {".md", ".markdown"}:
        content = f"```mermaid\n{mermaid}\n```"
    args.output.write_text(content + "\n", encoding="utf-8")
    print(f"Mermaid graph written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
