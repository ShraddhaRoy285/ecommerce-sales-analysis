"""Build Excel dashboard: Data sheet + formula-driven pivot-style tables + charts."""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.utils import get_column_letter

df = pd.read_csv("data/cleaned/ecommerce_cleaned.csv")
cols = ["order_id","customer_id","order_date","order_month","product_category","product_name","region",
        "payment_method","order_status","quantity","unit_price","discount_pct","revenue","total_cost","profit"]
df = df[cols]; N = len(df) + 1
F = "Arial"; hdr_fill = PatternFill("solid", fgColor="1F3864"); hdr_font = Font(name=F, bold=True, color="FFFFFF")
def header(ws, row, c1, labels):
    for i, l in enumerate(labels):
        c = ws.cell(row=row, column=c1+i, value=l); c.font = hdr_font; c.fill = hdr_fill; c.alignment = Alignment(horizontal="center")

wb = Workbook()
# ---------------- Data ----------------
wd = wb.active; wd.title = "Data"
header(wd, 1, 1, cols)
for r in df.itertuples(index=False): wd.append(list(r))
wd.freeze_panes = "A2"; wd.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{N}"
for i, w in enumerate([12,12,12,11,16,20,12,14,12,9,11,10,12,12,12], 1): wd.column_dimensions[get_column_letter(i)].width = w
for row in wd.iter_rows(min_row=2, max_row=N):
    for c in row:
        c.font = Font(name=F, size=10)
        if c.column in (11,13,14,15): c.number_format = "#,##0.00"
for c in wd[1]: c.font = hdr_font
rng = lambda col: f"Data!${col}$2:${col}${N}"
REV, PROF, REG, CAT, MON, ST, ORD, CUS = rng("M"), rng("O"), rng("G"), rng("E"), rng("D"), rng("I"), rng("A"), rng("B")

# ---------------- Summary (KPIs) ----------------
ws = wb.create_sheet("Summary", 0)
ws["A1"] = "E-Commerce Sales & Customer Behavior Dashboard"; ws["A1"].font = Font(name=F, size=16, bold=True, color="1F3864")
ws["A2"] = "All figures in INR (₹). Cancelled orders excluded from revenue/profit. Source: data/cleaned/ecommerce_cleaned.csv (synthetic)."
ws["A2"].font = Font(name=F, italic=True, size=9, color="595959")
kpis = [("Total Revenue (₹)", f'=SUMIFS({REV},{ST},"<>Cancelled")', "#,##0"),
        ("Total Profit (₹)", f'=SUMIFS({PROF},{ST},"<>Cancelled")', "#,##0"),
        ("Overall Profit Margin", "=B5/B4", "0.0%"),
        ("Valid Orders", f'=COUNTIFS({ST},"<>Cancelled")', "#,##0"),
        ("Avg Order Value (₹)", "=B4/B7", "#,##0"),
        ("Return Rate", f'=COUNTIFS({ST},"Returned")/COUNTA({ORD})', "0.0%"),
        ("Cancellation Rate", f'=COUNTIFS({ST},"Cancelled")/COUNTA({ORD})', "0.0%")]
header(ws, 3, 1, ["KPI", "Value"])
for i, (k, f, nf) in enumerate(kpis, 4):
    ws.cell(row=i, column=1, value=k).font = Font(name=F, bold=True)
    c = ws.cell(row=i, column=2, value=f); c.number_format = nf; c.font = Font(name=F)

# Category pivot
cats = sorted(df.product_category.unique()); r0 = 13
ws.cell(row=r0-1, column=1, value="Category Performance (pivot-style)").font = Font(name=F, bold=True, size=12)
header(ws, r0, 1, ["Category", "Revenue (₹)", "Profit (₹)", "Margin %", "Revenue Share"])
for i, c in enumerate(cats, r0+1):
    ws.cell(row=i, column=1, value=c)
    ws.cell(row=i, column=2, value=f'=SUMIFS({REV},{CAT},A{i},{ST},"<>Cancelled")').number_format = "#,##0"
    ws.cell(row=i, column=3, value=f'=SUMIFS({PROF},{CAT},A{i},{ST},"<>Cancelled")').number_format = "#,##0"
    ws.cell(row=i, column=4, value=f"=C{i}/B{i}").number_format = "0.0%"
    ws.cell(row=i, column=5, value=f"=B{i}/$B$4").number_format = "0.0%"
