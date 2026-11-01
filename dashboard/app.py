from datetime import timedelta

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text, bindparam


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Retail Sales Analytics",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Retail Sales & Customer Analytics")
st.caption(
    "Interactive business intelligence dashboard | UCI Online Retail Dataset"
)

st.divider()


# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

# Keep these credentials consistent with your existing setup.
# Do not commit database passwords to a public GitHub repository.


import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
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

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL)


@st.cache_data(ttl=300)
def fetch_data(query, params=None, expanding_params=None):
    engine = get_engine()
    statement = text(query)

    if expanding_params:
        for parameter in expanding_params:
            statement = statement.bindparams(
                bindparam(parameter, expanding=True)
            )

    with engine.connect() as connection:
        return pd.read_sql_query(
            statement,
            connection,
            params=params or {}
        )


# --------------------------------------------------
# DATABASE CONNECTION CHECK
# --------------------------------------------------

try:
    engine = get_engine()

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

except Exception as error:
    st.error("Unable to connect to PostgreSQL.")
    st.exception(error)
    st.stop()


# --------------------------------------------------
# FILTER OPTIONS
# --------------------------------------------------

@st.cache_data(ttl=300)
def get_date_bounds():
    result = fetch_data("""
        SELECT
            MIN("InvoiceDate")::date AS min_date,
            MAX("InvoiceDate")::date AS max_date
        FROM retail_transactions
        WHERE "TransactionType" = 'Sale';
    """)

    min_date = pd.to_datetime(result.iloc[0]["min_date"]).date()
    max_date = pd.to_datetime(result.iloc[0]["max_date"]).date()

    return min_date, max_date


@st.cache_data(ttl=300)
def get_countries():
    result = fetch_data("""
        SELECT DISTINCT "Country"
        FROM retail_transactions
        WHERE "TransactionType" = 'Sale'
          AND "Country" IS NOT NULL
        ORDER BY "Country";
    """)

    return result["Country"].tolist()


try:
    min_date, max_date = get_date_bounds()
    available_countries = get_countries()

except Exception as error:
    st.error("Unable to load dashboard filter options.")
    st.exception(error)
    st.stop()


# --------------------------------------------------
# INTERACTIVE FILTERS
# --------------------------------------------------

st.subheader("Dashboard Filters")

filter_col1, filter_col2 = st.columns([1, 2])

with filter_col1:
    selected_dates = st.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        format="YYYY-MM-DD"
    )

with filter_col2:
    selected_countries = st.multiselect(
        "Select Countries",
        options=available_countries,
        default=available_countries,
        help=(
            "All countries are selected by default. "
            "Deselect countries to filter the dashboard."
        )
    )

if len(selected_dates) != 2:
    st.info("Please select both a start date and an end date.")
    st.stop()

start_date, end_date = selected_dates

if start_date > end_date:
    st.warning("The start date cannot be after the end date.")
    st.stop()

if not selected_countries:
    st.warning("Please select at least one country.")
    st.stop()


# --------------------------------------------------
# BUILD FILTERED SQL CONDITIONS
# --------------------------------------------------

end_date_exclusive = end_date + timedelta(days=1)

filter_conditions = """
    "TransactionType" = 'Sale'
    AND "InvoiceDate" >= :start_date
    AND "InvoiceDate" < :end_date_exclusive
    AND "Country" IN :countries
"""

filter_params = {
    "start_date": start_date,
    "end_date_exclusive": end_date_exclusive,
    "countries": selected_countries
}

expanding_params = ["countries"]


# --------------------------------------------------
# KPI DATA
# --------------------------------------------------

@st.cache_data(ttl=300)
def get_kpis(query, params, expanding):
    return fetch_data(query, params, expanding)


# --------------------------------------------------
# LOAD FILTERED BUSINESS DATA
# --------------------------------------------------

try:

    kpis = get_kpis(
        f"""
        SELECT
            COUNT(DISTINCT "InvoiceNo") AS total_orders,
            COUNT(DISTINCT "CustomerID") AS total_customers,
            COALESCE(SUM("Quantity"), 0) AS total_quantity_sold,
            ROUND(COALESCE(SUM("Revenue"), 0), 2) AS total_revenue,
            ROUND(
                COALESCE(SUM("Revenue"), 0) /
                NULLIF(COUNT(DISTINCT "InvoiceNo"), 0),
                2
            ) AS average_order_value
        FROM retail_transactions
        WHERE {filter_conditions};
        """,
        filter_params,
        expanding_params
    )

    monthly_revenue = fetch_data(
        f"""
        SELECT
            TO_CHAR("InvoiceDate", 'YYYY-MM') AS sales_month,
            ROUND(SUM("Revenue"), 2) AS monthly_revenue
        FROM retail_transactions
        WHERE {filter_conditions}
        GROUP BY TO_CHAR("InvoiceDate", 'YYYY-MM')
        ORDER BY sales_month;
        """,
        filter_params,
        expanding_params
    )

    country_revenue = fetch_data(
        f"""
        SELECT
            "Country",
            ROUND(SUM("Revenue"), 2) AS total_revenue
        FROM retail_transactions
        WHERE {filter_conditions}
        GROUP BY "Country"
        ORDER BY total_revenue DESC
        LIMIT 10;
        """,
        filter_params,
        expanding_params
    )

