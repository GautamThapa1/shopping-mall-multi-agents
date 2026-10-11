from typing import Annotated

from langchain_core.tools import tool
from openai import OpenAIError
from psycopg import Error as PsycopgError

from src.database import get_connection


def _vector_literal(vector: list[float]) -> str:
    return f"[{','.join(str(value) for value in vector)}]"


@tool
def get_recommendation(
    query: Annotated[str, "The user's product request"],
    color: Annotated[str | None, "Optional product color"] = None,
    count: Annotated[int | None, "Number of products to recommend"] = None,
) -> list[tuple[object, ...]] | str:
    """Recommend in-stock products using description similarity and an optional color."""
    if count is not None and count < 1:
        return "Recommendation count must be at least 1."

    try:
        from langchain_openai import OpenAIEmbeddings

        embedding = OpenAIEmbeddings(model="text-embedding-3-small").embed_query(query)
        sql = """
            SELECT p.name, p.brand, p.gender, i.price, i.description
            FROM inventory AS i
            JOIN product AS p ON p.id = i.product_id
            WHERE i.remains > 0
        """
        parameters: list[object] = []
        if color:
            sql += " AND lower(replace(p.primary_color, ' ', '')) = lower(replace(%s, ' ', ''))"
            parameters.append(color)
        sql += " ORDER BY i.description_ebd <=> %s::vector LIMIT %s"
        parameters.extend((_vector_literal(embedding), count or 5))

        with get_connection() as conn:
            return conn.execute(sql, parameters).fetchall()
    except (OpenAIError, ImportError, PsycopgError, ValueError):
        return "The recommendation search could not be completed."