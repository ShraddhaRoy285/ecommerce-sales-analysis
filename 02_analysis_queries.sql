-- =====================================================================
-- E-COMMERCE ANALYSIS QUERIES  (Joins, CTEs, Aggregations, Window Functions)
-- Business rule: Cancelled orders are excluded from revenue metrics.
-- =====================================================================

-- Q1. MONTHLY REVENUE & MONTH-OVER-MONTH GROWTH  (CTE + LAG window)
WITH monthly AS (
    SELECT order_month,
           ROUND(SUM(revenue), 2)  AS revenue,
           COUNT(DISTINCT order_id) AS orders
    FROM orders
    WHERE order_status <> 'Cancelled'
    GROUP BY order_month
)
SELECT order_month, revenue, orders,
       LAG(revenue) OVER (ORDER BY order_month) AS prev_month_revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY order_month))
             / LAG(revenue) OVER (ORDER BY order_month), 2) AS mom_growth_pct
FROM monthly
ORDER BY order_month;

-- Q2. CUSTOMER LIFETIME VALUE + RANK  (JOIN + CTE + DENSE_RANK)
WITH clv AS (
    SELECT c.customer_id,
           COUNT(o.order_id)          AS total_orders,
           ROUND(SUM(o.revenue), 2)   AS lifetime_value,
           ROUND(AVG(o.revenue), 2)   AS avg_order_value,
           c.first_order_date, c.last_order_date
    FROM customers c
    JOIN orders o ON o.customer_id = c.customer_id
    WHERE o.order_status <> 'Cancelled'
    GROUP BY c.customer_id
)
SELECT DENSE_RANK() OVER (ORDER BY lifetime_value DESC) AS clv_rank, *
FROM clv
ORDER BY clv_rank
LIMIT 20;

-- Q3. REPEAT ORDER RATE  (CTE + CASE)
WITH cust_orders AS (
    SELECT customer_id, COUNT(*) AS n_orders
    FROM orders WHERE order_status <> 'Cancelled'
    GROUP BY customer_id
)
SELECT COUNT(*)                                             AS total_customers,
       SUM(CASE WHEN n_orders > 1 THEN 1 ELSE 0 END)        AS repeat_customers,
       ROUND(100.0 * SUM(CASE WHEN n_orders > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_order_rate_pct,
       ROUND(AVG(n_orders), 2)                              AS avg_orders_per_customer
FROM cust_orders;

-- Q4. CUSTOMER SEGMENTS BY VALUE  (NTILE window)
WITH clv AS (
    SELECT customer_id, SUM(revenue) AS ltv, COUNT(*) AS orders
    FROM orders WHERE order_status <> 'Cancelled' GROUP BY customer_id
), tiles AS (
    SELECT *, NTILE(4) OVER (ORDER BY ltv DESC) AS quartile FROM clv
)
SELECT CASE quartile WHEN 1 THEN 'Top 25% (VIP)' WHEN 2 THEN 'Upper-mid'
                     WHEN 3 THEN 'Lower-mid' ELSE 'Bottom 25%' END AS segment,
       COUNT(*) AS customers,
       ROUND(SUM(ltv), 2) AS revenue,
       ROUND(100.0 * SUM(ltv) / (SELECT SUM(ltv) FROM clv), 2) AS pct_of_total_revenue
FROM tiles GROUP BY quartile ORDER BY quartile;

-- Q5. CATEGORY PROFITABILITY RANKING  (JOIN + aggregation + DENSE_RANK)
SELECT DENSE_RANK() OVER (ORDER BY SUM(o.profit) * 1.0 / SUM(o.revenue) DESC) AS margin_rank,
       p.product_category,
       ROUND(SUM(o.revenue), 2) AS revenue,
       ROUND(SUM(o.profit), 2)  AS profit,
       ROUND(100.0 * SUM(o.profit) / SUM(o.revenue), 2) AS profit_margin_pct
FROM orders o JOIN products p ON p.product_id = o.product_id
WHERE o.order_status <> 'Cancelled'
GROUP BY p.product_category
ORDER BY margin_rank;

-- Q6. TOP 3 PRODUCTS PER CATEGORY BY REVENUE  (DENSE_RANK PARTITION BY)
WITH prod AS (
    SELECT p.product_category, p.product_name,
           ROUND(SUM(o.revenue), 2) AS revenue,
           ROUND(100.0 * SUM(o.profit) / SUM(o.revenue), 2) AS margin_pct
    FROM orders o JOIN products p ON p.product_id = o.product_id
    WHERE o.order_status <> 'Cancelled'
    GROUP BY p.product_category, p.product_name
), ranked AS (
    SELECT *, DENSE_RANK() OVER (PARTITION BY product_category ORDER BY revenue DESC) AS rnk FROM prod
)
SELECT * FROM ranked WHERE rnk <= 3 ORDER BY product_category, rnk;

-- Q7. REGIONAL SALES DISTRIBUTION  (share of total via window SUM)
SELECT region,
       ROUND(SUM(revenue), 2) AS revenue,
       COUNT(DISTINCT order_id) AS orders,
       ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 2) AS revenue_share_pct
FROM orders WHERE order_status <> 'Cancelled'
GROUP BY region ORDER BY revenue DESC;

-- Q8. RETURN & CANCELLATION RATE BY CATEGORY  (conditional aggregation)
SELECT p.product_category,
       COUNT(*) AS total_orders,
       ROUND(100.0 * SUM(o.order_status = 'Returned')  / COUNT(*), 2) AS return_rate_pct,
       ROUND(100.0 * SUM(o.order_status = 'Cancelled') / COUNT(*), 2) AS cancel_rate_pct
FROM orders o JOIN products p ON p.product_id = o.product_id
GROUP BY p.product_category ORDER BY return_rate_pct DESC;

-- Q9. CUMULATIVE REVENUE (running total window)
WITH m AS (
    SELECT order_month, SUM(revenue) AS revenue FROM orders
    WHERE order_status <> 'Cancelled' GROUP BY order_month
)
SELECT order_month, ROUND(revenue,2) AS revenue,
       ROUND(SUM(revenue) OVER (ORDER BY order_month), 2) AS cumulative_revenue
FROM m ORDER BY order_month;
