import duckdb

# Connect to the DuckDB database created in Task B
con = duckdb.connect('annapurna.duckdb')

print("Designing and building the dashboard Fact Table...")

# Ensure DuckDB is connected to PostgreSQL to read the master tables
con.execute("INSTALL postgres;")
con.execute("LOAD postgres;")
con.execute("ATTACH 'dbname=annapurna user=postgres password=postgres' AS pg (TYPE postgres);")

sql = """
CREATE OR REPLACE TABLE fact_sales AS 
SELECT 
    s.bill_no,
    -- Extract store ID and dates directly from bill_no format (SXX/YYYYMMDD/XXXXX)
    SUBSTRING(s.bill_no, 1, 3) AS store_id,
    CAST(strptime(SUBSTRING(s.bill_no, 5, 8), '%Y%m%d') AS DATE) AS business_date,
    DAYOFWEEK(CAST(strptime(SUBSTRING(s.bill_no, 5, 8), '%Y%m%d') AS DATE)) AS day_of_week,
    MONTH(CAST(strptime(SUBSTRING(s.bill_no, 5, 8), '%Y%m%d') AS DATE)) AS sales_month,
    
    p.product_sk,       -- Surrogate key resolves the reissued code issue
    p.category_id,
    s.qty,
    s.unit_price,
    s.line_type
FROM clean_sales s
-- Join on code AND temporal validity to handle reissued codes
LEFT JOIN pg.products p 
  ON s.product_code = p.product_code 
 AND CAST(strptime(SUBSTRING(s.bill_no, 5, 8), '%Y%m%d') AS DATE) BETWEEN p.valid_from AND p.valid_to

-- Filter out non-revenue lines to prevent double counting
WHERE s.line_type IN ('SALE', 'RETURN', 'DISCOUNT', 'VOID');
"""

con.execute(sql)

print("\nTask C Complete: fact_sales table built.")

# Quick validation check to show the schema and a sample of the dashboard data
print("\nFact Table Schema:")
print(con.execute("DESCRIBE fact_sales;").df())

print("\nSample Data (Ready for Dashboard slicing):")
print(con.execute("SELECT * FROM fact_sales LIMIT 5;").df())