-- ============================================================
-- Online Retail Sales Analysis — SQL Queries
-- Database: online_retail_sales.db
-- Open in DB Browser for SQLite → Execute SQL tab
-- ============================================================


-- 1. OVERALL SALES HEADLINE NUMBERS
-- Shows four (4) KPI numbers: total revenue, orders, customers, avg order value

SELECT
    ROUND(SUM(CAST(Revenue AS REAL)), 2)            AS total_revenue,
    COUNT(DISTINCT InvoiceNo)                        AS total_orders,
    COUNT(DISTINCT CustomerID)                       AS total_customers,
    ROUND(SUM(CAST(Revenue AS REAL))
          / COUNT(DISTINCT InvoiceNo), 2)            AS avg_order_value
FROM sales_clean
WHERE CustomerType = 'Registered';


-- 2. MONTHLY REVENUE TREND
-- Shows whether the business is growing month over month and where the seasonal peaks are.

SELECT
    MonthName,
    Year,
    Month,
    ROUND(CAST(Total_Revenue AS REAL), 2) AS Total_Revenue,
    Orders,
    Items_Sold
FROM monthly_revenue
ORDER BY Year, Month;


-- 3. REVENUE BY COUNTRY (top 10)
-- Shows which markets drive the most revenue and which are small but worth watching.

SELECT
    Country,
    ROUND(CAST(Total_Revenue AS REAL), 2) AS Total_Revenue,
    Orders,
    Customers
FROM revenue_by_country
ORDER BY CAST(Total_Revenue AS REAL) DESC
LIMIT 10;


-- 4. TOP 20 PRODUCTS BY REVENUE
-- Tells which specific products make the most money, the classic "80/20 rule" analysis (often top 20 products = 60-80% 
-- of revenue)

SELECT
    Description,
    ROUND(CAST(Total_Revenue AS REAL), 2) AS Total_Revenue,
    Units_Sold,
    Times_Ordered
FROM top_products
ORDER BY CAST(Total_Revenue AS REAL) DESC;


-- 5. CUSTOMER SEGMENT BREAKDOWN
-- Shows the "Champions" vs "At Risk" vs "Lost" customers. This is a standard RFM segmentation result that tells 
-- sales/marketing where to focus their energy

SELECT
    Segment,
    COUNT(*) AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_customers,
    ROUND(AVG(CAST(Monetary AS REAL)), 2) AS avg_spend
FROM customer_segments
GROUP BY Segment
ORDER BY avg_spend DESC;


-- 6. CONVERSION FUNNEL
-- What this tells you: out of all orders placed, how many had actual revenue, and how many customers came back 
-- to buy again?

SELECT Stage, Count, Pct_of_Top
FROM conversion_funnel
ORDER BY Stage;


-- 7. CANCELLATION RATE ANALYSIS
-- This shows which countries or months have the highest cancellation rates 
-- This is actionable for a sales/ops team

SELECT
    Country,
    COUNT(*) AS cancellation_rows
FROM cancellations
GROUP BY Country
ORDER BY cancellation_rows DESC
LIMIT 10;


-- 8. WHAT CLEANING REMOVED AND WHY
-- This shows my full data cleaning audit trail, the same story the cleaning_log table tells, but in SQL form

SELECT step, rows_removed, reason
FROM cleaning_log
ORDER BY rows_removed DESC;
