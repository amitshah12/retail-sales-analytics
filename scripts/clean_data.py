import pandas as pd
import numpy as np
from pathlib import Path

# --------------------------------------------------
# 1. Define project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "online_retail.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = PROCESSED_DIR / "online_retail_cleaned.csv"


# --------------------------------------------------
# 2. Load raw dataset
# --------------------------------------------------

print("Loading raw dataset...")

df = pd.read_csv(RAW_DATA_PATH)

original_rows = len(df)

print(f"Original records: {original_rows:,}")


# --------------------------------------------------
# 3. Remove exact duplicate records
# --------------------------------------------------

duplicate_count = df.duplicated().sum()

print(f"\nExact duplicate occurrences: {duplicate_count:,}")

df = df.drop_duplicates().copy()

print(f"Records after duplicate removal: {len(df):,}")


# --------------------------------------------------
# 4. Convert data types
# --------------------------------------------------

df["InvoiceDate"] = pd.to_datetime(
    df["InvoiceDate"],
    format="%m/%d/%Y %H:%M",
    errors="coerce"
)

# Preserve CustomerID as an identifier, not a measurement.
df["CustomerID"] = (
    pd.to_numeric(df["CustomerID"], errors="coerce")
    .astype("Int64")
    .astype("string")
)

# --------------------------------------------------
# 5. Create data-quality and transaction flags
# --------------------------------------------------

df["IsCancelled"] = df["InvoiceNo"].str.startswith(
    "C", na=False
)

df["IsReturnCandidate"] = (
    (~df["IsCancelled"]) & (df["Quantity"] < 0)
)

df["IsZeroPrice"] = df["UnitPrice"] == 0

df["IsNegativePrice"] = df["UnitPrice"] < 0

# --------------------------------------------------
# 6. Classify transaction types
# --------------------------------------------------

conditions = [
    df["IsCancelled"],
    df["IsReturnCandidate"],
    df["IsNegativePrice"],
    df["IsZeroPrice"]
]

choices = [
    "Cancelled Invoice",
    "Potential Return",
    "Negative Price Adjustment",
    "Zero-priced Item"
]

df["TransactionType"] = np.select(
    conditions,
    choices,
    default="Sale"
)

# --------------------------------------------------
# 7. Calculate transaction value
# --------------------------------------------------

df["Revenue"] = df["Quantity"] * df["UnitPrice"]

# --------------------------------------------------
# 8. Check invalid dates
# --------------------------------------------------

invalid_dates = df["InvoiceDate"].isna().sum()

# --------------------------------------------------
# 9. Save processed dataset
# --------------------------------------------------

df.to_csv(OUTPUT_PATH, index=False)

# --------------------------------------------------
# 10. Print cleaning report
# --------------------------------------------------

print("\n========== DATA CLEANING REPORT ==========")

print(f"Original records: {original_rows:,}")
print(f"Duplicate occurrences removed: {duplicate_count:,}")
print(f"Final records: {len(df):,}")

print(f"\nMissing CustomerID: {df['CustomerID'].isna().sum():,}")
print(f"Missing Description: {df['Description'].isna().sum():,}")

print(f"Invalid dates: {invalid_dates:,}")

print("\nTransaction Type Distribution:")
print(df["TransactionType"].value_counts())

print("\nAdditional Data Quality Checks:")
print("Zero-price records:", df["IsZeroPrice"].sum())
print("Negative-price records:", df["IsNegativePrice"].sum())
print("Potential return records:", df["IsReturnCandidate"].sum())

print("\nRevenue Summary:")
print(df["Revenue"].describe())

print("\nCleaned dataset saved successfully!")
print(f"Output location: {OUTPUT_PATH}")
