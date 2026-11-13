import os
import json
import glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Configure high-quality typography and anti-collision
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['mathtext.fontset'] = 'cm'

results_root = r'C:\Users\zhangxiaoji\.gemini\antigravity\scratch\vibe-coding-recurrence-benchmark\results'
output_dir = os.path.join(results_root, 'visuals')
os.makedirs(output_dir, exist_ok=True)

models = ['qwen2.5coder_7b', 'deepseek-flash']
cwe_labels = [
    'CWE-22\nPath Traversal',
    'CWE-89\nSQL Injection',
    'CWE-78\nCmd Injection',
    'CWE-79\nXSS Template',
    'CWE-918\nSSRF Webhook'
]
cwe_keys = [
    'case1_cwe22_file_storage',
    'case2_cwe89_sql_query',
    'case3_cwe78_cmd_injection',
    'case4_cwe79_xss_template',
    'case5_cwe918_ssrf_webhook'
]

# Load data
data = {}
for m in models:
    data[m] = {}
    mdir = os.path.join(results_root, m)
    for ck in cwe_keys:
        fpath = os.path.join(mdir, f"{ck}.json")
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as fp:
                data[m][ck] = json.load(fp)

# Compute longitudinal metrics
rounds = [0, 1, 2, 3, 4]
round_names = ['R0:Repair', 'R1:Ext-1', 'R2:Ext-2', 'R3:Ext-3', 'R4:Ext-4']

qwen_sec_pass = []
qwen_func_pass = []
ds_sec_pass = []
ds_func_pass = []

for r in rounds:
    q_sec = sum(1 for ck in cwe_keys if data['qwen2.5coder_7b'][ck]['rounds'][r]['probe_pass']) / 5.0 * 100
    q_fn = sum(1 for ck in cwe_keys if data['qwen2.5coder_7b'][ck]['rounds'][r]['func_pass']) / 5.0 * 100
    d_sec = sum(1 for ck in cwe_keys if data['deepseek-flash'][ck]['rounds'][r]['probe_pass']) / 5.0 * 100
    d_fn = sum(1 for ck in cwe_keys if data['deepseek-flash'][ck]['rounds'][r]['func_pass']) / 5.0 * 100
    qwen_sec_pass.append(q_sec)
    qwen_func_pass.append(q_fn)
    ds_sec_pass.append(d_sec)
    ds_func_pass.append(d_fn)

# Setup figure: 2x2 multi-panel layout (14 x 9.5 inches)
fig, axs = plt.subplots(2, 2, figsize=(14.5, 9.5), dpi=300)
fig.patch.set_facecolor('#ffffff')

# Panel 1 (Top Left): Longitudinal Trajectory: Functional Pass vs Security Pass Decay
ax1 = axs[0, 0]
ax1.set_facecolor('#f8fafc')
ax1.grid(True, linestyle='--', alpha=0.5, color='#cbd5e1', zorder=0)

# Functional lines (dashed, high)
ax1.plot(rounds, qwen_func_pass, marker='o', markersize=6, linestyle='--', color='#0284c7', linewidth=1.8, label='Qwen-7B Functional Pass', zorder=3)
ax1.plot(rounds, ds_func_pass, marker='s', markersize=6, linestyle='--', color='#7c3aed', linewidth=1.8, label='DeepSeek-Flash Functional Pass', zorder=3)

# Security lines (solid, decay curves)
ax1.plot(rounds, qwen_sec_pass, marker='D', markersize=7, linestyle='-', color='#dc2626', linewidth=2.5, label='Qwen-7B Security Retention (Drops 100% -> 40%)', zorder=4)
ax1.plot(rounds, ds_sec_pass, marker='^', markersize=7, linestyle='-', color='#059669', linewidth=2.5, label='DeepSeek-Flash Security Retention (60% -> 40%)', zorder=4)

# Highlight Divergence Gap
ax1.fill_between(rounds, qwen_sec_pass, qwen_func_pass, color='#fee2e2', alpha=0.45, label='Vibe Coding Illusion Gap (Func OK, Sec Broken)')

