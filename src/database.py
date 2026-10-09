import os

import psycopg


def get_connection() -> psycopg.Connection:
    return psycopg.connect(os.environ["DATABASE_URL"])


def check_db() -> None:
    with get_connection() as conn:
        conn.execute("SELECT 1")