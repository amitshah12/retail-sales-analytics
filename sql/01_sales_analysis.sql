-- Query 1 — Overall business KPIs
SELECT
    COUNT(DISTINCT "InvoiceNo") AS total_orders,
    COUNT(DISTINCT "CustomerID") AS identified_customers,
    SUM("Quantity") AS total_quantity_sold,
    ROUND(SUM("Revenue"), 2) AS total_revenue,
    ROUND(
        SUM("Revenue") / COUNT(DISTINCT "InvoiceNo"),
        2
    ) AS average_order_value
FROM retail_transactions
WHERE "TransactionType" = 'Sale';


-- Query 2 — Monthly revenue and order trends
SELECT
    TO_CHAR("InvoiceDate", 'YYYY-MM') AS sales_month,
    COUNT(DISTINCT "InvoiceNo") AS total_orders,
    SUM("Quantity") AS quantity_sold,
    ROUND(SUM("Revenue"), 2) AS monthly_revenue
FROM retail_transactions
WHERE "TransactionType" = 'Sale'
GROUP BY TO_CHAR("InvoiceDate", 'YYYY-MM')
ORDER BY sales_month;

-- Query 3 — Top 10 products by revenue
SELECT
    "StockCode",
    "Description",
    SUM("Quantity") AS quantity_sold,
    ROUND(SUM("Revenue"), 2) AS total_revenue
FROM retail_transactions
WHERE "TransactionType" = 'Sale'
GROUP BY "StockCode", "Description"
ORDER BY total_revenue DESC
LIMIT 10;

-- Query 4 — Top 10 countries by revenue
SELECT
    "Country",
    COUNT(DISTINCT "InvoiceNo") AS total_orders,
    ROUND(SUM("Revenue"), 2) AS total_revenue,
    ROUND(
        SUM("Revenue") * 100.0 /
        SUM(SUM("Revenue")) OVER (),
        2
    ) AS revenue_percentage
FROM retail_transactions
WHERE "TransactionType" = 'Sale'
GROUP BY "Country"
ORDER BY total_revenue DESC
LIMIT 10;

-- Query 5 — Top 10 customers by revenue
SELECT
    "CustomerID",
    COUNT(DISTINCT "InvoiceNo") AS total_orders,
    SUM("Quantity") AS quantity_purchased,
    ROUND(SUM("Revenue"), 2) AS total_revenue
FROM retail_transactions
WHERE
    "TransactionType" = 'Sale'
    AND "CustomerID" IS NOT NULL
GROUP BY "CustomerID"
ORDER BY total_revenue DESC
LIMIT 10;

-- Query 6 — Cancellation and return analysis
SELECT
    "TransactionType",
    COUNT(*) AS total_records,
    COUNT(DISTINCT "InvoiceNo") AS total_invoices,
    SUM("Quantity") AS total_quantity,
    ROUND(SUM("Revenue"), 2) AS total_transaction_value
FROM retail_transactions
GROUP BY "TransactionType"
ORDER BY total_records DESC;

-- Query 7 — Monthly revenue ranking ->This query demonstrates SQL window functions.
WITH monthly_sales AS (
    SELECT
        DATE_TRUNC('month', "InvoiceDate") AS sales_month,
        SUM("Revenue") AS revenue
    FROM retail_transactions
    WHERE "TransactionType" = 'Sale'
    GROUP BY DATE_TRUNC('month', "InvoiceDate")
)

SELECT
    TO_CHAR(sales_month, 'YYYY-MM') AS sales_month,
    ROUND(revenue, 2) AS revenue,
    RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
FROM monthly_sales
ORDER BY revenue_rank;

-- Query 8 — Customer purchase frequency
WITH customer_orders AS (
    SELECT
        "CustomerID",
        COUNT(DISTINCT "InvoiceNo") AS total_orders
    FROM retail_transactions
    WHERE
        "TransactionType" = 'Sale'
        AND "CustomerID" IS NOT NULL
    GROUP BY "CustomerID"
)

SELECT
    CASE
        WHEN total_orders = 1 THEN 'One-time Customer'
        WHEN total_orders BETWEEN 2 AND 5 THEN '2-5 Orders'
        WHEN total_orders BETWEEN 6 AND 10 THEN '6-10 Orders'
        ELSE '10+ Orders'
    END AS customer_category,
    COUNT(*) AS customer_count
FROM customer_orders
GROUP BY customer_category
ORDER BY customer_count DESC;

