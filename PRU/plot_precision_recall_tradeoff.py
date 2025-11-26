#!/usr/bin/env python3
"""
Generate Precision-Recall Trade-off Graph for LISA Traffic Light Dataset

Data from Paper Section 5.3.1:
| Tolerance (δ) | LCR | Anomalies Flagged | Precision | Recall Cost |
|---------------|-----|-------------------|-----------|-------------|
| 0ms (Strict)  | 66.6% | 3,344 | 87% | 13% |
| 50ms          | 71.1% | 2,891 | 97% | 3% |
| 100ms (Optimal)| 78.4% | 2,156 | 94% | 6% |
"""
import matplotlib.pyplot as plt
import numpy as np

# Data from paper
tolerances = [0, 50, 100]  # milliseconds
precision = [87, 97, 94]  # percentage
recall = [100 - 13, 100 - 3, 100 - 6]  # 100% - recall_cost
anomalies_flagged = [3344, 2891, 2156]
lcr = [66.6, 71.1, 78.4]  # Logical Consistency Rate

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: Precision-Recall Trade-off
ax1.plot(tolerances, precision, 'o-', linewidth=2, markersize=8,
         label='Precision (True Anomalies)', color='#2E86AB')
ax1.plot(tolerances, recall, 's-', linewidth=2, markersize=8,
         label='Recall (Valid States Retained)', color='#A23B72')
ax1.axvline(x=100, color='green', linestyle='--', alpha=0.5,
           label='Optimal (100ms)')
ax1.axvline(x=50, color='orange', linestyle='--', alpha=0.5,
           label='Safety-Critical (50ms)')

ax1.set_xlabel('Temporal Tolerance (ms)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
ax1.set_title('LISA Traffic Light: Safety-Recall Trade-off',
              fontsize=14, fontweight='bold')
ax1.legend(loc='lower right', fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.set_ylim(80, 102)

# Add annotations
ax1.annotate('97% Precision\n(Safety-Critical)',
            xy=(50, 97), xytext=(60, 92),
            arrowprops=dict(arrowstyle='->', color='black', lw=1),
            fontsize=9, ha='left')
ax1.annotate('94% Precision\n94% Recall\n(Balanced)',
            xy=(100, 94), xytext=(110, 88),
            arrowprops=dict(arrowstyle='->', color='black', lw=1),
            fontsize=9, ha='left')

# Plot 2: Anomalies Detected vs LCR
ax2_twin = ax2.twinx()

bars = ax2.bar(tolerances, anomalies_flagged, width=30, alpha=0.7,
               color='#F18F01', label='Anomalies Flagged')
line = ax2_twin.plot(tolerances, lcr, 'o-', linewidth=2, markersize=8,
                     color='#C73E1D', label='LCR (Compliance)')

ax2.set_xlabel('Temporal Tolerance (ms)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Anomalies Flagged (count)', fontsize=11, fontweight='bold',
               color='#F18F01')
ax2_twin.set_ylabel('Logical Consistency Rate (%)', fontsize=11,
                    fontweight='bold', color='#C73E1D')
ax2.set_title('Anomaly Detection vs System Compliance',
              fontsize=14, fontweight='bold')
ax2.tick_params(axis='y', labelcolor='#F18F01')
ax2_twin.tick_params(axis='y', labelcolor='#C73E1D')
ax2.grid(True, alpha=0.3, axis='x')

# Add value labels on bars
for i, (tol, anom) in enumerate(zip(tolerances, anomalies_flagged)):
    ax2.text(tol, anom + 100, f'{anom}', ha='center', fontsize=10,
             fontweight='bold')

# Combine legends
lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2_twin.get_legend_handles_labels()
ax2_twin.legend(lines1 + lines2, labels1 + labels2, loc='upper right',
                fontsize=10)

plt.tight_layout()
plt.savefig('pru_benchmark_results/lisa_precision_recall_tradeoff.png',
            dpi=300, bbox_inches='tight')
plt.savefig('pru_benchmark_results/lisa_precision_recall_tradeoff.pdf',
            bbox_inches='tight')
print("✅ Saved: pru_benchmark_results/lisa_precision_recall_tradeoff.png")
print("✅ Saved: pru_benchmark_results/lisa_precision_recall_tradeoff.pdf")

# Generate summary statistics
print("\n" + "="*60)
print("LISA Traffic Light Trade-off Summary")
print("="*60)
for i, tol in enumerate(tolerances):
    print(f"\nTolerance: {tol}ms")
    print(f"  Precision: {precision[i]}% (anomalies correctly flagged)")
    print(f"  Recall: {recall[i]}% (valid states retained)")
    print(f"  Anomalies Flagged: {anomalies_flagged[i]}")
    print(f"  LCR (Compliance): {lcr[i]}%")
    if tol == 50:
        print("  ⭐ Recommendation: Autonomous vehicles (prioritize safety)")
    elif tol == 100:
        print("  ⭐ Recommendation: Dataset cleaning (balance safety/recall)")

print("\n" + "="*60)
print("Key Insight: Vector RAG would flag 0 anomalies (100% recall, 0% safety)")
print("="*60)
