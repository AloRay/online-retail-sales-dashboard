"""
clean_and_analyse.py

Cleans the raw Online Retail dataset and produces a full set of
analysis-ready CSV outputs that feed directly into Power BI.

INPUT:
    online_retail_raw.csv

OUTPUT:
    sales_clean.csv              -- cleaned transactions (no cancellations,
                                    no bad prices, no dupes, CustomerID filled)
    cancellations.csv            -- cancelled orders only (for analysis)
    monthly_revenue.csv          -- revenue by month
    revenue_by_country.csv       -- revenue by country (top 10 + Other)
    top_products.csv             -- top 20 products by revenue
    customer_segments.csv        -- RFM-style customer segmentation
    conversion_funnel.csv        -- funnel: orders → paid → repeat customers
    cleaning_log.csv             -- what was removed and why

Run: python clean_and_analyse.py
"""

import pandas as pd
import numpy as np
from datetime import datetime

pd.set_option("mode.chained_assignment", None)

# ── LOAD ─────────────────────────────────────────────────────────────────────
df = pd.read_csv("online_retail_raw.csv",
                 encoding="utf-8-sig",
                 dtype={"CustomerID": str,
                        "InvoiceNo": str,
                        "StockCode": str})

raw_rows = len(df)
cleaning_log = []

def log(step, removed, reason):
    cleaning_log.append({"step": step, "rows_removed": removed, "reason": reason})
    print(f"  [{step}] removed {removed} rows — {reason}")

print(f"\nLoaded {raw_rows:,} raw rows")
print("=" * 55)

# ── STEP 1: PARSE DATES ───────────────────────────────────────────────────────
# Dates come in as "18/01/2011 14:44" (day/month/year) -- not ISO format.
# dayfirst=True is critical here; without it, 05/06/2011 gets read as May 6
# (US format) instead of June 5 (UK format), silently wrong.
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], dayfirst=True, errors="coerce")
unparseable_dates = df["InvoiceDate"].isna().sum()
if unparseable_dates:
    log("1-date-parse", unparseable_dates, "InvoiceDate could not be parsed")
    df = df[df["InvoiceDate"].notna()]

df["Year"]  = df["InvoiceDate"].dt.year
df["Month"] = df["InvoiceDate"].dt.month
df["MonthName"] = df["InvoiceDate"].dt.strftime("%b %Y")
df["DayOfWeek"] = df["InvoiceDate"].dt.day_name()
df["Hour"] = df["InvoiceDate"].dt.hour

# ── STEP 2: REMOVE EXACT DUPLICATE ROWS ──────────────────────────────────────
dupe_mask = df.duplicated()
n_dupes = dupe_mask.sum()
log("2-duplicates", n_dupes, "exact duplicate rows (double-processed transactions)")
df = df[~dupe_mask]

# ── STEP 3: SEPARATE CANCELLATIONS (keep them, don't throw away) ─────────────
cancel_mask = df["InvoiceNo"].str.startswith("C")
cancellations = df[cancel_mask].copy()
df_active = df[~cancel_mask].copy()
log("3-cancellations", cancel_mask.sum(),
    "cancellation invoices (InvoiceNo starts with C) -- moved to cancellations.csv, not deleted")

# ── STEP 4: REMOVE BAD PRICES ────────────────────────────────────────────────
df_active["UnitPrice"] = pd.to_numeric(df_active["UnitPrice"], errors="coerce")
bad_price_mask = df_active["UnitPrice"].isna() | (df_active["UnitPrice"] <= 0)
n_bad = bad_price_mask.sum()
log("4-bad-prices", n_bad,
    "zero or negative unit prices (free samples / data-entry errors)")
df_active = df_active[~bad_price_mask]

# ── STEP 5: REMOVE BAD QUANTITIES ────────────────────────────────────────────
df_active["Quantity"] = pd.to_numeric(df_active["Quantity"], errors="coerce")
bad_qty_mask = df_active["Quantity"].isna() | (df_active["Quantity"] <= 0)
n_bad_qty = bad_qty_mask.sum()
log("5-bad-quantity", n_bad_qty,
    "zero or negative quantities in non-cancellation rows (data error)")
