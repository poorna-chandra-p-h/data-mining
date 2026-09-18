import duckdb

# Connect to DuckDB
con = duckdb.connect('annapurna.duckdb')

# Attach Postgres
con.execute("INSTALL postgres;")
con.execute("LOAD postgres;")
con.execute("ATTACH 'dbname=annapurna user=postgres password=postgres' AS pg (TYPE postgres);")

print("Task D: Temporal Pricing Join (SCD2)\n")

# Define ONE single SQL query string. 
# It joins the fact table to the price history table using the sale's business_date.
sql_query = """
SELECT 
    f.sales_month,
    CAST(SUM(f.qty * pr.selling_price) AS DECIMAL(15,2)) AS true_revenue
FROM fact_sales f
JOIN pg.price_revisions pr 
  ON f.product_sk = pr.product_sk
 AND f.business_date BETWEEN pr.effective_from AND pr.effective_to
WHERE f.sales_month = ?
GROUP BY f.sales_month;
"""

print("Running query for March (Month 3)...")
march_result = con.execute(sql_query, [3]).df()
print(march_result)

print("\nRunning the EXACT SAME query string for October (Month 10)...")
oct_result = con.execute(sql_query, [10]).df()
print(oct_result)