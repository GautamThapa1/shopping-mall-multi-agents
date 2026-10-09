"""Create the initial shopping mall schema."""

from typing import Sequence, Union

from alembic import op

revision: str = "e4387080a0ef"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE product (
            id BIGINT PRIMARY KEY,
            name TEXT NOT NULL,
            brand TEXT,
            gender TEXT,
            price INTEGER,
            description TEXT,
            primary_color TEXT
        )
        """
    )
    op.execute(
        """
        CREATE TABLE service_user (
            id TEXT PRIMARY KEY,
            name TEXT,
            gender TEXT,
            type TEXT
        )
        """
    )
    op.execute(
        """
        CREATE TABLE inventory (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES service_user(id),
            product_id BIGINT NOT NULL REFERENCES product(id),
            remains INTEGER NOT NULL DEFAULT 0,
            price INTEGER,
            description TEXT,
            description_ebd vector(1536)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE purchase (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            customer_id TEXT NOT NULL REFERENCES service_user(id),
            inventory_id BIGINT NOT NULL REFERENCES inventory(id),
            status TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX ON inventory USING hnsw "
        "(description_ebd vector_cosine_ops)"
    )
    op.execute("CREATE INDEX ON inventory (user_id)")
    op.execute("CREATE INDEX ON purchase (customer_id)")


def downgrade() -> None:
    op.execute("DROP TABLE purchase, inventory, service_user, product")