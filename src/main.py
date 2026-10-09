from src.database import check_db
from dotenv import load_dotenv


def main():
    load_dotenv()
    check_db()
    print("Application started, database reachable")


if __name__ == "__main__":
    main()