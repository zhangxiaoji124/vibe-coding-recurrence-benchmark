#!/usr/bin/env python3
"""把"我们的机制增益"和"SusVibes 官方报告的策略增益"放同一张表（比 effect size，不比绝对值）。

用法：
  python3 scripts/compare_gains.py --results results/R48/results.csv
"""
from __future__ import annotations

import argparse
import csv
import os

# SusVibes 论文 Table 5（SWE-agent + Claude 4 Sonnet，186 任务）
OFFICIAL = [
    {"name": "generic（官方基线）", "func": 57.0, "sec": 11.8, "d_func": 0.0, "d_sec": 0.0, "deploy": "是"},
    {"name": "self-selection", "func": 50.0, "sec": 14.5, "d_func": -7.0, "d_sec": 2.7, "deploy": "是"},
    {"name": "oracle（上界）", "func": 55.4, "sec": 15.1, "d_func": -1.6, "d_sec": 3.3, "deploy": "否"},
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True, help="evaluate.py 产出的 results.csv")
    ap.add_argument("--baseline-arm", default="baseline", help="无机制基线的 arm 名（默认 baseline）")
    args = ap.parse_args()
    if not os.path.exists(args.results):
        print("找不到", args.results, "（先跑 48 组 + evaluate.py）")
        return 2

    rows = list(csv.DictReader(open(args.results, encoding="utf-8")))
    if not rows:
        print("results.csv 是空的")
        return 2

    def f(row, key, default=0.0):
        try:
            return float(row.get(key, default) or default)
        except ValueError:
            return default

    base = next((r for r in rows if r.get("arm") == args.baseline_arm), None)
    if base is None:
        # 没有 baseline 行就用最低 SecPass 的臂当参照
        base = min(rows, key=lambda r: f(r, "sec_rate"))
        print("⚠️ 没有找到 arm=" + args.baseline_arm + "，用 SecPass 最低的臂当基线：" + str(base.get("arm")))

    best = max(rows, key=lambda r: f(r, "sec_rate"))
    d_sec = (f(best, "sec_rate") - f(base, "sec_rate")) * 100
    d_func = (f(best, "func_rate") - f(base, "func_rate")) * 100

    print("# 机制增益 vs 官方策略增益（只比 effect size，不比绝对值）\n")
    print("## 我们的结果\n")
    print("| 臂 | n | FuncPass | SecPass | ΔSec vs 基线 | ΔFunc vs 基线 |")
    print("|---|---:|---:|---:|---:|---:|")
    print("| {}（基线） | {} | {:.1f}% | {:.1f}% | — | — |".format(
        base.get("arm"), base.get("n"), f(base, "func_rate") * 100, f(base, "sec_rate") * 100))
    print("| **{}（最优）** | {} | {:.1f}% | {:.1f}% | **{:+.1f} pp** | **{:+.1f} pp** |".format(
        best.get("arm"), best.get("n"), f(best, "func_rate") * 100, f(best, "sec_rate") * 100, d_sec, d_func))

    print("\n## 官方报告（论文 Table 5，不同模型/scaffold，仅作增益参照）\n")
    print("| 官方策略 | SecPass | ΔSec | ΔFunc | 可部署 |")
    print("|---|---:|---:|---:|---|")
    for o in OFFICIAL:
        print("| {} | {:.1f}% | {:+.1f} pp | {:+.1f} pp | {} |".format(
            o["name"], o["sec"], o["d_sec"], o["d_func"], o["deploy"]))

    print("\n## 结论模板（可直接改）\n")
    print("> 在同一评测口径下，我们的机制组合把 SecPass 提升 **{:+.1f} pp**、FuncPass 代价 **{:+.1f} pp**；".format(d_sec, d_func))
    print("> 作为参照，SusVibes 报告的可部署策略 self-selection 提升 2.7pp 但损失 7.0pp 功能，oracle 提升 3.3pp 但不可部署。")
    print("> **注意：模型与 scaffold 不同，本文只比较增益幅度，不比较绝对水平。**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
