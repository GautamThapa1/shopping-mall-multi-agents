import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv()

from src.database import get_connection

query = "SELECT id, name, gender FROM service_user WHERE type = %s"
with get_connection() as conn, conn.cursor() as db_cursor:
    db_cursor.execute(query, ("vendor",))
    vendors = db_cursor.fetchall()

if not vendors:
    print("No vendors found.")
    raise SystemExit(0)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    api_key=os.environ["OPENAI_API_KEY"],
)

personalities = {}

for vendor_id, name, gender in vendors:
    existing_personalities = list(personalities.values())
    for attempt in range(3):
        personality = llm.invoke(f"""
        The seller's name is {name} and the gender is {gender}, please assign a random personality in one line.
        It must be different from these personalities: {existing_personalities}
        """).content.strip()
        if personality and personality.casefold() not in {
            existing.casefold() for existing in existing_personalities
        }:
            break
    else:
        raise RuntimeError(f"Could not generate a unique personality for seller {vendor_id}.")

    personalities[vendor_id] = personality

print("personalities : ", personalities)