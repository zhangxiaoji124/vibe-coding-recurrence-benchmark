"""统计：从官方评测的 per-instance report.json 读数据，算主效应与 M2×M3 交互。

输入：--eval-root <susvibes>/logs/eval，里面是 eval_<arm>/.../<iid>/report.json
输出：markdown 表 + 每个量的 Wilson 95% 区间（不依赖 scipy）。

用法：
  python -m harness_sec.analyze --eval-root ../susvibes/logs/eval --arms 000 100 010 001 110 101 011 111
"""
from __future__ import annotations

import argparse
import json
import math
import os


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - half) / d, (c + half) / d)


def read_arm(eval_root: str, arm: str) -> dict:
    out = {}
    for name in os.listdir(eval_root):
        if name == "eval_" + arm or name.startswith("eval_" + arm + "_"):
            for base, _dirs, files in os.walk(os.path.join(eval_root, name)):
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
                if name.endswith("_first"):
                    continue
    return out


def rate(data: dict, key: str) -> tuple[int, int]:
    n = len(data)
    k = sum(1 for v in data.values() if v.get(key))
    return k, n


def fmt(name: str, k: int, n: int) -> str:
    lo, hi = wilson(k, n)
    return "| " + name + " | " + str(k) + "/" + str(n) + " | %.3f | [%.3f, %.3f] |" % ((k / n) if n else 0, lo, hi)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-root", required=True)
    ap.add_argument("--arms", nargs="+", default=["000", "100", "010", "001", "110", "101", "011", "111"])
    args = ap.parse_args()

    data = {a: read_arm(args.eval_root, a) for a in args.arms}
    lines = ["# 结果汇总", "",
             "| 臂 | SecPass | 比例 | Wilson 95% |", "|---|---|---|---|"]
    for a in args.arms:
        k, n = rate(data[a], "sec")
        lines.append(fmt(a, k, n))
    lines += ["", "| 臂 | FuncPass | 比例 | Wilson 95% |", "|---|---|---|---|"]
    for a in args.arms:
        k, n = rate(data[a], "func")
        lines.append(fmt(a, k, n))

    # 主效应（因子 = 开/关，跨该因子的所有臂池化，按任务配对）
    lines += ["", "## 主效应（开 vs 关，按任务配对）", "",
              "| 因子 | 开 | 关 | 差值（开−关） |", "|---|---|---|---|"]
    all_iids = set()
    for a in args.arms:
        all_iids |= set(data[a])
    for idx, label in enumerate(["M1", "M2", "M3"]):
        on_sum = off_sum = 0.0
        n = 0
        for iid in all_iids:
            on_vals = [data[a][iid]["sec"] for a in args.arms if a[idx] == "1" and iid in data[a]]
            off_vals = [data[a][iid]["sec"] for a in args.arms if a[idx] == "0" and iid in data[a]]
            if not on_vals or not off_vals:
                continue
            on_sum += sum(on_vals) / len(on_vals)
            off_sum += sum(off_vals) / len(off_vals)
            n += 1
        if n:
            on_m, off_m = on_sum / n, off_sum / n
            lines.append("| " + label + " | %.3f | %.3f | %+.3f |" % (on_m, off_m, on_m - off_m))
        else:
            lines.append("| " + label + " | — | — | 无配对数据 |")

    # M2×M3 交互：DiD = (011 - 001) - (010 - 000)
    lines += ["", "## M2×M3 交互（DiD）", ""]
    if all(a in data for a in ("000", "010", "001", "011")):
        iids = set(data["000"]) & set(data["010"]) & set(data["001"]) & set(data["011"])
        if iids:
            def avg(a):
                return sum(1 for i in iids if data[a][i]["sec"]) / len(iids)
            did = (avg("011") - avg("001")) - (avg("010") - avg("000"))
            lines.append("DiD = [SecPass(011) − SecPass(001)] − [SecPass(010) − SecPass(000)] = **%+.3f**" % did)
            lines.append("")
            lines.append("> n=" + str(len(iids)) + " 个配对任务；小样本下只报效应量与区间，不单靠 p 值下结论。")
    md = "\n".join(lines)
    print(md)
    out = os.path.join(args.eval_root, "summary_table.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md + "\n")
    print("\n表 ->", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
