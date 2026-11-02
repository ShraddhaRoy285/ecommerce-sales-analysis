"""Data preprocessing & cleaning with Pandas.
Input : data/raw/ecommerce_raw.csv
Output: data/cleaned/ecommerce_cleaned.csv  + data/cleaned/cleaning_report.txt"""
import re, pandas as pd, numpy as np

raw = pd.read_csv("data/raw/ecommerce_raw.csv")
log = [f"Raw rows: {len(raw):,}"]
df = raw.copy()

# 1. Duplicates -------------------------------------------------------------
n = len(df); df = df.drop_duplicates(); log.append(f"Exact duplicate rows removed: {n-len(df):,}")
n = len(df); df = df.drop_duplicates(subset="order_id"); log.append(f"Duplicate order_ids removed: {n-len(df):,}")

# 2. Standardise text columns -------------------------------------------------
df["product_category"] = df["product_category"].str.strip().str.title().replace({"Home & Kitchen": "Home & Kitchen"})
df["region"] = df["region"].str.strip().str.title().replace({"North-East": "North-East"})
df["region"] = df["region"].fillna("Unknown")
df["payment_method"] = df["payment_method"].fillna("Unknown")
log.append("Text standardised (strip / title-case) for category & region")

# 3. Fix mixed date formats ---------------------------------------------------
def parse_date(s):
    s = str(s).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):   return pd.to_datetime(s, format="%Y-%m-%d")
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", s):   return pd.to_datetime(s, format="%d/%m/%Y")
    if re.fullmatch(r"\d{2}-[A-Za-z]{3}-\d{4}", s): return pd.to_datetime(s, format="%d-%b-%Y")
    if re.fullmatch(r"\d{2}-\d{2}-\d{4}", s):   return pd.to_datetime(s, format="%m-%d-%Y")
    return pd.NaT
df["order_date"] = df["order_date"].apply(parse_date)
bad = df["order_date"].isna().sum(); df = df.dropna(subset=["order_date"])
log.append(f"Dates converted to datetime (4 formats unified); unparseable dropped: {bad}")

# 4. Missing values -----------------------------------------------------------
n = len(df); df = df.dropna(subset=["customer_id"]); log.append(f"Rows with missing customer_id dropped: {n-len(df)}")
df["discount_pct"] = df["discount_pct"].fillna(0)
df.loc[df["unit_price"] <= 0, "unit_price"] = np.nan                      # negatives are invalid
log.append(f"Invalid (<=0) prices set to NaN for imputation: {df['unit_price'].isna().sum()} total NaN prices")
prod_med_price = df.groupby("product_name")["unit_price"].transform("median")
df["unit_price"] = df["unit_price"].fillna(prod_med_price)
df["quantity"] = df["quantity"].fillna(df.groupby("product_name")["quantity"].transform("median")).round().astype(int)
log.append("Missing quantity / unit_price imputed with product-level median; missing discount -> 0; region/payment -> 'Unknown'")

# 5. Outliers -----------------------------------------------------------------
n = len(df)
price_ratio = df["unit_price"] / df.groupby("product_name")["unit_price"].transform("median")
df = df[(price_ratio < 3) & (df["quantity"] <= 10)]
log.append(f"Outliers removed (price >3x product median OR quantity >10): {n-len(df)}")

# 6. Feature engineering ------------------------------------------------------
df["revenue"] = (df["quantity"] * df["unit_price"] * (1 - df["discount_pct"]/100)).round(2)
df["total_cost"] = (df["quantity"] * df["cost_price"]).round(2)
df["profit"] = (df["revenue"] - df["total_cost"]).round(2)
df["profit_margin_pct"] = (df["profit"] / df["revenue"] * 100).round(2)
df["order_month"] = df["order_date"].dt.to_period("M").astype(str)
df["order_year"] = df["order_date"].dt.year
df = df.sort_values("order_date").reset_index(drop=True)
df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")

df.to_csv("data/cleaned/ecommerce_cleaned.csv", index=False)
log += [f"Final clean rows: {len(df):,}", f"Remaining nulls: {int(df.isna().sum().sum())}",
        f"Date range: {df.order_date.min()} to {df.order_date.max()}"]
open("data/cleaned/cleaning_report.txt", "w").write("\n".join(log))
print("\n".join(log))
