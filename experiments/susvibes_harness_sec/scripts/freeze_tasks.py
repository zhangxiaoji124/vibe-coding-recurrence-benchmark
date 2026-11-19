#!/usr/bin/env python3
"""从 Stage 0 的 CSV 冻结任务集：只保留 ok==True 的前 N 个，写成 JSON 列表。

用法：
  python3 scripts/freeze_tasks.py --stage0 runs/stage0/stage0.csv --n 8 --out data/tasks_8.json
"""
from __future__ import annotations

import argparse
import csv
import json
import os


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage0", required=True)
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    ids = []
    with open(args.stage0, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if str(row.get("ok", "")).strip().lower() in ("true", "1", "yes"):
                ids.append(row["iid"])
            if len(ids) >= args.n:
                break
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(ids, f, ensure_ascii=False, indent=1)
    print("冻结", len(ids), "个任务 ->", args.out)
    if len(ids) < args.n:
        print("警告：可跑任务不足", args.n, "个，先扩 Stage 0 的候选数")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
