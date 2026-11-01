from pathlib import Path
import os

import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# --------------------------------------------------
# 1. PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables from the project root.
load_dotenv(PROJECT_ROOT / ".env")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "retail_analytics")

required_variables = {
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_NAME": DB_NAME,
}

missing_variables = [
    name for name, value in required_variables.items()
    if not value
]

if missing_variables:
    raise ValueError(
        "Missing database environment variables: "
        + ", ".join(missing_variables)
    )

# URL.create safely handles special characters in passwords.
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME
)


# --------------------------------------------------
# 2. DATABASE CONNECTION
# --------------------------------------------------

print("Connecting to PostgreSQL...")

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    print("Database connection successful!")


    # --------------------------------------------------
    # 3. DATA RETRIEVAL
    # --------------------------------------------------

    def fetch_data(query):
        return pd.read_sql_query(text(query), engine)


    print("\nFetching monthly revenue...")

    monthly_revenue = fetch_data("""
        SELECT
            TO_CHAR("InvoiceDate", 'YYYY-MM') AS sales_month,
            ROUND(SUM("Revenue"), 2) AS monthly_revenue
        FROM retail_transactions
        WHERE "TransactionType" = 'Sale'
        GROUP BY TO_CHAR("InvoiceDate", 'YYYY-MM')
        ORDER BY sales_month;
    """)

    print("Fetching customer segments...")

    customer_segments = fetch_data("""
        SELECT
            "Customer_Segment",
            "Customer_Count"
        FROM rfm_segment_summary
        ORDER BY "Customer_Count" DESC;
    """)

    print("Fetching revenue by country...")

    country_revenue = fetch_data("""
        SELECT
            "Country",
            ROUND(SUM("Revenue"), 2) AS total_revenue
        FROM retail_transactions
        WHERE "TransactionType" = 'Sale'
        GROUP BY "Country"
        ORDER BY total_revenue DESC
        LIMIT 10;
    """)

    print("Fetching new and returning customers...")

    customer_activity = fetch_data("""
        WITH customer_first_purchase AS (
            SELECT
                "CustomerID",
                MIN(DATE_TRUNC('month', "InvoiceDate")) AS first_purchase_month
            FROM retail_transactions
            WHERE "TransactionType" = 'Sale'
              AND "CustomerID" IS NOT NULL
            GROUP BY "CustomerID"
        ),
        monthly_activity AS (
            SELECT
                DATE_TRUNC('month', t."InvoiceDate") AS sales_month,
                COUNT(DISTINCT t."CustomerID") AS active_customers,
                COUNT(DISTINCT t."CustomerID") FILTER (
                    WHERE DATE_TRUNC('month', t."InvoiceDate")
                        = f.first_purchase_month
                ) AS new_customers
            FROM retail_transactions t
            JOIN customer_first_purchase f
              ON t."CustomerID" = f."CustomerID"
            WHERE t."TransactionType" = 'Sale'
            GROUP BY DATE_TRUNC('month', t."InvoiceDate")
        )
        SELECT
            TO_CHAR(sales_month, 'YYYY-MM') AS sales_month,
            new_customers,
            active_customers - new_customers AS returning_customers,
            active_customers
        FROM monthly_activity
        ORDER BY sales_month;
    """)

    print("Fetching customer revenue contribution...")

    pareto_data = fetch_data("""
        WITH customer_revenue AS (
            SELECT
                "CustomerID",
                SUM("Revenue") AS total_revenue
            FROM retail_transactions
            WHERE "TransactionType" = 'Sale'
              AND "CustomerID" IS NOT NULL
            GROUP BY "CustomerID"
        ),
        ranked_customers AS (
            SELECT
                "CustomerID",
                total_revenue,
                SUM(total_revenue) OVER (
                    ORDER BY total_revenue DESC, "CustomerID"
                ) * 100.0
                / SUM(total_revenue) OVER () AS cumulative_revenue_percentage
            FROM customer_revenue
        )
        SELECT
            "CustomerID",
            total_revenue,
            cumulative_revenue_percentage
        FROM ranked_customers
        ORDER BY total_revenue DESC
        LIMIT 100;
    """)

    print("All datasets retrieved successfully!")


    # --------------------------------------------------
    # 4. CHART 1: MONTHLY REVENUE TREND
    # --------------------------------------------------

    plt.figure(figsize=(12, 6))

    plt.plot(
        monthly_revenue["sales_month"],
        monthly_revenue["monthly_revenue"],
        marker="o",
        linewidth=2
    )

    plt.title("Monthly Revenue Trend", fontsize=16)
    plt.xlabel("Month")
    plt.ylabel("Revenue")
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(REPORTS_DIR / "monthly_revenue.png", dpi=300)
    plt.close()


    # --------------------------------------------------
    # 5. CHART 2: CUSTOMER SEGMENT DISTRIBUTION
    # --------------------------------------------------

    plt.figure(figsize=(10, 6))

    plt.bar(
        customer_segments["Customer_Segment"],
        customer_segments["Customer_Count"]
    )

    plt.title("Customer Segment Distribution", fontsize=16)
    plt.xlabel("Customer Segment")
    plt.ylabel("Number of Customers")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    plt.savefig(REPORTS_DIR / "customer_segments.png", dpi=300)
    plt.close()


    # --------------------------------------------------
    # 6. CHART 3: REVENUE BY COUNTRY
    # --------------------------------------------------

    plt.figure(figsize=(12, 7))

    plt.barh(
        country_revenue["Country"][::-1],
        country_revenue["total_revenue"][::-1]
    )

    plt.title("Top 10 Countries by Revenue", fontsize=16)
    plt.xlabel("Revenue")
    plt.ylabel("Country")
    plt.tight_layout()

    plt.savefig(REPORTS_DIR / "revenue_by_country.png", dpi=300)
    plt.close()


    # --------------------------------------------------
    # 7. CHART 4: NEW VS RETURNING CUSTOMERS
    # --------------------------------------------------

    plt.figure(figsize=(12, 6))

    plt.plot(
        customer_activity["sales_month"],
        customer_activity["new_customers"],
        marker="o",
        label="New Customers"
    )

    plt.plot(
        customer_activity["sales_month"],
        customer_activity["returning_customers"],
        marker="o",
        label="Returning Customers"
    )

    plt.title("New vs Returning Customers", fontsize=16)
    plt.xlabel("Month")
    plt.ylabel("Number of Customers")
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        REPORTS_DIR / "customer_acquisition_retention.png",
        dpi=300
    )
    plt.close()


    # --------------------------------------------------
    # 8. CHART 5: CUSTOMER REVENUE PARETO ANALYSIS
    # --------------------------------------------------

    plt.figure(figsize=(12, 6))

    plt.plot(
        range(1, len(pareto_data) + 1),
        pareto_data["cumulative_revenue_percentage"],
        marker=".",
        linewidth=2
    )

    plt.axhline(
        y=80,
        linestyle="--",
        label="80% Revenue Threshold"
    )

    plt.title("Customer Revenue Pareto Analysis", fontsize=16)
    plt.xlabel("Customer Rank")
    plt.ylabel("Cumulative Revenue (%)")
    plt.ylim(0, 105)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        REPORTS_DIR / "customer_revenue_pareto.png",
        dpi=300
    )
    plt.close()


    # --------------------------------------------------
    # 9. COMPLETION
    # --------------------------------------------------

    print("\n========================================")
    print("VISUALIZATION COMPLETED SUCCESSFULLY!")
    print("========================================")

    print(f"\nCharts saved in: {REPORTS_DIR}")

    for chart in REPORTS_DIR.glob("*.png"):
        print(f" - {chart.name}")

finally:
    engine.dispose()
