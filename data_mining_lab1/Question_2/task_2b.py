import duckdb
import re
import hashlib

# 1. Connect and fetch the exact same pairs from Task 2A
con = duckdb.connect()
query = """
WITH pairs AS (
    SELECT * FROM read_csv_auto('labelled_pairs.csv', ignore_errors=true)
),
notices AS (
    SELECT notice_id, body FROM read_csv_auto('notices/part-*.csv', ignore_errors=true)
)
SELECT 
    p.label, n1.body AS body1, n2.body AS body2
FROM pairs p
JOIN notices n1 ON p.notice_id_a = n1.notice_id
JOIN notices n2 ON p.notice_id_b = n2.notice_id
WHERE p.label IN ('same', 'different')
LIMIT 100;
"""
sample_pairs = con.execute(query).df()
same_row = sample_pairs[sample_pairs['label'] == 'same'].iloc[0]
diff_row = sample_pairs[sample_pairs['label'] == 'different'].iloc[0]

# 2. Our Adopted Clean Trigram method from Part A
def clean_and_shingle(text):
    text = re.sub(r'\d+', '', str(text).lower()) 
    text = re.sub(r'[^\w\s]', '', text) 
    tokens = text.split()
    return set([' '.join(tokens[i:i+3]) for i in range(len(tokens)-2)])

def true_jaccard(set1, set2):
    if not set1 or not set2: return 0.0
    return len(set1.intersection(set2)) / len(set1.union(set2))

# 3. MinHash Implementation (K = 400 hashes for ~5% error)
def get_minhash_signature(shingles, num_hashes=400):
    signature = [float('inf')] * num_hashes
    for shingle in shingles:
        for i in range(num_hashes):
            # Deterministic hash using md5
            h = int(hashlib.md5(f"{shingle}_{i}".encode('utf8')).hexdigest()[:8], 16)
            if h < signature[i]:
                signature[i] = h
    return signature

def estimated_jaccard(sig1, sig2):
    matches = sum(1 for i, j in zip(sig1, sig2) if i == j)
    return matches / len(sig1)

print("--- EVALUATING 'SAME' PAIR ---")
s1_shingles = clean_and_shingle(same_row['body1'])
s2_shingles = clean_and_shingle(same_row['body2'])
true_sim_same = true_jaccard(s1_shingles, s2_shingles)

s1_sig = get_minhash_signature(s1_shingles)
s2_sig = get_minhash_signature(s2_shingles)
est_sim_same = estimated_jaccard(s1_sig, s2_sig)

print(f"True Exact Jaccard:      {true_sim_same:.3f}")
print(f"MinHash Estimated (k=400): {est_sim_same:.3f}")
print(f"Realized Error:          {abs(true_sim_same - est_sim_same):.3f} (Target: <= 0.050)")

print("\n--- EVALUATING 'DIFFERENT' PAIR ---")
d1_shingles = clean_and_shingle(diff_row['body1'])
d2_shingles = clean_and_shingle(diff_row['body2'])
true_sim_diff = true_jaccard(d1_shingles, d2_shingles)

d1_sig = get_minhash_signature(d1_shingles)
d2_sig = get_minhash_signature(d2_shingles)
est_sim_diff = estimated_jaccard(d1_sig, d2_sig)

print(f"True Exact Jaccard:      {true_sim_diff:.3f}")
print(f"MinHash Estimated (k=400): {est_sim_diff:.3f}")
print(f"Realized Error:          {abs(true_sim_diff - est_sim_diff):.3f} (Target: <= 0.050)")