
-- =====================================================
-- ADVANCED BUSINESS ANALYSIS
-- CTEs, WINDOW FUNCTIONS AND CUSTOMER ANALYTICS
-- =====================================================


-- QUERY 1: Rank customers by revenue
WITH customer_revenue AS (
    SELECT
        "CustomerID",
        COUNT(DISTINCT "InvoiceNo") AS total_orders,
        ROUND(SUM("Revenue"), 2) AS total_revenue
    FROM retail_transactions
    WHERE "TransactionType" = 'Sale'
      AND "CustomerID" IS NOT NULL
    GROUP BY "CustomerID"
)
SELECT
    "CustomerID",
    total_orders,
    total_revenue,
    RANK() OVER (
        ORDER BY total_revenue DESC
    ) AS revenue_rank
FROM customer_revenue
ORDER BY revenue_rank
LIMIT 20;


-- QUERY 2: Month-over-month revenue growth
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', "InvoiceDate") AS sales_month,
        SUM("Revenue") AS revenue
    FROM retail_transactions
    WHERE "TransactionType" = 'Sale'
    GROUP BY DATE_TRUNC('month', "InvoiceDate")
),
revenue_comparison AS (
    SELECT
        sales_month,
        revenue,
        LAG(revenue) OVER (
            ORDER BY sales_month
        ) AS previous_month_revenue
    FROM monthly_revenue
)
SELECT
    TO_CHAR(sales_month, 'YYYY-MM') AS sales_month,
    ROUND(revenue, 2) AS monthly_revenue,
    ROUND(previous_month_revenue, 2) AS previous_month_revenue,
    ROUND(
        (revenue - previous_month_revenue) * 100.0 /
        NULLIF(previous_month_revenue, 0),
        2
    ) AS growth_percentage
FROM revenue_comparison
ORDER BY sales_month;


-- QUERY 3: Running cumulative revenue
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', "InvoiceDate") AS sales_month,
        SUM("Revenue") AS revenue
    FROM retail_transactions
    WHERE "TransactionType" = 'Sale'
    GROUP BY DATE_TRUNC('month', "InvoiceDate")
)
SELECT
    TO_CHAR(sales_month, 'YYYY-MM') AS sales_month,
    ROUND(revenue, 2) AS monthly_revenue,
    ROUND(
        SUM(revenue) OVER (
            ORDER BY sales_month
            ROWS BETWEEN UNBOUNDED PRECEDING
            AND CURRENT ROW
        ),
        2
    ) AS cumulative_revenue
FROM monthly_revenue
ORDER BY sales_month;


-- QUERY 4: Customer revenue contribution and Pareto ranking
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
            ORDER BY total_revenue DESC
            ROWS BETWEEN UNBOUNDED PRECEDING
            AND CURRENT ROW
        ) AS cumulative_revenue,
        SUM(total_revenue) OVER () AS overall_revenue
    FROM customer_revenue
)
SELECT
    "CustomerID",
    ROUND(total_revenue, 2) AS total_revenue,
    ROUND(
        cumulative_revenue * 100.0 /
        NULLIF(overall_revenue, 0),
        2
    ) AS cumulative_revenue_percentage
FROM ranked_customers
ORDER BY total_revenue DESC
LIMIT 30;


-- QUERY 5: Monthly new versus returning customers
WITH customer_first_purchase AS (
    SELECT
        "CustomerID",
        MIN(DATE_TRUNC('month', "InvoiceDate")) AS first_purchase_month
    FROM retail_transactions
    WHERE "TransactionType" = 'Sale'
      AND "CustomerID" IS NOT NULL
    GROUP BY "CustomerID"
),
monthly_customer_activity AS (
    SELECT DISTINCT
        DATE_TRUNC('month', "InvoiceDate") AS sales_month,
        "CustomerID"
    FROM retail_transactions
    WHERE "TransactionType" = 'Sale'
      AND "CustomerID" IS NOT NULL
)
SELECT
    TO_CHAR(m.sales_month, 'YYYY-MM') AS sales_month,
    COUNT(*) FILTER (
        WHERE f.first_purchase_month = m.sales_month
    ) AS new_customers,
    COUNT(*) FILTER (
        WHERE f.first_purchase_month < m.sales_month
    ) AS returning_customers,
    COUNT(*) AS active_customers
FROM monthly_customer_activity m
JOIN customer_first_purchase f
    ON m."CustomerID" = f."CustomerID"
GROUP BY m.sales_month
ORDER BY m.sales_month;
