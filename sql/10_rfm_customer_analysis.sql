
-- =====================================================
-- RETAIL SALES ANALYTICS
-- ADVANCED SQL: RFM CUSTOMER ANALYSIS
-- =====================================================


-- QUERY 1: Customer segment distribution
-- Understand the number of customers in each segment.

SELECT
    "Customer_Segment",
    "Customer_Count",
    ROUND(
        "Customer_Count" * 100.0 /
        SUM("Customer_Count") OVER (),
        2
    ) AS customer_percentage
FROM rfm_segment_summary
ORDER BY "Customer_Count" DESC;


-- QUERY 2: Revenue contribution by customer segment
-- Identify the most valuable customer segments.

SELECT
    "Customer_Segment",
    "Customer_Count",
    ROUND("Total_Revenue", 2) AS total_revenue,
    ROUND(
        "Total_Revenue" * 100.0 /
        SUM("Total_Revenue") OVER (),
        2
    ) AS revenue_percentage,
    ROUND("Average_Monetary", 2) AS average_customer_value
FROM rfm_segment_summary
ORDER BY "Total_Revenue" DESC;


-- QUERY 3: Champions and loyal customers
-- Identify high-value customers for retention campaigns.

SELECT
    "CustomerID",
    "Recency",
    "Frequency",
    "Monetary",
    "RFM_Score",
    "Customer_Segment"
FROM customer_rfm
WHERE "Customer_Segment" IN (
    'Champions',
    'Loyal Customers'
)
ORDER BY
    "Monetary" DESC
LIMIT 20;


-- QUERY 4: At-risk and lost customers
-- Identify customers who may need re-engagement.

SELECT
    "CustomerID",
    "Recency",
    "Frequency",
    "Monetary",
    "RFM_Score",
    "Customer_Segment"
FROM customer_rfm
WHERE "Customer_Segment" IN (
    'At Risk',
    'Lost Customers'
)
ORDER BY
    "Recency" DESC,
    "Monetary" DESC
LIMIT 20;


-- QUERY 5: RFM score analysis
-- Compare customer value across RFM scores.

SELECT
    "RFM_Score",
    COUNT(*) AS customer_count,
    ROUND(AVG("Recency"), 2) AS average_recency,
    ROUND(AVG("Frequency"), 2) AS average_frequency,
    ROUND(AVG("Monetary"), 2) AS average_monetary,
    ROUND(SUM("Monetary"), 2) AS total_revenue
FROM customer_rfm
GROUP BY "RFM_Score"
ORDER BY "RFM_Score" DESC;
