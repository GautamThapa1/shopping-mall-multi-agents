from typing import Annotated, Literal

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from psycopg import Error as PsycopgError
from psycopg.rows import dict_row

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
                  SELECT p.id AS purchase_id, p.customer_id, customer.name AS customer_name,
                      p.inventory_id, p.status, p.created_at, i.product_id, i.price, i.remains
                FROM purchase AS p
                JOIN inventory AS i ON i.id = p.inventory_id
                  JOIN service_user AS customer ON customer.id = p.customer_id
                WHERE i.user_id = %s
                ORDER BY p.created_at DESC
                """,
                (get_user_id(config),),
            ).fetchall()
    except (PsycopgError, ValueError):
        return "Sales records could not be retrieved."


@tool
def check_inventory(config: RunnableConfig) -> list[dict[str, object]] | str:
    """List this seller's inventory IDs, product details, prices, and stock levels."""
    try:
        with get_connection() as conn, conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT i.id AS inventory_id, i.product_id, p.name AS product_name,
                       p.brand, i.price, i.remains AS stock, i.description
                FROM inventory AS i
                JOIN product AS p ON p.id = i.product_id
                WHERE i.user_id = %s
                ORDER BY p.name, i.id
                """,
                (get_user_id(config),),
            )
            return cursor.fetchall()
    except (PsycopgError, ValueError):
        return "Inventory could not be retrieved."


@tool
def restock(
    inventory_id: Annotated[int, "Inventory listing ID from the seller's inventory"],
    count: Annotated[int, "Number of units to add"],
    config: RunnableConfig,
) -> str:
    """Add stock to one of this seller's inventory listings."""
    if count < 1:
        return "Restock count must be at least 1."
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE inventory
                SET remains = remains + %s
                WHERE id = %s AND user_id = %s
                RETURNING remains
                """,
                (count, inventory_id, get_user_id(config)),
            )
            updated_stock = cursor.fetchone()
            if updated_stock is None:
                return "No inventory listing with that ID belongs to this seller."
        return f"Stock replenishment is complete. New stock level: {updated_stock[0]}."
    except (PsycopgError, ValueError):
        return "Stock replenishment could not be completed."


@tool
def update_item_status(
    purchase_id: Annotated[int, "Purchase ID from the seller's sales records"],
    status: Annotated[
        Literal["In transit", "Delivered", "Cancelled"],
        "The new purchase status.",
    ],
    config: RunnableConfig,
) -> str:
    """Update one purchase status for a product listing owned by this seller."""
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE purchase AS p
                SET status = %s
                FROM inventory AS i
                WHERE p.inventory_id = i.id AND p.id = %s AND i.user_id = %s
                RETURNING p.id
                """,
                (status, purchase_id, get_user_id(config)),
            )
            if cursor.fetchone() is None:
                return "No purchases for that listing belong to this seller."
        return "Purchase status updated."
    except (PsycopgError, ValueError):
        return "Purchase status could not be updated."