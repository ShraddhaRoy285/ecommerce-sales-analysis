"""Generate a realistic, deliberately MESSY e-commerce dataset (12,000+ rows).
Synthetic data so the project is fully reproducible (seed fixed)."""
import numpy as np, pandas as pd
rng = np.random.default_rng(42)
N = 12000

catalog = {  # category: [(product, base_price INR, cost_ratio)]
 "Electronics": [("Wireless Earbuds",2499,.72),("Smart Watch",4999,.75),("Power Bank",1299,.68),("Bluetooth Speaker",1999,.70)],
 "Fashion":     [("Men's T-Shirt",599,.45),("Women's Kurti",899,.48),("Sneakers",2199,.55),("Jacket",2999,.52)],
 "Home & Kitchen":[("Mixer Grinder",3499,.70),("Cookware Set",2799,.62),("Bedsheet Set",1199,.50),("Water Bottle",399,.40)],
 "Beauty":      [("Face Serum",799,.35),("Perfume",1499,.40),("Hair Dryer",1599,.60),("Lipstick Set",699,.38)],
 "Books":       [("Self-Help Book",349,.60),("Fiction Novel",299,.58),("Exam Guide",499,.62)],
 "Sports":      [("Yoga Mat",799,.55),("Dumbbell Set",2499,.65),("Football",699,.58)],
}
keys = list(catalog)
cat_w = [.26,.22,.18,.14,.08,.12]
regions = ["North","South","East","West","North-East","Central"]
reg_w = [.17,.25,.15,.25,.07,.11]
pay = ["UPI","Credit Card","Debit Card","COD","Net Banking","Wallet"]
status = ["Delivered","Shipped","Returned","Cancelled"]

n_cust = 3200
cust = rng.integers(1, n_cust+1, N)
loyal = rng.random(N) < 0.35                    # 35% of orders from a small loyal group
cust[loyal] = rng.integers(1, 400, loyal.sum())

# growth trend + festive (Oct-Nov) seasonality
days = pd.to_datetime("2024-01-01") + pd.to_timedelta(np.arange(730), unit="D")
w = np.linspace(1, 1.8, 730) * (1 + 0.6*np.isin(days.month, [10, 11]))
dates = days[rng.choice(730, N, p=w/w.sum())]

cat_pick = rng.choice(len(keys), N, p=cat_w)
recs = []
for i in range(N):
    c = keys[cat_pick[i]]
    p, bp, cr = catalog[c][rng.integers(len(catalog[c]))]
    price = round(bp*rng.uniform(.92, 1.08), 2)
    recs.append((f"ORD{100000+i}", f"CUST{cust[i]:04d}", dates[i], c, p,
                 int(rng.choice([1,1,1,2,2,3,4])), price, int(rng.choice([0,0,0,5,10,15,20])),
                 round(price*cr, 2), rng.choice(regions, p=reg_w), rng.choice(pay),
                 rng.choice(status, p=[.72,.12,.07,.09])))
df = pd.DataFrame(recs, columns=["order_id","customer_id","order_date","product_category","product_name",
        "quantity","unit_price","discount_pct","cost_price","region","payment_method","order_status"])

# ---------- inject real-world mess ----------
fmts = ["%Y-%m-%d","%d/%m/%Y","%d-%b-%Y","%m-%d-%Y"]
df["order_date"] = [d.strftime(fmts[rng.integers(4)]) if rng.random() < .35 else d.strftime("%Y-%m-%d")
                    for d in pd.to_datetime(df.order_date)]
for col, frac in [("region",.04),("discount_pct",.05),("quantity",.02),("unit_price",.015),
                  ("payment_method",.03),("customer_id",.005)]:
    df.loc[rng.random(N) < frac, col] = np.nan
df["region"] = df["region"].apply(lambda x: x if pd.isna(x) else rng.choice([x,x.lower(),x.upper(),f" {x} "], p=[.8,.07,.07,.06]))
df["product_category"] = df["product_category"].apply(lambda x: rng.choice([x,x.lower(),x.upper()+" "], p=[.9,.05,.05]))
idx = rng.choice(N, 60, replace=False)
df.loc[idx[:25], "quantity"] = rng.integers(80, 500, 25)                                   # outlier quantities
df.loc[idx[25:45], "unit_price"] = df.loc[idx[25:45], "unit_price"].astype(float)*rng.uniform(15, 40, 20)  # outlier prices
df.loc[idx[45:], "unit_price"] = -df.loc[idx[45:], "unit_price"].astype(float)             # invalid negatives
dups = df.sample(250, random_state=1)                                                      # duplicate rows
df = pd.concat([df, dups]).sample(frac=1, random_state=3).reset_index(drop=True)
df.to_csv("data/raw/ecommerce_raw.csv", index=False)
print("Raw data saved:", df.shape)