df_active = df_active[~bad_qty_mask]

# ── STEP 6: FILL MISSING CUSTOMER IDs ────────────────────────────────────────
# Guest checkouts have no CustomerID. We DON'T drop these rows (that would
# lose ~25% of real revenue). Instead we assign a placeholder so every row
# has a value, and flag them separately.
missing_cust = (df_active["CustomerID"].isna() |
                (df_active["CustomerID"].str.strip() == ""))
n_missing_cust = missing_cust.sum()
df_active["CustomerType"] = np.where(missing_cust, "Guest", "Registered")
df_active.loc[missing_cust, "CustomerID"] = "GUEST"
log("6-guest-customers", 0,
    f"{n_missing_cust:,} rows had no CustomerID (guest checkouts) -- "
    "filled with 'GUEST' and flagged in CustomerType column, NOT removed "
    "(removing them would silently lose real revenue)")

# ── STEP 7: CALCULATE REVENUE PER LINE ───────────────────────────────────────
df_active["Revenue"] = (df_active["Quantity"] * df_active["UnitPrice"]).round(2)

# ── STEP 8: SAVE CLEAN FILE ──────────────────────────────────────────────────
df_active.to_csv("sales_clean.csv", index=False)
cancellations.to_csv("cancellations.csv", index=False)

clean_rows = len(df_active)
print(f"\nClean rows: {clean_rows:,}  ({round(100*clean_rows/raw_rows,1)}% of raw)")

# ── ANALYSIS 1: MONTHLY REVENUE ──────────────────────────────────────────────
monthly = (df_active.groupby(["Year","Month","MonthName"])
           .agg(Total_Revenue=("Revenue","sum"),
                Orders=("InvoiceNo","nunique"),
                Items_Sold=("Quantity","sum"))
           .reset_index()
           .sort_values(["Year","Month"]))
monthly["Total_Revenue"] = monthly["Total_Revenue"].round(2)
monthly.to_csv("monthly_revenue.csv", index=False)

# ── ANALYSIS 2: REVENUE BY COUNTRY ───────────────────────────────────────────
by_country = (df_active.groupby("Country")
              .agg(Total_Revenue=("Revenue","sum"),
                   Orders=("InvoiceNo","nunique"),
                   Customers=("CustomerID","nunique"))
              .reset_index()
              .sort_values("Total_Revenue", ascending=False))
by_country["Total_Revenue"] = by_country["Total_Revenue"].round(2)
# label rows outside top 10 as "Other" for a cleaner chart
top10 = by_country.head(10)["Country"].tolist()
by_country["Country_Group"] = by_country["Country"].apply(
    lambda c: c if c in top10 else "Other")
by_country.to_csv("revenue_by_country.csv", index=False)

# ── ANALYSIS 3: TOP 20 PRODUCTS ──────────────────────────────────────────────
top_prods = (df_active.groupby(["StockCode","Description"])
             .agg(Total_Revenue=("Revenue","sum"),
                  Units_Sold=("Quantity","sum"),
                  Times_Ordered=("InvoiceNo","nunique"))
             .reset_index()
             .sort_values("Total_Revenue", ascending=False)
             .head(20))
top_prods["Total_Revenue"] = top_prods["Total_Revenue"].round(2)
top_prods.to_csv("top_products.csv", index=False)

# ── ANALYSIS 4: CUSTOMER SEGMENTATION (RFM) ──────────────────────────────────
# RFM = Recency, Frequency, Monetary -- the classic way to segment customers.
# Recency:   how recently did they buy? (lower days = better)
# Frequency: how many orders did they place?
# Monetary:  how much did they spend total?
snapshot_date = df_active["InvoiceDate"].max() + pd.Timedelta(days=1)

rfm = (df_active[df_active["CustomerType"] == "Registered"]
       .groupby("CustomerID")
       .agg(
           Recency=("InvoiceDate", lambda x: (snapshot_date - x.max()).days),
           Frequency=("InvoiceNo", "nunique"),
           Monetary=("Revenue", "sum")
       )
       .reset_index())
