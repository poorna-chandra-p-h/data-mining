import duckdb

# Connect to DuckDB
con = duckdb.connect('annapurna.duckdb')

# Attach Postgres
con.execute("INSTALL postgres;")
con.execute("LOAD postgres;")
con.execute("ATTACH 'dbname=annapurna user=postgres password=postgres' AS pg (TYPE postgres);")

print("Task E: Federated Query Plan Evaluation\n")

# Run EXPLAIN on the federated query
sql_plan = """
EXPLAIN 
SELECT 
    c.category_name,
    SUM(s.qty * pr.selling_price) AS true_revenue
FROM read_csv_auto('annapurna-lake/partitioned_sales/*/*/store=S12/*.csv', ignore_errors=true) s
JOIN pg.products p 
  ON s.product_code = p.product_code
 AND CAST(strptime(SUBSTRING(s.bill_no, 5, 8), '%Y%m%d') AS DATE) BETWEEN p.valid_from AND p.valid_to
JOIN pg.price_revisions pr 
  ON p.product_sk = pr.product_sk
 AND CAST(strptime(SUBSTRING(s.bill_no, 5, 8), '%Y%m%d') AS DATE) BETWEEN pr.effective_from AND pr.effective_to
JOIN pg.product_categories c
  ON p.category_id = c.category_id
WHERE s.line_type IN ('SALE', 'RETURN', 'DISCOUNT', 'VOID')
GROUP BY c.category_name;
"""

result = con.execute(sql_plan).fetchall()

for row in result:
    print(row[0])
    print(row[1])
    print("-" * 80)