except Exception as error:
    st.error("Unable to retrieve filtered dashboard data.")
    st.exception(error)
    st.stop()


# --------------------------------------------------
# FILTER SUMMARY
# --------------------------------------------------

st.caption(
    f"Showing sales from {start_date.strftime('%d %b %Y')} "
    f"to {end_date.strftime('%d %b %Y')} "
    f"across {len(selected_countries)} selected countries."
)


# --------------------------------------------------
# BUSINESS OVERVIEW KPI CARDS
# --------------------------------------------------

st.subheader("Business Overview")

row = kpis.iloc[0]

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Total Revenue",
    f"£{row['total_revenue'] / 1_000_000:.2f}M"
)

col2.metric(
    "Total Orders",
    f"{int(row['total_orders']):,}"
)

col3.metric(
    "Unique Customers",
    f"{int(row['total_customers']):,}"
)

col4.metric(
    "Quantity Sold",
    f"{int(row['total_quantity_sold']):,}"
)

average_order_value = row["average_order_value"]

col5.metric(
    "Average Order Value",
    f"£{average_order_value:,.2f}"
    if pd.notna(average_order_value)
    else "£0.00"
)


st.divider()


# --------------------------------------------------
# MONTHLY REVENUE CHART
# --------------------------------------------------

st.subheader("Monthly Revenue Trend")

if not monthly_revenue.empty:

    st.line_chart(
        monthly_revenue,
        x="sales_month",
        y="monthly_revenue",
        x_label="Month",
        y_label="Revenue (£)",
        width="stretch"
    )

else:
    st.info("No monthly revenue data is available for these filters.")


st.divider()


# --------------------------------------------------
# COUNTRY REVENUE CHART
# --------------------------------------------------

st.subheader("Top 10 Countries by Revenue")

if not country_revenue.empty:

    st.bar_chart(
        country_revenue,
        x="Country",
        y="total_revenue",
        x_label="Country",
        y_label="Revenue (£)",
        horizontal=True,
        width="stretch"
    )

else:
    st.info("No country revenue data is available for these filters.")


st.divider()


# ==================================================
# RFM CUSTOMER ANALYTICS
# ==================================================

st.header("👥 Customer Segmentation & RFM Analysis")

st.caption(
    "Understand customer purchasing behaviour using "
    "Recency, Frequency and Monetary analysis."
)

st.info(
    "RFM metrics are calculated from the complete dataset. "
    "They are independent of the date and country filters above."
)


# --------------------------------------------------
# LOAD RFM SEGMENT DATA
# --------------------------------------------------

@st.cache_data(ttl=300)
def get_rfm_segment_summary():

    return fetch_data("""
        SELECT
            "Customer_Segment",
            COUNT(*) AS customer_count,
            ROUND(SUM("Monetary"), 2) AS total_revenue,
            ROUND(AVG("Monetary"), 2) AS average_customer_value,
            ROUND(AVG("Recency"), 2) AS average_recency,
            ROUND(AVG("Frequency"), 2) AS average_frequency
        FROM customer_rfm
        GROUP BY "Customer_Segment"
        ORDER BY customer_count DESC;
    """)


@st.cache_data(ttl=300)
def get_rfm_customers():

    return fetch_data("""
        SELECT
            "CustomerID",
            "Recency",
            "Frequency",
            "Monetary",
            "RFM_Score",
            "Customer_Segment"
        FROM customer_rfm
        ORDER BY "Monetary" DESC;
    """)


try:

    rfm_summary = get_rfm_segment_summary()
    rfm_customers = get_rfm_customers()

except Exception as error:

    st.error("Unable to retrieve RFM customer analytics.")
    st.exception(error)
    st.stop()


if rfm_summary.empty or rfm_customers.empty:

    st.warning("No RFM customer data is currently available.")

