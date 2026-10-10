# insert customer and vendor into service_user table
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv()

from src.database import get_connection

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    api_key=os.environ["OPENAI_API_KEY"],
)

prompt = ChatPromptTemplate.from_template(
    """
    You are an expert in generating PostgreSQL queries. Please review the given table information and column details,
    and write appropriate queries based on the user's questions.

    Do not wrap in MD code blocks, do not insert newline characters with \n, just return the SQL query statement only.

    {db_info}

    {user_input}
    """
)

chain = prompt | llm

insert_user_queries = chain.invoke({
    "db_info": """
    # Table information
    - service_user: A table that contains user information.
    # Column information
    - id (varchar): The user's site ID.
    - name (varchar): The user's name.
    - gender (varchar): The user's gender.
    - type (varchar): The user's type. Use either 'customer' or 'vendor'.
    """,
    "user_input": """
    # User's Question
    Please return 20 individual insert queries generating dummy data.
    Please separate each query with a newline.
    """,
}).content
insert_user_queries = [query.strip() for query in insert_user_queries.split("\n") if query.strip()]


with get_connection() as conn, conn.cursor() as cursor:
    try:
        for index, insert_user_query in enumerate(insert_user_queries, start=1):
            fixed_query = (
                insert_user_query
                .replace("ServiceUser", "service_user")
                .replace("serviceUser", "service_user")
                .replace("'TYPE'", "'customer'" if index <= 10 else "'vendor'")
                .replace('"TYPE"', '"customer"' if index <= 10 else '"vendor"')
                .replace("TYPE", "customer" if index <= 10 else "vendor")
            )
            cursor.execute(fixed_query)

        conn.commit()
        print("ServiceUser data insertion completed.")

    except Exception as e:
        conn.rollback()
        print(f"An error occurred: {e}")