rfm["Monetary"] = rfm["Monetary"].round(2)

# score each dimension 1-4 (4 = best)
rfm["R_Score"] = pd.qcut(rfm["Recency"],  4, labels=[4,3,2,1])
rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 4, labels=[1,2,3,4])
rfm["M_Score"] = pd.qcut(rfm["Monetary"].rank(method="first"), 4, labels=[1,2,3,4])
rfm["RFM_Score"] = (rfm["R_Score"].astype(str) +
                    rfm["F_Score"].astype(str) +
                    rfm["M_Score"].astype(str))

def segment(row):
    r, f, m = int(row["R_Score"]), int(row["F_Score"]), int(row["M_Score"])
    if r >= 3 and f >= 3 and m >= 3: return "Champions"
    if r >= 3 and f >= 2:            return "Loyal Customers"
    if r >= 3 and f == 1:            return "Promising"
    if r == 2 and f >= 2:            return "At Risk"
    return "Lost / Inactive"

rfm["Segment"] = rfm.apply(segment, axis=1)
rfm.to_csv("customer_segments.csv", index=False)

# ── ANALYSIS 5: CONVERSION FUNNEL ────────────────────────────────────────────
total_invoices = df_active["InvoiceNo"].nunique()
paid_invoices  = df_active[df_active["Revenue"] > 0]["InvoiceNo"].nunique()
repeat_customers = (rfm[rfm["Frequency"] > 1]["CustomerID"].nunique())
total_customers  = rfm["CustomerID"].nunique()
cancel_invoices  = cancellations["InvoiceNo"].nunique()

funnel = pd.DataFrame([
    {"Stage": "1. Total Orders Placed",   "Count": total_invoices},
    {"Stage": "2. Orders With Revenue",   "Count": paid_invoices},
    {"Stage": "3. Registered Customers",  "Count": total_customers},
    {"Stage": "4. Repeat Customers",      "Count": repeat_customers},
])
funnel["Pct_of_Top"] = (funnel["Count"] / total_invoices * 100).round(1)
funnel.to_csv("conversion_funnel.csv", index=False)

# ── CLEANING LOG ─────────────────────────────────────────────────────────────
pd.DataFrame(cleaning_log).to_csv("cleaning_log.csv", index=False)

# ── FINAL SUMMARY ─────────────────────────────────────────────────────────────
total_rev = df_active["Revenue"].sum()
avg_order = df_active.groupby("InvoiceNo")["Revenue"].sum().mean()
best_month = monthly.loc[monthly["Total_Revenue"].idxmax(), "MonthName"]
best_country = by_country.iloc[0]["Country"]
cancel_rate  = round(100 * cancel_invoices / (total_invoices + cancel_invoices), 1)

summary = f"""
SALES ANALYSIS SUMMARY
=======================
Raw rows:            {raw_rows:,}
Clean rows:          {clean_rows:,}
Cancellations:       {len(cancellations):,} rows ({cancel_rate}% of all invoices)
-----------------------------------------------------
Total Revenue:       £{total_rev:,.2f}
Avg Order Value:     £{avg_order:,.2f}
Total Orders:        {total_invoices:,}
Total Customers:     {total_customers:,}
Repeat Customers:    {repeat_customers:,} ({round(100*repeat_customers/total_customers,1)}% of registered)
-----------------------------------------------------
Best Month:          {best_month}
Top Country:         {best_country}
Top Product:         {top_prods.iloc[0]['Description']} (£{top_prods.iloc[0]['Total_Revenue']:,.2f})
=====================================================
Outputs saved:
  sales_clean.csv, cancellations.csv,
  monthly_revenue.csv, revenue_by_country.csv,
  top_products.csv, customer_segments.csv,
  conversion_funnel.csv, cleaning_log.csv
"""
print(summary)
with open("analysis_summary.txt", "w") as f:
    f.write(summary)
