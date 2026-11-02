"""Load cleaned CSV into SQLite, execute every query in sql/02_analysis_queries.sql,
and export each result to data/query_results/qN_*.csv"""
import sqlite3, pandas as pd, os, re
os.makedirs("data/query_results", exist_ok=True)
df = pd.read_csv("data/cleaned/ecommerce_cleaned.csv")
con = sqlite3.connect("data/ecommerce.db")
con.executescript(open("sql/01_schema.sql").read())

products = df[["product_name","product_category"]].drop_duplicates().reset_index(drop=True)
products.insert(0, "product_id", products.index + 1)
cust = df.groupby("customer_id")["order_date"].agg(first_order_date="min", last_order_date="max").reset_index()
orders = df.merge(products, on=["product_name","product_category"])[
    ["order_id","customer_id","product_id","order_date","order_month","region","payment_method",
     "order_status","quantity","unit_price","discount_pct","revenue","total_cost","profit"]]
cust.to_sql("customers", con, if_exists="append", index=False)
products.to_sql("products", con, if_exists="append", index=False)
orders.to_sql("orders", con, if_exists="append", index=False)
print("Loaded:", len(cust), "customers,", len(products), "products,", len(orders), "orders")

sql = open("sql/02_analysis_queries.sql").read()
blocks = [b for b in re.split(r"-- Q(\d+)\.", sql)[1:]]
for i in range(0, len(blocks), 2):
    num, body = blocks[i], blocks[i+1]
    title = body.split("\n")[0].strip()
    query = "\n".join(l for l in body.split("\n")[1:] if not l.strip().startswith("--")).strip().rstrip(";")
    res = pd.read_sql_query(query, con)
    res.to_csv(f"data/query_results/q{num}.csv", index=False)
    print(f"\n=== Q{num}: {title}\n{res.head(8).to_string(index=False)}")
con.close()
