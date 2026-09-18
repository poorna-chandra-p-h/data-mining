import duckdb
import glob

# Check which file dialects actually exist in the object store
has_d1 = len(glob.glob('annapurna-lake/partitioned_sales/*/*/store=S0[1-5]/*.csv')) > 0
has_d2 = len(glob.glob('annapurna-lake/partitioned_sales/*/*/store=S0[6-9]/*.csv')) > 0
has_d3 = len(glob.glob('annapurna-lake/partitioned_sales/*/*/store=S1[0-2]/*.csv')) > 0
has_pq = len(glob.glob('annapurna-lake/partitioned_sales/*/*/*/*.parquet')) > 0

queries = []

# S01-S05: Standard CSV
if has_d1:
    queries.append("""
        SELECT bill_no::VARCHAR as bill_no, line_no::VARCHAR as line_no, product_code::VARCHAR as product_code, 
               qty::DOUBLE as qty, unit_price::DOUBLE as unit_price, line_type::VARCHAR as line_type, filename 
        FROM read_csv_auto('annapurna-lake/partitioned_sales/*/*/store=S0[1-5]/*.csv', ignore_errors=true)
    """)

# S06-S09: Semicolon separated, different column headers
if has_d2:
    queries.append("""
        SELECT bill_no::VARCHAR as bill_no, line_no::VARCHAR as line_no, item_code::VARCHAR as product_code, 
               quantity::DOUBLE as qty, rate::DOUBLE as unit_price, type::VARCHAR as line_type, filename 
        FROM read_csv_auto('annapurna-lake/partitioned_sales/*/*/store=S0[6-9]/*.csv', delim=';', ignore_errors=true)
    """)

# S10-S12: UTF-8 BOM, epoch timestamps, standard column headers
if has_d3:
    queries.append("""
        SELECT bill_no::VARCHAR as bill_no, line_no::VARCHAR as line_no, product_code::VARCHAR as product_code, 
               qty::DOUBLE as qty, unit_price::DOUBLE as unit_price, line_type::VARCHAR as line_type, filename 
        FROM read_csv_auto('annapurna-lake/partitioned_sales/*/*/store=S1[0-2]/*.csv', ignore_errors=true)
    """)

# Parquet files
if has_pq:
    queries.append("""
        SELECT bill_no::VARCHAR as bill_no, line_no::VARCHAR as line_no, product_code::VARCHAR as product_code, 
               qty::DOUBLE as qty, unit_price::DOUBLE as unit_price, line_type::VARCHAR as line_type, filename 
        FROM read_parquet('annapurna-lake/partitioned_sales/*/*/*/*.parquet')
    """)

if not queries:
    print("No sales files found in annapurna-lake/partitioned_sales/!")
    exit()

# Combine all existing dialects
combined_raw_sql = " UNION ALL ".join(queries)

con = duckdb.connect('annapurna.duckdb')
print("Executing idempotent load and deduplication...")

# Create the clean deduplicated table
sql = f"""
CREATE OR REPLACE TABLE clean_sales AS 
WITH combined_raw AS (
    {combined_raw_sql}
),
deduped AS (
    SELECT *,
        ROW_NUMBER() OVER(
            PARTITION BY bill_no, line_no 
            ORDER BY filename DESC
        ) as rn
    FROM combined_raw
)
SELECT bill_no, line_no, product_code, qty, unit_price, line_type 
FROM deduped 
WHERE rn = 1;
"""
con.execute(sql)

# Prove idempotency
print("Validation Check:")
result = con.execute("""
SELECT 
    COUNT(*) as total_rows, 
    SUM(hash(bill_no || '_' || line_no)) as check_sum 
FROM clean_sales;
""").df()

print(result)