cat_end = r0 + len(cats)

# Region pivot
regs = sorted(df.region.unique()); r1 = cat_end + 3
ws.cell(row=r1-1, column=1, value="Regional Sales Distribution (pivot-style)").font = Font(name=F, bold=True, size=12)
header(ws, r1, 1, ["Region", "Revenue (₹)", "Orders", "Revenue Share"])
for i, g in enumerate(regs, r1+1):
    ws.cell(row=i, column=1, value=g)
    ws.cell(row=i, column=2, value=f'=SUMIFS({REV},{REG},A{i},{ST},"<>Cancelled")').number_format = "#,##0"
    ws.cell(row=i, column=3, value=f'=COUNTIFS({REG},A{i},{ST},"<>Cancelled")').number_format = "#,##0"
    ws.cell(row=i, column=4, value=f"=B{i}/$B$4").number_format = "0.0%"
reg_end = r1 + len(regs)

# Monthly trend
months = sorted(df.order_month.unique()); r2 = reg_end + 3
ws.cell(row=r2-1, column=1, value="Monthly Revenue & MoM Growth").font = Font(name=F, bold=True, size=12)
header(ws, r2, 1, ["Month", "Revenue (₹)", "MoM Growth"])
for i, m in enumerate(months, r2+1):
    ws.cell(row=i, column=1, value=m)
    ws.cell(row=i, column=2, value=f'=SUMIFS({REV},{MON},A{i},{ST},"<>Cancelled")').number_format = "#,##0"
    if i > r2+1: ws.cell(row=i, column=3, value=f"=B{i}/B{i-1}-1").number_format = "0.0%"
mon_end = r2 + len(months)

for row in ws.iter_rows(min_row=4, max_row=mon_end, max_col=5):
    for c in row:
        if c.font.name != F or not c.font.bold and c.fill.fgColor.rgb != "001F3864": c.font = Font(name=F, bold=c.font.bold, color=c.font.color)
for r in (3, r0, r1, r2):
    for c in ws[r][:5]:
        if c.value: c.font = hdr_font
ws.column_dimensions["A"].width = 26
for col in "BCDE": ws.column_dimensions[col].width = 16

# Charts
b = BarChart(); b.title = "Revenue & Profit by Category (₹)"; b.height, b.width = 8, 15
b.add_data(Reference(ws, min_col=2, max_col=3, min_row=r0, max_row=cat_end), titles_from_data=True)
b.set_categories(Reference(ws, min_col=1, min_row=r0+1, max_row=cat_end)); ws.add_chart(b, "G3")
p = PieChart(); p.title = "Revenue Share by Region"; p.height, p.width = 8, 12
p.add_data(Reference(ws, min_col=2, min_row=r1, max_row=reg_end), titles_from_data=True)
p.set_categories(Reference(ws, min_col=1, min_row=r1+1, max_row=reg_end)); ws.add_chart(p, "G20")
l = LineChart(); l.title = "Monthly Revenue Trend (₹)"; l.height, l.width = 8, 22
l.add_data(Reference(ws, min_col=2, min_row=r2, max_row=mon_end), titles_from_data=True)
l.set_categories(Reference(ws, min_col=1, min_row=r2+1, max_row=mon_end)); ws.add_chart(l, "G37")

# ---------------- SQL result sheets ----------------
for q, name in [("q2","Top Customers (CLV)"),("q4","Customer Segments"),("q5","Category Margin Rank"),("q6","Top Products")]:
    s = wb.create_sheet(name); res = pd.read_csv(f"data/query_results/{q}.csv")
    header(s, 1, 1, list(res.columns))
    for r in res.itertuples(index=False): s.append(list(r))
    for i in range(1, len(res.columns)+1): s.column_dimensions[get_column_letter(i)].width = 20
    for row in s.iter_rows(min_row=2):
        for c in row: c.font = Font(name=F, size=10)
wb.save("excel/ecommerce_analysis_dashboard.xlsx"); print("saved")
