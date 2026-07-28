## Online Retail Sales & Customer Intelligence Dashboard
A Python → SQL → Power BI analytics pipeline built on the UCI Online Retail Dataset — 541,909 real transactions from a UK-based online gift retailer (December 2010 – December 2011). Covers revenue analysis, country performance, top products, RFM customer segmentation, and a conversion funnel across two interactive dashboard pages.


### Data Source
UCI Online Retail Dataset — Daqing Chen, Sai Liang Sain, and Kun Guo, "Data mining for the online retail industry", Journal of Database Marketing and Customer Strategy Management, 2012. Download: https://archive.ics.uci.edu/dataset/352/online+retail

### Three (3) Key Data Decisions
1. UK date format parsed explicitly: InvoiceDate arrives as DD/MM/YYYY. Without dayfirst=True, Python reads 05/06/2011 as May 6 instead of June 5 — silently misassigning every transaction to the wrong month. One parameter, big impact.

2. Cancellations kept, not deleted: ~9,288 cancellation invoices (16% of all invoices) were moved to a separate file rather than deleted. The cancellation rate is a real business metric, not noise to hide.

3. Guest checkouts preserved: ~135,080 rows had no CustomerID (guest checkouts). Dropping them would silently lose ~25% of revenue. Filled with "GUEST" and flagged in a CustomerType column instead.


### Key Findings
- Total revenue: £10.6M across 19,960 orders
- Average order value: £533.17
- 16.1% cancellation rate
- 65.6% of registered customers are repeat buyers
- UK accounts for ~91% of revenue; Germany and France are next
- Clear seasonal revenue spike in Oct-Nov (Christmas gift buying)


### Dashboard
<img width="648" height="364" alt="customer intelligence" src="https://github.com/user-attachments/assets/14c0643d-9fe3-48de-af97-8800d6b89a97" />

<img width="643" height="362" alt="revenue overview" src="https://github.com/user-attachments/assets/a4250c94-0337-458f-8a3d-2f67908326bf" />


### Watch Demo / Walkthrough
https://www.loom.com/share/394c82ee61334c0da04717083b12518e


### Tools
Python (pandas), SQL (SQLite), Power BI Desktop, DAX


### Files
File	Description
analysis_summary
build_database (python script)
clean_and_analyse (python script)
online_retail_raw.csv	Raw input (541,909 rows)
clean_and_analyse.py	Python cleaning + analysis pipeline
sales_clean.csv	Cleaned output (406,829 rows)
cancellations.csv	Cancelled orders for analysis
monthly_revenue.csv	Revenue by month
revenue_by_country.csv	Revenue by country
top_products.csv	Top 20 products by revenue
customer_segments.csv	RFM scores per customer
conversion_funnel.csv	Funnel: orders to repeat customers
cleaning_log.csv	What was removed and why
online_retail_sales.db	All tables in SQLite
sql_queries.sql	8 analysis queries
OnlineRetail_Sales_Dashboard.pbix	Power BI file
```
