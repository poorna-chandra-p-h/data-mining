import duckdb
import re

# 1. Connect to DuckDB and load the data
con = duckdb.connect()

print("Fetching a 'same' pair and a 'different' pair...")

# Updated query: Only use string comparisons for the label
query = """
WITH pairs AS (
    SELECT * FROM read_csv_auto('labelled_pairs.csv', ignore_errors=true)
),
notices AS (
    SELECT notice_id, body FROM read_csv_auto('notices/part-*.csv', ignore_errors=true)
)
SELECT 
    p.label, 
    n1.body AS body1, 
    n2.body AS body2
FROM pairs p
JOIN notices n1 ON p.notice_id_a = n1.notice_id
JOIN notices n2 ON p.notice_id_b = n2.notice_id
WHERE p.label IN ('same', 'different')
LIMIT 100;
"""
try:
    sample_pairs = con.execute(query).df()
except Exception as e:
    print(f"Error reading data: {e}")
    exit()

# Extract one same and one different
try:
    same_row = sample_pairs[sample_pairs['label'] == 'same'].iloc[0]
    diff_row = sample_pairs[sample_pairs['label'] == 'different'].iloc[0]
except IndexError:
    print("Could not find both a 'same' and 'different' pair. Check labels.")
    exit()

# 2. Define the two competing text processing methods
def clean_and_shingle(text, method):
    text = str(text).lower()
    
    if method == "raw_unigram":
        # Competing Choice: Keep everything (dates, money, boilerplate words)
        tokens = text.split()
        return set(tokens)
        
    elif method == "clean_trigram":
        # Adopted Choice: Strip digits and punctuation. Use 3-word shingles.
        # This destroys volatile dates/money and penalizes shuffled boilerplate.
        text = re.sub(r'\d+', '', text) 
        text = re.sub(r'[^\w\s]', '', text) 
        tokens = text.split()
        return set([' '.join(tokens[i:i+3]) for i in range(len(tokens)-2)])

def jaccard(set1, set2):
    if not set1 or not set2: return 0.0
    return len(set1.intersection(set2)) / len(set1.union(set2))

print("\n--- EVALUATING 'SAME' PAIR ---")
s1_raw = clean_and_shingle(same_row['body1'], "raw_unigram")
s2_raw = clean_and_shingle(same_row['body2'], "raw_unigram")
print(f"Competing (Raw Unigrams Jaccard): {jaccard(s1_raw, s2_raw):.3f}")

s1_clean = clean_and_shingle(same_row['body1'], "clean_trigram")
s2_clean = clean_and_shingle(same_row['body2'], "clean_trigram")
print(f"Adopted (Clean Trigrams Jaccard): {jaccard(s1_clean, s2_clean):.3f}")

print("\n--- EVALUATING 'DIFFERENT' PAIR ---")
d1_raw = clean_and_shingle(diff_row['body1'], "raw_unigram")
d2_raw = clean_and_shingle(diff_row['body2'], "raw_unigram")
print(f"Competing (Raw Unigrams Jaccard): {jaccard(d1_raw, d2_raw):.3f}")

d1_clean = clean_and_shingle(diff_row['body1'], "clean_trigram")
d2_clean = clean_and_shingle(diff_row['body2'], "clean_trigram")
print(f"Adopted (Clean Trigrams Jaccard): {jaccard(d1_clean, d2_clean):.3f}")