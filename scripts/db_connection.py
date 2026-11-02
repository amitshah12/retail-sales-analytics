
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "retail_analytics")
DB_SSLMODE = os.getenv("DB_SSLMODE", "")

if not DB_USER or not DB_PASSWORD:
    raise ValueError(
        "Database credentials are missing. Check your .env file."
    )

connection_options = {}

if DB_SSLMODE:
    connection_options["sslmode"] = DB_SSLMODE

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
    query=connection_options,
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

if __name__ == "__main__":
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))

            print("PostgreSQL connection successful!")
            print(result.scalar())

    except Exception as error:
        print("PostgreSQL connection failed!")
        print(error)

    finally:
        engine.dispose()
