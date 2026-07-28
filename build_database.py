"""
build_database.py

Run this AFTER clean_and_analyse.py has finished.
Loads all 9 output CSV files into a single SQLite database
so you can open everything in DB Browser for SQLite and
connect to it from Power BI using the Python script method.

Run with: py build_database.py
"""

import sqlite3
import pandas as pd
import os

DB_NAME = "online_retail_sales.db"

FILES = {
    "sales_raw":          "online_retail_raw.csv",
    "sales_clean":        "sales_clean.csv",
    "cancellations":      "cancellations.csv",
    "monthly_revenue":    "monthly_revenue.csv",
    "revenue_by_country": "revenue_by_country.csv",
    "top_products":       "top_products.csv",
    "customer_segments":  "customer_segments.csv",
    "conversion_funnel":  "conversion_funnel.csv",
    "cleaning_log":       "cleaning_log.csv",
}

# check all files exist before starting
missing = [f for f in FILES.values() if not os.path.exists(f)]
if missing:
    print("ERROR: These files are missing — run clean_and_analyse.py first:")
    for m in missing:
        print(f"  - {m}")
    exit(1)

print(f"Building {DB_NAME}...")
conn = sqlite3.connect(DB_NAME)

for table_name, filename in FILES.items():
    df = pd.read_csv(filename, dtype=str, encoding="utf-8-sig",
                     keep_default_na=False)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    print(f"  {table_name}: {len(df):,} rows loaded")

conn.commit()
conn.close()

print(f"\nDone. Open {DB_NAME} in DB Browser for SQLite.")
print("Or connect to it from Power BI using the Python script method.")
