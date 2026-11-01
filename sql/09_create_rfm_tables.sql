-- ============================================
-- RFM CUSTOMER ANALYSIS
-- Create tables for customer-level RFM data
-- ============================================

DROP TABLE IF EXISTS customer_rfm;

CREATE TABLE customer_rfm (
    "CustomerID" VARCHAR(20) PRIMARY KEY,
    "Recency" INTEGER NOT NULL,
    "Frequency" INTEGER NOT NULL,
    "Monetary" NUMERIC(14, 2) NOT NULL,
    "R_Score" INTEGER NOT NULL,
    "F_Score" INTEGER NOT NULL,
    "M_Score" INTEGER NOT NULL,
    "RFM_Score" VARCHAR(3) NOT NULL,
    "Customer_Segment" VARCHAR(50) NOT NULL
);

DROP TABLE IF EXISTS rfm_segment_summary;

CREATE TABLE rfm_segment_summary (
    "Customer_Segment" VARCHAR(50) PRIMARY KEY,
    "Customer_Count" INTEGER,
    "Average_Recency" NUMERIC(12, 2),
    "Average_Frequency" NUMERIC(12, 2),
    "Average_Monetary" NUMERIC(14, 2),
    "Total_Revenue" NUMERIC(16, 2)
);