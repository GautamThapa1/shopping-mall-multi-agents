from typing import Annotated, Literal

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from psycopg import Error as PsycopgError

from src.database import get_connection
from src.tools.common import get_user_id


# Sales Specialist tools: review seller sales, replenish stock, and update shipping.
@tool
def check_sales_record(config: RunnableConfig) -> list[tuple[object, ...]] | str:
    """Return purchases made from listings owned by the configured seller."""
    try:
        with get_connection() as conn:
            return conn.execute(
                """
                SELECT p.id, p.customer_id, p.inventory_id, p.status, p.created_at,
                       i.product_id, i.price, i.remains
                FROM purchase AS p
                JOIN inventory AS i ON i.id = p.inventory_id
                WHERE i.user_id = %s
                ORDER BY p.created_at DESC
                """,
                (get_user_id(config),),
            ).fetchall()
    except (PsycopgError, ValueError):
        return "Sales records could not be retrieved."


@tool
def restock(
    product_id: Annotated[int, "Product ID to restock"],
    count: Annotated[int, "Number of units to add"],
    config: RunnableConfig,
) -> str:
    """Add stock to this seller's listing for the given product."""
    if count < 1:
        return "Restock count must be at least 1."
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE inventory
                SET remains = remains + %s
                WHERE user_id = %s AND product_id = %s
                RETURNING id
                """,
                (count, get_user_id(config), product_id),
            )
            if cursor.fetchone() is None:
                return "No listing for that product belongs to this seller."
        return "Stock replenishment is complete."
    except (PsycopgError, ValueError):
        return "Stock replenishment could not be completed."


@tool
def update_item_status(
    inventory_id: Annotated[int, "Inventory listing ID for the purchased product"],
    status: Annotated[
        Literal["In transit", "Delivered", "Cancelled"],
        "The new purchase status.",
    ],
    config: RunnableConfig,
) -> str:
    """Update purchase status for an inventory listing owned by this seller."""
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE purchase AS p
                SET status = %s
                FROM inventory AS i
                WHERE p.inventory_id = i.id AND i.id = %s AND i.user_id = %s
                RETURNING p.id
                """,
                (status, inventory_id, get_user_id(config)),
            )
            if cursor.fetchone() is None:
                return "No purchases for that listing belong to this seller."
        return "Purchase status updated."
    except (PsycopgError, ValueError):
        return "Purchase status could not be updated."