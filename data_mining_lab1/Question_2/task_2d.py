import duckdb
import time

# 1. Create a persistent disk-backed database for our index
con = duckdb.connect('setubid_lsh.duckdb')

print("1. Creating Relational LSH Index Schema...")
con.execute("""
    CREATE TABLE IF NOT EXISTS lsh_index (
        band_id INTEGER,
        band_hash VARCHAR,
        notice_id VARCHAR
    );
    CREATE TABLE IF NOT EXISTS new_notice (
        band_id INTEGER,
        band_hash VARCHAR
    );
""")

# Clear tables for a clean run
con.execute("DELETE FROM lsh_index; DELETE FROM new_notice;")

print("2. Populating index with 500,000 synthetic band hashes (simulating corpus)...")
con.execute("""
    INSERT INTO lsh_index 
    SELECT 
        (i % 20) AS band_id, 
        md5((i % 10000)::VARCHAR) AS band_hash, 
        'N' || (i / 20)::INT AS notice_id
    FROM generate_series(1, 500000) s(i);
""")

print("3. Simulating a new incoming notice (20 bands)...")
con.execute("""
    INSERT INTO new_notice 
    SELECT 
        (i % 20) AS band_id, 
        md5((i % 10000)::VARCHAR) AS band_hash
    FROM generate_series(1, 20) s(i);
""")

print("\n--- MEASURING ADOPTED METHOD: HASH JOIN ---")
# Standard Equi-Join triggers the query planner to use a Hash Join
query_hash_join = """
    SELECT l.notice_id 
    FROM lsh_index l 
    INNER JOIN new_notice n 
      ON l.band_id = n.band_id 
     AND l.band_hash = n.band_hash;
"""
start = time.time()
con.execute(query_hash_join).fetchall()
hash_time = time.time() - start
plan_hash = con.execute("EXPLAIN ANALYZE " + query_hash_join).df()

print(f"Wall-clock time: {hash_time:.4f} seconds")
print("Physical Plan uses HASH_JOIN:")
print([line for line in plan_hash.iloc[0]['explain_value'].split('\n') if 'HASH_JOIN' in line or 'Rows' in line][:3])


print("\n--- MEASURING REJECTED METHOD: NESTED LOOP JOIN ---")
# Forcing a Nested Loop Join by using a logically equivalent range condition (>= and <=)
# This prevents the planner from building a Hash Table
query_nested_loop = """
    SELECT l.notice_id 
    FROM lsh_index l 
    INNER JOIN new_notice n 
      ON l.band_id = n.band_id 
     AND l.band_hash >= n.band_hash 
     AND l.band_hash <= n.band_hash; 
"""
start = time.time()
con.execute(query_nested_loop).fetchall()
nested_time = time.time() - start
plan_nested = con.execute("EXPLAIN ANALYZE " + query_nested_loop).df()

print(f"Wall-clock time: {nested_time:.4f} seconds")
print("Physical Plan uses NESTED_LOOP:")
print([line for line in plan_nested.iloc[0]['explain_value'].split('\n') if 'NESTED' in line or 'Rows' in line][:3])

if hash_time > 0:
    print(f"\nConclusion: The Hash Join is approximately {nested_time / hash_time:.0f}x faster.")