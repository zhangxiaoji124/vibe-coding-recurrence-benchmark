#!/usr/bin/env python3
"""按"改动量"挑简单任务：golden_patch 行数越少，越适合先验证 agent 能力。

用法：
  python3 scripts/pick_small_tasks.py --dataset "$SUSVIBES_DIR/datasets/default/susvibes_dataset.jsonl" \
      --max-lines 60 --limit 10 --out data/tasks_small.json
"""
from __future__ import annotations

import argparse
import json
import os


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--core", default="", help="可选：只在这些 iid 里挑（如 core_tasks_40.json）")
    ap.add_argument("--max-lines", type=int, default=60)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--out", default="data/tasks_small.json")
    args = ap.parse_args()

    core = None
    if args.core and os.path.exists(args.core):
        raw = json.load(open(args.core, encoding="utf-8"))
        core = {x.get("iid") or x.get("instance_id") for x in raw}

    rows = []
    with open(args.dataset, encoding="utf-8") as f:
        for line in f:
            t = json.loads(line)
            if core is not None and t["instance_id"] not in core:
                continue
            gold = (t.get("golden_patch") or "").splitlines()
            files = [l[6:].strip() for l in gold if l.startswith("+++ b/")]
            n = len(gold)
            if n > args.max_lines:
                continue
            rows.append({
                "iid": t["instance_id"],
                "golden_lines": n,
                "files": files[:3],
                "cwe_ids": t.get("cwe_ids") or [],
                "ps_chars": len(t.get("problem_statement") or ""),
            })
    rows.sort(key=lambda r: (r["golden_lines"], r["ps_chars"]))
    rows = rows[: args.limit]

    print("| iid | golden 行数 | 涉及文件 | CWE | 题面字符 |")
    print("|---|---:|---|---|---:|")
    for r in rows:
        print("| {} | {} | {} | {} | {} |".format(
            r["iid"], r["golden_lines"], ", ".join(r["files"]), ",".join(r["cwe_ids"]), r["ps_chars"]))

    if rows:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump([r["iid"] for r in rows], f, ensure_ascii=False, indent=1)
        print("\n候选任务 -> " + args.out)
        print("先跑一个看看：")
        print("  python3 -m harness_sec.stage0 --susvibes-dir \"$SUSVIBES_DIR\" --tasks " + rows[0]["iid"] + " --limit 1 --out runs/M0/stage0_small")
        print("  python3 -m harness_sec.run_recipe --config harness_sec/configs/baseline.yaml --susvibes-dir \"$SUSVIBES_DIR\" --tasks " + rows[0]["iid"] + " --out runs/M0/baseline_small")
    else:
        print("没有满足 --max-lines " + str(args.max_lines) + " 的任务，调大阈值")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
