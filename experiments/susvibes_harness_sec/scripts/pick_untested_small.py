#!/usr/bin/env python3
"""挑"还没跑过"的小任务（golden_patch ≤ N 行），避免重复花钱。

已跑过的判定：runs/ 下任意 episode.json 的目录名（即 iid）；也兼容日志目录。
用法：
  python3 scripts/pick_untested_small.py \
    --dataset "$SUSVIBES_DIR/datasets/default/susvibes_dataset.jsonl" \
    --max-lines 50 --limit 20 --out data/tasks_untested.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def tested_iids(runs_root: str) -> set[str]:
    out = set()
    for ep in glob.glob(os.path.join(runs_root, "**", "episode.json"), recursive=True):
        # .../runs/<...>/<iid>/episode.json
        out.add(os.path.basename(os.path.dirname(ep)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--max-lines", type=int, default=50)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--runs-root", default=os.path.join(ROOT, "runs"))
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "tasks_untested.json"))
    args = ap.parse_args()

    done = tested_iids(args.runs_root)
    rows = []
    for line in open(args.dataset, encoding="utf-8"):
        t = json.loads(line)
        n = len((t.get("golden_patch") or "").splitlines())
        if n > args.max_lines or t["instance_id"] in done:
            continue
        rows.append((n, t["instance_id"], t.get("cwe_ids") or []))
    rows.sort()
    rows = rows[: args.limit]

    print("已跑过", len(done), "个任务；本次候选（≤%d 行、未跑过）%d 个：\n" % (args.max_lines, len(rows)))
    print("| golden 行数 | iid | CWE |")
    print("|---:|---|---|")
    for n, iid, cwe in rows:
        print("| %d | %s | %s |" % (n, iid, ",".join(cwe)))
    if rows:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        json.dump([r[1] for r in rows], open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("\n候选 -> " + args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
