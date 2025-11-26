#!/usr/bin/env python3
"""
Generate URP System Architecture Diagram for Paper

Shows the validation layer architecture with neural extractors,
FOL validator, and graph storage integration.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# Create figure
fig, ax = plt.subplots(1, 1, figsize=(14, 10))
ax.set_xlim(0, 10)
ax.set_ylim(0, 12)
ax.axis('off')

# Define colors
color_input = '#E8F4F8'
color_neural = '#FFE5B4'
color_urp = '#D4E7D4'
color_storage = '#E6E6FA'
color_output = '#FFE4E1'

# Helper function for boxes
def add_box(ax, x, y, w, h, text, color, fontsize=11, bold=False):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                          edgecolor='black', facecolor=color, linewidth=2)
    ax.add_patch(box)
    weight = 'bold' if bold else 'normal'
    ax.text(x + w/2, y + h/2, text, ha='center', va='center',
            fontsize=fontsize, fontweight=weight, wrap=True)

# Helper function for arrows
def add_arrow(ax, x1, y1, x2, y2, label='', color='black'):
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                           arrowstyle='->', mutation_scale=20,
                           color=color, linewidth=2)
    ax.add_patch(arrow)
    if label:
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mid_x + 0.3, mid_y, label, fontsize=9,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# Title
ax.text(5, 11.5, 'URP: Logical Safety Layer for Agentic RAG',
        ha='center', fontsize=16, fontweight='bold')
ax.text(5, 11, 'Neuro-Symbolic Architecture with FOL Validation',
        ha='center', fontsize=12, style='italic')

# Layer 1: Input (top)
add_box(ax, 0.5, 9.5, 1.5, 0.8, 'Text\nDocuments', color_input, 10)
add_box(ax, 2.5, 9.5, 1.5, 0.8, 'Images\n(PDF pages)', color_input, 10)
add_box(ax, 4.5, 9.5, 1.5, 0.8, 'Video\nFrames', color_input, 10)
add_box(ax, 6.5, 9.5, 1.5, 0.8, 'Tables\nCSV/Excel', color_input, 10)
add_box(ax, 8.5, 9.5, 1.2, 0.8, 'IoT Logs', color_input, 10)

# Layer 2: Neural Extractors
add_box(ax, 0.3, 7.8, 2, 1, 'Claude 4.5\nSonnet\n(Text → URP)', color_neural, 10)
add_box(ax, 2.6, 7.8, 1.8, 1, 'Qwen3-VL\n(Image → URP)', color_neural, 10)
add_box(ax, 4.7, 7.8, 1.6, 1, 'YOLO+LLM\n(Video → URP)', color_neural, 10)
add_box(ax, 6.6, 7.8, 1.8, 1, 'Gemini Flash\n(Table → URP)', color_neural, 10)
add_box(ax, 8.7, 7.8, 1, 1, 'Regex\n(Log → URP)', color_neural, 9)

# Arrows: Input → Extractors
for i, x in enumerate([1.25, 3.25, 5.25, 7.25, 9.1]):
    add_arrow(ax, x, 9.5, x, 8.8)

# Central box: Extracted Relations (Raw)
add_box(ax, 1, 6.8, 8, 0.6, 'Raw Relations: (entity1, URP-type, entity2, metadata)',
        '#FFFACD', 10, bold=True)

# Arrows: Extractors → Raw Relations
for x in [1.3, 3.5, 5.5, 7.5, 9.2]:
    add_arrow(ax, x, 7.8, x if x < 5 else x - 0.5, 7.4)

# Layer 3: URP Validation Layer (CRITICAL COMPONENT)
urp_box_y = 5.5
add_box(ax, 0.5, urp_box_y, 9, 1.8, '', color_urp)  # Background box

# URP title
ax.text(5, urp_box_y + 1.5, 'URP VALIDATION LAYER (Bounded-Deterministic)',
        ha='center', fontsize=12, fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='#90EE90', edgecolor='black', linewidth=2))

# Three sub-components
add_box(ax, 0.8, urp_box_y + 0.3, 2.6, 0.9,
        'Entity Resolver\n(Cross-modal identity\nresolution)',
        '#B0E0E6', 9)
add_box(ax, 3.7, urp_box_y + 0.3, 2.6, 0.9,
        'FOL Validator\n(7 primitives,\n13 constraints)',
        '#FFB6C1', 9, bold=True)
add_box(ax, 6.6, urp_box_y + 0.3, 2.6, 0.9,
        'Anomaly Detector\n(Cycle/disjunction\nviolations)',
        '#FFD700', 9)

# Arrow from raw relations to URP layer
add_arrow(ax, 5, 6.8, 5, 7.3)

# Layer 4: Validated Graph
add_box(ax, 2, 4.5, 6, 0.8,
        'Validated Knowledge Graph (FalkorDB)\nLogical Consistency Rate: 98.4%',
        color_storage, 11, bold=True)

# Arrow: URP → Graph
add_arrow(ax, 5, urp_box_y, 5, 5.3)

# Layer 5: Query Interface
add_box(ax, 0.5, 3, 3, 0.8, 'Multi-hop Queries\n(temporal/causal chains)',
        '#F0E68C', 10)
add_box(ax, 4, 3, 3, 0.8, 'Anomaly Alerts\n(violation logs)',
        '#FFA07A', 10)
add_box(ax, 7.5, 3, 2, 0.8, 'Audit Trails\n(ISO 26262)',
        '#DDA0DD', 10)

# Arrows: Graph → Query outputs
add_arrow(ax, 3, 4.5, 2, 3.8)
add_arrow(ax, 5, 4.5, 5.5, 3.8)
add_arrow(ax, 7, 4.5, 8.5, 3.8)

# Layer 6: Integration with Agentic RAG
add_box(ax, 1.5, 1.5, 3, 0.9,
        'LangGraph\n(Agent orchestration)',
        '#E0FFFF', 10)
add_box(ax, 5.5, 1.5, 3, 0.9,
        'Vector RAG\n(Semantic search)',
        '#FFE4E1', 10)

# Arrows: Outputs → Frameworks
add_arrow(ax, 2.5, 3, 3, 2.4, 'validate()')
add_arrow(ax, 6.5, 3, 7, 2.4, 'hybrid()')

# Final output
add_box(ax, 3, 0.3, 4, 0.8,
        'Explainable Answers + Safety Guarantees',
        '#90EE90', 11, bold=True)

# Arrow: Frameworks → Output
add_arrow(ax, 3, 1.5, 4, 1.1)
add_arrow(ax, 7, 1.5, 6, 1.1)

# Add legend for 7 URP types (bottom right)
legend_x, legend_y = 0.5, 0.1
ax.text(legend_x, legend_y + 1.8, '7 Universal Relational Primitives:',
        fontsize=10, fontweight='bold')
urp_types = [
    'URP-1: Co-presence (spatial)', 'URP-2: Sequentiality (temporal)',
    'URP-3: Modulation (causal)', 'URP-4: Containment (spatial)',
    'URP-5: Disjunction (state)', 'URP-6: Perspective (observer)',
    'URP-7: Dynamics (temporal)'
]
for i, urp in enumerate(urp_types):
    y_offset = legend_y + 1.5 - (i * 0.2)
    ax.text(legend_x + 0.1, y_offset, f'• {urp}', fontsize=8)

# Add performance metrics (bottom right)
metrics_x = 7
ax.text(metrics_x, 1.2, 'Performance Metrics:', fontsize=10, fontweight='bold')
metrics = [
    'FOL Consistency: 98.4%',
    'Anomaly Detection: 33.4% (LISA)',
    'Multi-hop Accuracy: 100% vs 0%',
    'Throughput: 18,717 rel/sec',
    'Cost: ~10⁴× cheaper than CAG'
]
for i, metric in enumerate(metrics):
    y_offset = 1.0 - (i * 0.15)
    ax.text(metrics_x + 0.1, y_offset, f'✓ {metric}', fontsize=8,
            color='darkgreen')

plt.tight_layout()
plt.savefig('pru_benchmark_results/urp_architecture.png',
            dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig('pru_benchmark_results/urp_architecture.pdf',
            bbox_inches='tight', facecolor='white')
print("✅ Saved: pru_benchmark_results/urp_architecture.png")
print("✅ Saved: pru_benchmark_results/urp_architecture.pdf")
print("\n📊 Architecture diagram shows:")
print("  • Neural extractors → URP validation → Validated graph")
print("  • Integration with LangGraph/AutoGen")
print("  • 7 primitive types + FOL constraints")
print("  • Multi-hop queries + anomaly detection")
