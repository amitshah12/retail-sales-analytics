
import pandas as pd
from pathlib import Path
from sqlalchemy import text

from db_connection import engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

RFM_FILE = PROCESSED_DIR / "customer_rfm.csv"
SUMMARY_FILE = PROCESSED_DIR / "rfm_segment_summary.csv"


def load_rfm_data():
    print("Reading customer RFM dataset...")
    customer_df = pd.read_csv(RFM_FILE)

    print("Reading RFM segment summary...")
    summary_df = pd.read_csv(SUMMARY_FILE)

    print(f"Customer records: {len(customer_df):,}")
    print(f"Segment records: {len(summary_df):,}")

    print("\nRefreshing RFM tables...")

    # Both tables are refreshed in one transaction.
    # If an operation fails, the transaction is rolled back.
    with engine.begin() as connection:

        connection.execute(
            text("""
                TRUNCATE TABLE
                    customer_rfm,
                    rfm_segment_summary
            """)
        )

        customer_df.to_sql(
            "customer_rfm",
            connection,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=500
        )

        summary_df.to_sql(
            "rfm_segment_summary",
            connection,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=100
        )

        customer_count = connection.execute(
            text("SELECT COUNT(*) FROM customer_rfm")
        ).scalar_one()

        segment_count = connection.execute(
            text("SELECT COUNT(*) FROM rfm_segment_summary")
        ).scalar_one()

    print("\n========== IMPORT VERIFICATION ==========")
    print(f"Customer RFM records: {customer_count:,}")
    print(f"Segment summary records: {segment_count:,}")

    if customer_count == len(customer_df) and segment_count == len(summary_df):
        print("\nSUCCESS: Both RFM datasets imported successfully!")
    else:
        raise ValueError("Imported record counts do not match the CSV files.")


if __name__ == "__main__":
    try:
        load_rfm_data()
    except Exception as error:
        print(f"\nImport failed: {error}")
        raise
    finally:
        engine.dispose()
