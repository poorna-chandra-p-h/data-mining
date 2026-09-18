import matplotlib.pyplot as plt
import numpy as np

# Total hashes from Part B
k = 400

# Our chosen operating point to heavily penalize false positives (lawsuits)
b = 20
r = 20
assert b * r == k

# Generate similarity values from 0.0 to 1.0
similarities = np.linspace(0, 1.0, 100)

# Calculate the probability of surviving to the candidate stage: 1 - (1 - s^r)^b
probabilities = 1 - (1 - similarities**r)**b

# Create the plot
plt.figure(figsize=(10, 6))
plt.plot(similarities, probabilities, label=f'b={b}, r={r}', color='blue', linewidth=2)

# Mark our operating point (approximate threshold)
threshold = (1/b)**(1/r)
plt.axvline(x=threshold, color='red', linestyle='--', label=f'Threshold $\\approx$ {threshold:.2f}')
plt.plot(threshold, 0.5, 'ro', markersize=8)

# Formatting
plt.title('LSH Candidate Survival Probability (MinHash k=400)')
plt.xlabel('True Jaccard Similarity (s)')
plt.ylabel('Probability of becoming a Candidate')
plt.grid(True, alpha=0.3)
plt.legend()

# Save the plot
plt.savefig('lsh_curve.png')
print(f"Curve saved to lsh_curve.png. Threshold is {threshold:.3f}")