else:

    # ----------------------------------------------
    # RFM OVERVIEW
    # ----------------------------------------------

    total_rfm_customers = int(
        rfm_summary["customer_count"].sum()
    )

    total_rfm_revenue = float(
        rfm_summary["total_revenue"].sum()
    )

    average_customer_value = (
        total_rfm_revenue / total_rfm_customers
        if total_rfm_customers > 0
        else 0
    )

    segment_count = len(rfm_summary)

    rfm_col1, rfm_col2, rfm_col3, rfm_col4 = st.columns(4)

    rfm_col1.metric(
        "RFM Customers",
        f"{total_rfm_customers:,}"
    )

    rfm_col2.metric(
        "Customer Segments",
        f"{segment_count:,}"
    )

    rfm_col3.metric(
        "RFM Revenue",
        f"£{total_rfm_revenue:,.2f}"
    )

    rfm_col4.metric(
        "Average Customer Value",
        f"£{average_customer_value:,.2f}"
    )

    st.divider()

    # ----------------------------------------------
    # CUSTOMER SEGMENT DISTRIBUTION
    # ----------------------------------------------

    st.subheader("Customer Distribution by Segment")

    segment_chart_data = rfm_summary[
        ["Customer_Segment", "customer_count"]
    ].copy()

    segment_chart_data = segment_chart_data.set_index(
        "Customer_Segment"
    )

    st.bar_chart(
        segment_chart_data,
        horizontal=True,
        x_label="Number of Customers",
        y_label="Customer Segment",
        width="stretch"
    )

    st.divider()

    # ----------------------------------------------
    # REVENUE CONTRIBUTION BY SEGMENT
    # ----------------------------------------------

    st.subheader("Revenue Contribution by Segment")

    revenue_chart_data = rfm_summary[
        ["Customer_Segment", "total_revenue"]
    ].copy()

    revenue_chart_data = revenue_chart_data.set_index(
        "Customer_Segment"
    )

    st.bar_chart(
        revenue_chart_data,
        horizontal=True,
        x_label="Revenue (£)",
        y_label="Customer Segment",
        width="stretch"
    )

    # ----------------------------------------------
    # SEGMENT SUMMARY TABLE
    # ----------------------------------------------

    st.subheader("Customer Segment Performance")

    segment_display = rfm_summary.copy()

    segment_display["revenue_percentage"] = (
        segment_display["total_revenue"]
        / total_rfm_revenue * 100
        if total_rfm_revenue > 0
        else 0
    )

    segment_display = segment_display.rename(
        columns={
            "Customer_Segment": "Customer Segment",
            "customer_count": "Customer Count",
            "total_revenue": "Total Revenue (£)",
            "average_customer_value": "Average Customer Value (£)",
            "average_recency": "Average Recency (Days)",
            "average_frequency": "Average Frequency",
            "revenue_percentage": "Revenue Contribution (%)"
        }
    )

    st.dataframe(
        segment_display.style.format({
            "Total Revenue (£)": "£{:,.2f}",
            "Average Customer Value (£)": "£{:,.2f}",
            "Average Recency (Days)": "{:.2f}",
            "Average Frequency": "{:.2f}",
            "Revenue Contribution (%)": "{:.2f}%"
        }),
        width="stretch",
        hide_index=True
    )


    # ----------------------------------------------
    # CUSTOMER BUSINESS INSIGHTS
    # ----------------------------------------------

    st.divider()

    st.subheader("💡 Customer Business Insights")

    # Highest revenue segment
    highest_revenue_segment = rfm_summary.loc[
        rfm_summary["total_revenue"].idxmax()
    ]

    # Largest customer segment
    largest_segment = rfm_summary.loc[
        rfm_summary["customer_count"].idxmax()
    ]

    # Highest average customer value
    highest_value_segment = rfm_summary.loc[
        rfm_summary["average_customer_value"].idxmax()
    ]

    # At-risk and lost customer percentage
    risk_segments = ["At Risk", "Lost Customers"]

    risk_customer_count = int(
        rfm_summary.loc[
            rfm_summary["Customer_Segment"].isin(risk_segments),
            "customer_count"
        ].sum()
    )

    risk_percentage = (
        risk_customer_count / total_rfm_customers * 100
        if total_rfm_customers > 0
        else 0
    )

    # Display insight cards
    insight_col1, insight_col2 = st.columns(2)

    with insight_col1:

        st.markdown("#### 🏆 Highest Revenue Segment")

        st.metric(
            label=highest_revenue_segment["Customer_Segment"],
            value=f"£{highest_revenue_segment['total_revenue']:,.2f}",
            delta=(
                f"{highest_revenue_segment['total_revenue'] / total_rfm_revenue * 100:.2f}% "
                "of RFM revenue"
                if total_rfm_revenue > 0
                else None
            )
        )

        st.markdown("#### 👥 Largest Customer Segment")

        st.metric(
            label=largest_segment["Customer_Segment"],
            value=f"{int(largest_segment['customer_count']):,} customers",
            delta=(
                f"{largest_segment['customer_count'] / total_rfm_customers * 100:.2f}% "
                "of customers"
            )
            if total_rfm_customers > 0
            else None
        )

    with insight_col2:

        st.markdown("#### 💰 Highest Average Customer Value")

        st.metric(
            label=highest_value_segment["Customer_Segment"],
            value=f"£{highest_value_segment['average_customer_value']:,.2f}",
            delta="Average revenue per customer"
        )

        st.markdown("#### ⚠️ At-Risk & Lost Customers")

        st.metric(
            label="Customers requiring attention",
            value=f"{risk_customer_count:,}",
            delta=f"{risk_percentage:.2f}% of all RFM customers",
            delta_color="inverse"
        )

    # Business recommendations
    st.markdown("#### 📌 Suggested Business Actions")

    st.markdown(
        f"""
        - **Revenue:** Focus on retaining
          **{highest_revenue_segment['Customer_Segment']}**
          customers because this segment generates the highest revenue.

        - **Customer retention:** Develop targeted engagement campaigns
          for **{risk_customer_count:,} At Risk and Lost Customers**.

        - **Customer loyalty:** Build loyalty and repeat-purchase
          campaigns around your highest-value customer segment:
          **{highest_value_segment['Customer_Segment']}**.

        - **Customer acquisition:** Study the characteristics of
          **{largest_segment['Customer_Segment']}** customers to
          understand what attracts customers to this segment.
        """
    )


    st.divider()

    # ----------------------------------------------
    # CUSTOMER SEGMENT FILTER
    # ----------------------------------------------

    st.subheader("Explore Individual Customers")

    available_segments = sorted(
        rfm_customers["Customer_Segment"].dropna().unique().tolist()
    )

    selected_segment = st.selectbox(
        "Select Customer Segment",
        options=["All Segments"] + available_segments
    )

    if selected_segment == "All Segments":

        filtered_rfm = rfm_customers.copy()

    else:

        filtered_rfm = rfm_customers[
            rfm_customers["Customer_Segment"] == selected_segment
        ].copy()

    st.caption(
        f"Displaying {len(filtered_rfm):,} customers."
    )

    customer_display = filtered_rfm.rename(
        columns={
            "CustomerID": "Customer ID",
            "Recency": "Recency (Days)",
            "Frequency": "Purchase Frequency",
            "Monetary": "Monetary Value (£)",
            "RFM_Score": "RFM Score",
            "Customer_Segment": "Customer Segment"
        }
    )

    st.dataframe(
        customer_display.style.format({
            "Monetary Value (£)": "£{:,.2f}"
        }),
        width="stretch",
        hide_index=True
    )

    # ----------------------------------------------
    # AT-RISK AND LOST CUSTOMERS
    # ----------------------------------------------

    st.divider()

    st.subheader("⚠️ At-Risk & Lost Customers")

    risk_segments = [
        segment
        for segment in ["At Risk", "Lost Customers"]
        if segment in available_segments
    ]

    if risk_segments:

        risk_customers = rfm_customers[
            rfm_customers["Customer_Segment"].isin(risk_segments)
        ].copy()

        risk_col1, risk_col2 = st.columns(2)

        at_risk_count = int(
            (risk_customers["Customer_Segment"] == "At Risk").sum()
        )

        lost_count = int(
            (risk_customers["Customer_Segment"] == "Lost Customers").sum()
        )

        risk_col1.metric(
            "At-Risk Customers",
            f"{at_risk_count:,}"
        )

        risk_col2.metric(
            "Lost Customers",
            f"{lost_count:,}"
        )

        st.dataframe(
            risk_customers.rename(
                columns={
                    "CustomerID": "Customer ID",
                    "Recency": "Recency (Days)",
                    "Frequency": "Purchase Frequency",
                    "Monetary": "Monetary Value (£)",
                    "RFM_Score": "RFM Score",
                    "Customer_Segment": "Customer Segment"
                }
            ).style.format({
                "Monetary Value (£)": "£{:,.2f}"
            }),
            width="stretch",
            hide_index=True
        )

    else:

        st.info(
            "No At Risk or Lost Customers segments were found."
        )


st.divider()


# --------------------------------------------------
# DATA PREVIEW
# --------------------------------------------------

with st.expander("View Monthly Revenue Data"):

    st.dataframe(
        monthly_revenue,
        width="stretch",
        hide_index=True
    )


with st.expander("View Country Revenue Data"):

    st.dataframe(
        country_revenue,
        width="stretch",
        hide_index=True
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Data source: UCI Machine Learning Repository — Online Retail Dataset"
)

st.caption(
    "Built with Python, Pandas, PostgreSQL, SQLAlchemy and Streamlit."
)
