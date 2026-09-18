import duckdb
import pandas as pd
import os

# Connect to DuckDB database
con = duckdb.connect('annapurna.duckdb')

# Attach PostgreSQL for temporal pricing lookup
con.execute("INSTALL postgres;")
con.execute("LOAD postgres;")
con.execute("ATTACH 'dbname=annapurna user=postgres password=postgres' AS pg (TYPE postgres);")

print("==================================================")
print("     TASK F: PIPELINE VS FINANCE RECONCILIATION")
print("==================================================")

# 1. Calculate Monthly Revenue from the Pipeline (using SCD2 pricing)
pipeline_sql = """
SELECT 
    f.sales_month AS month,
    CAST(SUM(f.qty * pr.selling_price) AS DECIMAL(15,2)) AS pipeline_revenue
FROM fact_sales f
JOIN pg.price_revisions pr 
  ON f.product_sk = pr.product_sk
 AND f.business_date BETWEEN pr.effective_from AND pr.effective_to
GROUP BY f.sales_month
ORDER BY f.sales_month;
"""
pipeline_df = con.execute(pipeline_sql).df()

# Convert the pipeline's 'month' column to a string so it matches the CSV data type
pipeline_df['month'] = pipeline_df['month'].astype(str)

# 2. Locate and load the official monthly finance report CSV
finance_path = 'finance_monthly.csv'
if not os.path.exists(finance_path):
    finance_path = '../finance_monthly.csv' # Check parent folder

finance_df = pd.read_csv(finance_path)

# Normalize column names to lowercase for safe merging
finance_df.columns = [c.strip().lower() for c in finance_df.columns]

# Convert finance CSV's 'month' column to string as well, just to be absolutely certain
if 'month' in finance_df.columns:
    finance_df['month'] = finance_df['month'].astype(str)

# 3. Merge pipeline calculations with finance records for comparison
reconciliation_df = pd.merge(pipeline_df, finance_df, on='month', how='outer')

# Optional: Add a difference column to show any discrepancies
if 'revenue' in reconciliation_df.columns:
    reconciliation_df['difference'] = reconciliation_df['pipeline_revenue'] - reconciliation_df['revenue']

print("\n[SIDE-BY-SIDE RECONCILIATION TABLE]:")
print(reconciliation_df.to_string(index=False))
print("==================================================\n")