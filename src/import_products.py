# insert data into product_table from csv file
import pandas as pd
from dotenv import load_dotenv

from src.database import get_connection


def main() -> None:
    load_dotenv()

    df = pd.read_csv("data/myntra_products_catalog.csv")
    df = df.rename(columns={
        "ProductID": "id",
        "ProductName": "name",
        "ProductBrand": "brand",
        "Price (INR)": "price",
        "PrimaryColor": "primary_color",
    })

    columns = ("id", "name", "brand", "Gender", "price", "Description", "primary_color")
    df = df.loc[:, columns].astype(object).where(pd.notna(df), None)
    rows = list(df.itertuples(index=False, name=None))

    with get_connection() as conn, conn.cursor() as cursor:
        cursor.executemany(
            """
                INSERT INTO product
                    (id, name, brand, gender, price, description, primary_color)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
            rows,
        )

if __name__ == "__main__":
    main()