import pandas as pd

from pathlib import Path
from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    inspect,
    text,
)

from db_connection import engine


# --------------------------------------------------
# 1. Define paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "online_retail_cleaned.csv"
)

TABLE_NAME = "retail_transactions"


# --------------------------------------------------
# 2. Load cleaned CSV
# --------------------------------------------------

print("Reading cleaned retail dataset...")

df = pd.read_csv(
    CSV_PATH,
    parse_dates=["InvoiceDate"],
    dtype={
        "InvoiceNo": "string",
        "StockCode": "string",
        "Description": "string",
        "Country": "string",
        "CustomerID": "string",
        "TransactionType": "string",
    },
)

print(f"Records loaded from CSV: {len(df):,}")


# --------------------------------------------------
# 3. Define PostgreSQL column types
# --------------------------------------------------

column_types = {
    "InvoiceNo": String(20),
    "StockCode": String(30),
    "Description": Text(),
    "Quantity": Integer(),
    "InvoiceDate": DateTime(),
    "UnitPrice": Numeric(12, 4),
    "CustomerID": String(20),
    "Country": String(100),
    "IsCancelled": Boolean(),
    "IsReturnCandidate": Boolean(),
    "IsZeroPrice": Boolean(),
    "IsNegativePrice": Boolean(),
    "TransactionType": String(50),
    "Revenue": Numeric(14, 4),
}


# --------------------------------------------------
# 4. Load data into PostgreSQL
# --------------------------------------------------

print("\nImporting data into PostgreSQL...")

df.to_sql(
    name=TABLE_NAME,
    con=engine,
    schema="public",
    if_exists="replace",
    index=False,
    chunksize=5000,
    dtype=column_types,
    method="multi",
)

print("Data import completed!")


# --------------------------------------------------
# 5. Verify imported records
# --------------------------------------------------

with engine.connect() as connection:

    result = connection.execute(
        text(f"SELECT COUNT(*) FROM public.{TABLE_NAME}")
    )

    database_count = result.scalar()

print("\n========== DATABASE IMPORT REPORT ==========")

print(f"CSV records: {len(df):,}")
print(f"PostgreSQL records: {database_count:,}")

if len(df) == database_count:
    print("\nSUCCESS: All records imported successfully!")
else:
    print("\nWARNING: CSV and database record counts differ.")

print(f"Table name: public.{TABLE_NAME}")

print("\nAvailable columns:")

for column in inspect(engine).get_columns(
    TABLE_NAME,
    schema="public"
):
    print(f"- {column['name']}: {column['type']}")
