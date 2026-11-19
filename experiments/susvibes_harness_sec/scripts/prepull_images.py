#!/usr/bin/env python3
"""按任务清单逐个预拉评测镜像（带重试与间隔，避开镜像站 429）。

用法：
  python3 scripts/prepull_images.py --dataset "$SUSVIBES_DIR/datasets/default/susvibes_dataset.jsonl" \
      --tasks-file data/tasks_medium.json --retries 4 --sleep 8
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--tasks-file", default="")
    ap.add_argument("--retries", type=int, default=4)
    ap.add_argument("--sleep", type=float, default=8.0)
    ap.add_argument("--platform", default="linux/amd64")
    args = ap.parse_args()

    wanted = set()
    if args.tasks_file:
        wanted = set(json.load(open(args.tasks_file, encoding="utf-8")))
    rows = [json.loads(l) for l in open(args.dataset, encoding="utf-8")]
    tasks = [r for r in rows if (not wanted or r["instance_id"] in wanted)]

    ok = fail = skip = 0
    for r in tasks:
        iid = r["instance_id"]
        image = r["image_name"]
        exists = subprocess.run(["docker", "image", "inspect", image],
                                capture_output=True, text=True).returncode == 0
        if exists:
            print("SKIP 本地已有", iid)
            skip += 1
            continue
        done = False
        for attempt in range(1, args.retries + 1):
            print("PULL", iid, "attempt", attempt)
            p = subprocess.run(["docker", "pull", "--platform", args.platform, image],
                               capture_output=True, text=True)
            if p.returncode == 0:
                print("OK  ", iid)
                ok += 1
                done = True
                break
            print("FAIL", iid, (p.stderr or p.stdout).strip().splitlines()[-1][:160])
            time.sleep(args.sleep * attempt)
        if not done:
            fail += 1
    print("\n完成：新拉 %d，已有 %d，失败 %d" % (ok, skip, fail))
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
