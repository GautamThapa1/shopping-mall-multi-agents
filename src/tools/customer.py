from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from psycopg import Error as PsycopgError

from src.database import get_connection
from src.models import User
from src.tools.common import get_user_id


@tool
def check_validation(config: RunnableConfig) -> User | None:
    """Return the service user identified by the configured user ID, if present."""
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, name, gender, type FROM service_user WHERE id = %s",
                (get_user_id(config),),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return User(**dict(zip((column.name for column in cursor.description), row)))
    except (PsycopgError, ValueError, TypeError):
        return None


@tool
def purchase_product(
    inventory_id: Annotated[int, "ID of the inventory listing to purchase"],
    config: RunnableConfig,
) -> str:
    """Purchase one unit of an in-stock inventory listing."""
    try:
        customer_id = get_user_id(config)
        with get_connection() as conn:
            cursor = conn.execute(
                "UPDATE inventory SET remains = remains - 1 WHERE id = %s AND remains > 0 RETURNING id",
                (inventory_id,),
            )
            if cursor.fetchone() is None:
                return "That listing is unavailable or out of stock."
            conn.execute(
                "INSERT INTO purchase (customer_id, inventory_id, status) VALUES (%s, %s, %s)",
                (customer_id, inventory_id, "Pre-dispatch"),
            )
        return "The purchase has been completed."
    except (PsycopgError, ValueError):
        return "The purchase could not be completed."


@tool
def cancel_purchase(
    inventory_id: Annotated[int, "ID of the inventory listing to cancel"],
    config: RunnableConfig,
) -> str:
    """Cancel one pre-dispatch purchase and return the item to stock."""
    try:
        customer_id = get_user_id(config)
        with get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE purchase
                SET status = 'Cancelled'
                WHERE id = (
                    SELECT id
                    FROM purchase
                    WHERE customer_id = %s AND inventory_id = %s
                      AND status = 'Pre-dispatch'
                    ORDER BY created_at DESC
                    LIMIT 1
                    FOR UPDATE
                )
                RETURNING inventory_id
                """,
                (customer_id, inventory_id),
            )
            cancelled = cursor.fetchone()
            if cancelled is None:
                return "No eligible pre-dispatch purchase was found."
            conn.execute(
                "UPDATE inventory SET remains = remains + 1 WHERE id = %s",
                (cancelled[0],),
            )
        return "The purchase cancellation has been completed."
    except (PsycopgError, ValueError):
        return "The purchase cancellation could not be completed."


@tool
def check_item_status(config: RunnableConfig) -> list[tuple[object, ...]] | str:
    """Return the configured customer's purchase history."""
    try:
        with get_connection() as conn:
            return conn.execute(
                """
                SELECT p.id, p.inventory_id, p.status, p.created_at,
                       product.name, i.price
                FROM purchase AS p
                JOIN inventory AS i ON i.id = p.inventory_id
                JOIN product ON product.id = i.product_id
                WHERE p.customer_id = %s
                ORDER BY p.created_at DESC
                """,
                (get_user_id(config),),
            ).fetchall()
    except (PsycopgError, ValueError):
        return "Purchase status could not be retrieved."