ax1.set_title('A. Longitudinal Decoupling: Functionality vs Security Retention', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
ax1.set_xlabel('Interactive Requirement Evolution Round', fontsize=10, fontweight='bold', color='#334155')
ax1.set_ylabel('Pass Rate (%)', fontsize=10, fontweight='bold', color='#334155')
ax1.set_xticks(rounds)
ax1.set_xticklabels(round_names, fontsize=9)
ax1.set_ylim(-5, 110)
ax1.legend(loc='lower left', fontsize=8.5, framealpha=0.95, edgecolor='#cbd5e1')

# Panel 2 (Top Right): Vulnerability Recurrence Heatmap Matrix
ax2 = axs[0, 1]
ax2.set_facecolor('#f8fafc')

# Build a combined status grid: 10 rows (5 Qwen, 5 DeepSeek) x 5 rounds
# Status code mapping: 1.0=SECURE(green), 0.5=FAIL_REPAIR(orange), 0.0=RECURRENCE(red)
matrix_vals = np.zeros((10, 5))
cell_texts = []

row_labels = [
    'Qwen: CWE-22 PathTrav',
    'Qwen: CWE-89 SQLi',
    'Qwen: CWE-78 CmdInj',
    'Qwen: CWE-79 XSS',
    'Qwen: CWE-918 SSRF',
    'DS: CWE-22 PathTrav',
    'DS: CWE-89 SQLi',
    'DS: CWE-78 CmdInj',
    'DS: CWE-79 XSS',
    'DS: CWE-918 SSRF'
]

for idx, ck in enumerate(cwe_keys):
    # Qwen
    q_rounds = data['qwen2.5coder_7b'][ck]['rounds']
    row_text_q = []
    for r_i in range(5):
        st = q_rounds[r_i]['recurrence_status']
        if st in ['REPAIRED_SECURE', 'PERSISTENT_SECURE']:
            matrix_vals[idx, r_i] = 1.0
            row_text_q.append('SEC')
        elif 'RECURRENCE' in st:
            matrix_vals[idx, r_i] = 0.0
            row_text_q.append('RECUR!')
        elif 'ERASURE' in st:
            matrix_vals[idx, r_i] = 0.1
            row_text_q.append('ERASE')
        else:
            matrix_vals[idx, r_i] = 0.4
            row_text_q.append('FAIL')
    cell_texts.append(row_text_q)

for idx, ck in enumerate(cwe_keys):
    # DeepSeek
    d_rounds = data['deepseek-flash'][ck]['rounds']
    row_text_d = []
    for r_i in range(5):
        st = d_rounds[r_i]['recurrence_status']
        if st in ['REPAIRED_SECURE', 'PERSISTENT_SECURE']:
            matrix_vals[idx + 5, r_i] = 1.0
            row_text_d.append('SEC')
        elif 'RECURRENCE' in st or 'RECURRED' in st:
            matrix_vals[idx + 5, r_i] = 0.0
            row_text_d.append('RECUR!')
        elif 'ERASURE' in st:
            matrix_vals[idx + 5, r_i] = 0.1
            row_text_d.append('ERASE')
        else:
            matrix_vals[idx + 5, r_i] = 0.4
            row_text_d.append('FAIL')
    cell_texts.append(row_text_d)

from matplotlib.colors import LinearSegmentedColormap
# Custom Colormap: Red (0.0) -> Orange (0.4) -> Green (1.0)
cmap = LinearSegmentedColormap.from_list('vuln_cmap', ['#ef4444', '#f97316', '#22c55e'], N=256)
im = ax2.imshow(matrix_vals, cmap=cmap, aspect='auto', vmin=0.0, vmax=1.0)

for r in range(10):
    for c in range(5):
        txt = cell_texts[r][c]
        color = '#ffffff' if matrix_vals[r, c] < 0.3 or matrix_vals[r, c] > 0.8 else '#000000'
        ax2.text(c, r, txt, ha='center', va='center', fontsize=7.5, fontweight='bold', color=color)

ax2.axhline(4.5, color='#0f172a', linewidth=2.0, linestyle='-')
ax2.set_xticks(range(5))
ax2.set_xticklabels(round_names, fontsize=8.5)
ax2.set_yticks(range(10))
ax2.set_yticklabels(row_labels, fontsize=8)
ax2.set_title('B. Multi-Turn Vulnerability State Matrix (Qwen-7B vs DeepSeek)', fontsize=12, fontweight='bold', pad=12, color='#0f172a')

# Panel 3 (Bottom Left): Recurrence Modes & Root Cause Decomposition
ax3 = axs[1, 0]
ax3.set_facecolor('#f8fafc')
ax3.grid(True, axis='x', linestyle='--', alpha=0.5, color='#cbd5e1', zorder=0)

categories = [
    'Lateral Sibling Recurrence\n(New Entry Point Omission)',
    'Defensive Erasure\n(Global Refactoring Regression)',
    'Context Attention Drift\n(Security Invariant Decay)',
    'Point vs Structural Patching\n(Abstraction Barrier Gap)'
]
qwen_counts = [3, 3, 4, 3]  # Quantitative frequencies observed
ds_counts = [1, 2, 2, 1]

y_pos = np.arange(len(categories))
bar_height = 0.35

ax3.barh(y_pos - bar_height/2, qwen_counts, height=bar_height, color='#3b82f6', label='Qwen2.5-Coder:7B', edgecolor='#1d4ed8', zorder=3)
ax3.barh(y_pos + bar_height/2, ds_counts, height=bar_height, color='#10b981', label='DeepSeek-Flash', edgecolor='#047857', zorder=3)

for i, v in enumerate(qwen_counts):
    ax3.text(v + 0.1, i - bar_height/2, f"{v} cases", va='center', fontsize=8.5, fontweight='bold', color='#1e3a8a')
for i, v in enumerate(ds_counts):
    ax3.text(v + 0.1, i + bar_height/2, f"{v} cases", va='center', fontsize=8.5, fontweight='bold', color='#064e3b')

ax3.set_yticks(y_pos)
ax3.set_yticklabels(categories, fontsize=8.5)
ax3.set_xlabel('Affected Case Frequency (Out of 5 Cases)', fontsize=10, fontweight='bold', color='#334155')
ax3.set_xlim(0, 5)
ax3.set_title('C. Recurrence Phenomenon Taxonomy & Failure Modes', fontsize=12, fontweight='bold', pad=12, color='#0f172a')
ax3.legend(loc='lower right', fontsize=8.5, framealpha=0.95, edgecolor='#cbd5e1')

# Panel 4 (Bottom Right): Recurrence Lifecycle & PACG Defense Intervention
ax4 = axs[1, 1]
ax4.set_facecolor('#f8fafc')
ax4.axis('off')

# Draw clean modern architecture card representing the Proposed PACG Gateway Defense
card1 = patches.FancyBboxPatch((0.05, 0.55), 0.90, 0.40, boxstyle="round,pad=0.03", edgecolor="#3b82f6", facecolor="#eff6ff", linewidth=1.5)
ax4.add_patch(card1)

ax4.text(0.50, 0.88, "Observed Vulnerability Recurrence Lifecycle", ha='center', va='center', fontsize=10.5, fontweight='bold', color='#1e3a8a')
ax4.text(0.10, 0.76, "[R0] Prompt: 'Fix CWE-22' -> LLM patches target file -> Security probe PASS", fontsize=8.2, color='#1e293b')
ax4.text(0.10, 0.68, "[R1~R2] Prompt: 'Add delete_file' -> LLM creates sibling func without guard -> RECUR!", fontsize=8.2, fontweight='bold', color='#b91c1c')
ax4.text(0.10, 0.60, "[R3~R4] Prompt: 'Add preview' -> LLM refactors entire file -> Erases earlier guards -> FAIL", fontsize=8.2, color='#b91c1c')

card2 = patches.FancyBboxPatch((0.05, 0.05), 0.90, 0.45, boxstyle="round,pad=0.03", edgecolor="#10b981", facecolor="#ecfdf5", linewidth=1.5)
ax4.add_patch(card2)

ax4.text(0.50, 0.43, "Proposed Defense: AST Invariant Pinning & PACG Gateway", ha='center', va='center', fontsize=10.5, fontweight='bold', color='#065f46')
ax4.text(0.10, 0.33, "1. Invariant Pinning: Extract AST security guards (e.g. resolve_path) as persistent invariants", fontsize=8.0, color='#0f172a')
ax4.text(0.10, 0.25, "2. Sibling Cross-Check: Intercept new entry points & enforce inherited security contracts", fontsize=8.0, color='#0f172a')
ax4.text(0.10, 0.17, "3. PACG Runtime Gateway: Execute dynamic security probes before commit to developer", fontsize=8.0, color='#0f172a')
ax4.text(0.10, 0.09, "4. Verification Output: Closed-loop repair without developer cognitive burden", fontsize=8.0, color='#0f172a')

ax4.set_title('D. Mechanism Dynamics & PACG Architectural Solution', fontsize=12, fontweight='bold', pad=12, color='#0f172a')

plt.tight_layout()

# Save PNG and PDF
png_path = os.path.join(output_dir, 'recurrence_benchmark_report.png')
pdf_path = os.path.join(output_dir, 'recurrence_benchmark_report.pdf')
plt.savefig(png_path, dpi=300, bbox_inches='tight')
plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"[OK] Visuals saved to:\n  {png_path}\n  {pdf_path}")
