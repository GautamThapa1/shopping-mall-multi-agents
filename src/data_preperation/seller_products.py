import os
import random
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from src.database import get_connection


class GeneratedPersonality(BaseModel):
    personality: str = Field(min_length=1)


class GeneratedListing(BaseModel):
    markup_percent: int = Field(ge=1, le=50)
    description: str = Field(min_length=1)


def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY before generating seller inventory.")

    with get_connection() as conn, conn.cursor() as db_cursor:
        db_cursor.execute(
            "SELECT id, name, gender FROM service_user WHERE type = %s",
            ("vendor",),
        )
        vendors = db_cursor.fetchall()

        if not vendors:
            print("No vendors found.")
            return

        vendor_products = []
        for vendor_id, name, gender in vendors:
            product_count = random.randint(5, 9)
            db_cursor.execute(
                """
                SELECT id, name, brand, gender, price, description, primary_color
                FROM product
                ORDER BY RANDOM()
                LIMIT %s
                """,
                (product_count,),
            )
            vendor_products.append((vendor_id, name, gender, db_cursor.fetchall()))

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, api_key=api_key)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)

    personality_chain = (
        ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Give each seller a distinct, one-line personality. Return only the personality.",
                ),
                (
                    "human",
                    "Seller name: {name}\nGender: {gender}\n"
                    + "Personalities already used: {existing_personalities}",
                ),
            ]
        )
        | llm.with_structured_output(GeneratedPersonality)
    )
    listing_chain = (
        ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Create a concise product listing description that preserves the product facts "
                    + "and reflects the seller's personality without mentioning the seller. Also choose "
                    + "a markup percentage from 1 through 50 that suits the seller. Return the requested fields.",
                ),
                (
                    "human",
                    "Seller personality: {personality}\nProduct: {product}",
                ),
            ]
        )
        | llm.with_structured_output(GeneratedListing)
    )

    personalities = {}
    for vendor_id, name, gender, _ in vendor_products:
        existing_personalities = list(personalities.values())
        for _ in range(3):
            result = personality_chain.invoke(
                {
                    "name": name,
                    "gender": gender,
                    "existing_personalities": existing_personalities,
                }
            )
            personality = result.personality.strip()
            if personality and personality.casefold() not in {
                existing.casefold() for existing in existing_personalities
            }:
                break
        else:
            raise RuntimeError(f"Could not generate a unique personality for seller {vendor_id}.")

        personalities[vendor_id] = personality

    inventory_rows = []
    for vendor_id, _, _, products in vendor_products:
        for product in products:
            product_id, name, brand, gender, cost, description, color = product
            if cost is None or cost < 0:
                print(f"Skipping product {product_id}: its cost is missing or negative.")
                continue

            listing = listing_chain.invoke(
                {
                    "personality": personalities[vendor_id],
                    "product": {
                        "name": name,
                        "brand": brand,
                        "gender": gender,
                        "cost": cost,
                        "description": description,
                        "primary_color": color,
                    },
                }
            )
            markup = max(1, (cost * listing.markup_percent + 99) // 100)
            sale_price = cost + markup
            inventory_rows.append(
                (
                    vendor_id,
                    product_id,
                    random.randint(1, 10),
                    sale_price,
                    listing.description.strip(),
                )
            )

    if not inventory_rows:
        print("No inventory rows were generated.")
        return

    descriptions = [row[4] for row in inventory_rows]
    vectors = embeddings.embed_documents(descriptions)
    insert_rows = [
        (*row, f"[{','.join(str(value) for value in vector)}]")
        for row, vector in zip(inventory_rows, vectors, strict=True)
    ]

    with get_connection() as conn, conn.cursor() as db_cursor:
        db_cursor.executemany(
            """
            INSERT INTO inventory
                (user_id, product_id, remains, price, description, description_ebd)
            VALUES (%s, %s, %s, %s, %s, %s::vector)
            """,
            insert_rows,
        )

    print(f"Inserted {len(insert_rows)} seller inventory listings.")


if __name__ == "__main__":
    main()