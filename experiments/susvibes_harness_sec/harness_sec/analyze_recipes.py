"""48 组配方分析：每个配方的 FuncPass/SecPass、相对基线的 Δ、以及各机制的边际效应。

输入：<susvibes>/logs/eval/eval_<arm>/.../<iid>/report.json
  - 基线：eval_baseline（或 eval_000）
  - 配方：eval_01 ... eval_48

用法：
  python -m harness_sec.analyze_recipes --eval-root ../susvibes/logs/eval --out results/R48
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - half) / d, (c + half) / d)


def read_arm(eval_root: str, run_name: str) -> dict:
    out = {}
    root = os.path.join(eval_root, run_name)
    if not os.path.isdir(root):
        return out
    for base, _dirs, files in os.walk(root):
        if "report.json" in files:
            try:
                r = json.load(open(os.path.join(base, "report.json"), encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            run = r.get("run") or {}
            out[os.path.basename(base)] = {
                "func": bool((run.get("func") or {}).get("pass")),
                "sec": bool((run.get("sec") or {}).get("pass")),
            }
    return out


def rate(d: dict, key: str):
    return sum(1 for v in d.values() if v.get(key)), len(d)


def rank_table(data: dict, baseline: dict | None, arms: list[str]) -> list[dict]:
    rows = []
    base_sec, base_n = rate(baseline, "sec") if baseline else (0, 0)
    base_func, _ = rate(baseline, "func") if baseline else (0, 0)
    for arm in arms:
        d = data.get(arm) or {}
        if not d:
            continue
        f, n = rate(d, "func")
        s, _ = rate(d, "sec")
        joint = sum(1 for v in d.values() if v.get("func") and v.get("sec"))
        common = set(d) & set(baseline or {})
        if common:
            bs = sum(1 for i in common if baseline[i]["sec"]) / len(common)
            bf = sum(1 for i in common if baseline[i]["func"]) / len(common)
            delta_sec = s / n - bs
            delta_func = f / n - bf
        else:
            delta_sec = (s / n) - (base_sec / base_n if base_n else 0.0)
            delta_func = (f / n) - (base_func / base_n if base_n else 0.0)
        lo, hi = wilson(s, n)
        rows.append({"arm": arm, "n": n, "func_pass": f, "func_rate": f / n,
                     "sec_pass": s, "sec_rate": s / n, "sec_ci_lo": lo, "sec_ci_hi": hi,
                     "joint_rate": joint / n, "delta_sec": delta_sec, "delta_func": delta_func})
    rows.sort(key=lambda r: (-r["sec_rate"], -r["joint_rate"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


def marginal(data: dict, level_of: dict, key: str = "sec") -> dict:
    """按某个机制的水平做边际平均（3×4×4 设计的主效应估计）。"""
    agg: dict[str, list[float]] = {}
    for arm, d in data.items():
        if not d or arm not in level_of:
            continue
        k = sum(1 for v in d.values() if v.get(key))
        agg.setdefault(level_of[arm], []).append(k / len(d))
    return {lv: (sum(v) / len(v), len(v)) for lv, v in agg.items()}


def load_levels(path: str) -> dict:
    """从 data/recipe_assignment.json 读每个配方的三个水平。"""
    out = {}
    if os.path.exists(path):
        for r in json.load(open(path, encoding="utf-8")):
            out["%02d" % r["combo"]] = (r["m1"], r["m2"], r["m3"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-root", required=True)
    ap.add_argument("--baseline", default="eval_baseline")
    ap.add_argument("--arms", nargs="+", default=["%02d" % i for i in range(1, 49)])
    ap.add_argument("--assignment", default=os.path.join("data", "recipe_assignment.json"))
    ap.add_argument("--out", default="results/R48")
    args = ap.parse_args()

    baseline = read_arm(args.eval_root, args.baseline) or read_arm(args.eval_root, "eval_000")
    data = {a: read_arm(args.eval_root, "eval_" + a) for a in args.arms}
    rows = rank_table(data, baseline, args.arms)
    os.makedirs(args.out, exist_ok=True)

    with open(os.path.join(args.out, "recipes_rank.csv"), "w", newline="", encoding="utf-8") as f:
        keys = ["rank", "arm", "n", "func_rate", "sec_rate", "sec_ci_lo", "sec_ci_hi",
                "joint_rate", "delta_sec", "delta_func"]
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    md = ["# 48 组配方结果", "",
          "基线（eval_000/baseline）：FuncPass=%d/%d，SecPass=%d/%d" % (*rate(baseline, "func")[:1], rate(baseline, "func")[1], *rate(baseline, "sec")[:1], rate(baseline, "sec")[1]) if baseline else "基线缺失",
          "",
          "| 排名 | 组 | n | FuncPass | SecPass [95%] | Joint | ΔSec vs 基线 | ΔFunc vs 基线 |",
          "|---:|---|---:|---:|---|---:|---:|---:|"]
    for r in rows:
        md.append("| %d | %s | %d | %.3f | %.3f [%.3f, %.3f] | %.3f | %+.3f | %+.3f |" % (
            r["rank"], r["arm"], r["n"], r["func_rate"], r["sec_rate"], r["sec_ci_lo"], r["sec_ci_hi"],
            r["joint_rate"], r["delta_sec"], r["delta_func"]))

    levels = load_levels(args.assignment)
    if levels:
        md += ["", "## 机制边际效应（各水平上的平均 SecPass）", "",
               "| 机制 | 水平 | 平均 SecPass | 组数 |", "|---|---|---:|---:|"]
        for i, label in enumerate(("M1", "M2", "M3")):
            lv_of = {a: levels[a][i] for a in levels}
            for lv, (m, cnt) in sorted(marginal(data, lv_of).items(), key=lambda x: -x[1][0]):
                md.append("| %s | %s | %.3f | %d |" % (label, lv, m, cnt))
    md += ["", "> 注意：每组 n 较小（8–12 个任务），排名只能看**方向和区间**，不要宣称显著；确认阶段见 docs/EXPERIMENT_48.md。"]
    text = "\n".join(md) + "\n"
    open(os.path.join(args.out, "recipes_rank.md"), "w", encoding="utf-8").write(text)
    print(text[:2000])
    print("\n输出：", os.path.join(args.out, "recipes_rank.csv"), "| recipes_rank.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
