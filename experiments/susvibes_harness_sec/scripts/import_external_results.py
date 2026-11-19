#!/usr/bin/env python3
"""导入组员提交的 R48 结果：校验 + 汇总 + 归一化拷贝。

用法：
  python3 scripts/import_external_results.py --src /path/to/R48_P2_xxx --name P2_oldver
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="组员提交的目录（下面是 01/02/... 配方目录）")
    ap.add_argument("--name", required=True, help="导入标签，如 P2_oldver")
    ap.add_argument("--tasks-file", default="data/tasks_8.json")
    ap.add_argument("--out-root", default="runs/import")
    args = ap.parse_args()

    tasks = set(json.load(open(args.tasks_file, encoding="utf-8")))
    out = os.path.join(args.out_root, args.name)
    os.makedirs(out, exist_ok=True)
    rows = []
    for recipe in sorted(d for d in os.listdir(args.src) if os.path.isdir(os.path.join(args.src, d))):
        d = os.path.join(args.src, recipe)
        pred = os.path.join(d, "predictions.jsonl")
        n_pred = sum(1 for _ in open(pred, encoding="utf-8")) if os.path.exists(pred) else 0
        eps = []
        for p in [os.path.join(root, "episode.json") for root, _dirs, files in os.walk(d) if "episode.json" in files]:
            try:
                eps.append(json.load(open(p, encoding="utf-8")))
            except Exception:  # noqa: BLE001
                pass
        iids = {e.get("instance_id") for e in eps}
        missing = sorted(tasks - iids)
        extra = sorted(iids - tasks)
        errs = sum(1 for e in eps if e.get("agent_error"))
        empty = sum(1 for e in eps if not (e.get("patch_chars") or 0))
        blocked = sum(1 for e in eps if e.get("blocked"))
        att = sum(e.get("attempts", 1) for e in eps) / len(eps) if eps else 0
        fd = sum(e.get("n_findings", 0) for e in eps) / len(eps) if eps else 0
        hit = mi = o = 0
        up = os.path.join(d, "api_usage.jsonl")
        if os.path.exists(up):
            for line in open(up, encoding="utf-8"):
                try:
                    x = json.loads(line)
                except Exception:  # noqa: BLE001
                    continue
                hit += x.get("prompt_cache_hit_tokens", 0)
                mi += x.get("prompt_cache_miss_tokens", 0)
                o += x.get("completion_tokens", 0)
        cost = hit / 1e6 * 0.5 + mi / 1e6 * 2 + o / 1e6 * 8
        ok = n_pred == len(tasks) and not missing and not extra and not errs
        rows.append({"recipe": recipe, "ok": ok, "predictions": n_pred, "episodes": len(eps),
                     "missing_tasks": ";".join(missing), "extra_tasks": ";".join(extra),
                     "agent_errors": errs, "empty_patch": empty, "blocked": blocked,
                     "avg_attempts": round(att, 2), "avg_findings": round(fd, 2), "cost_cny": round(cost, 2)})
        shutil.copytree(d, os.path.join(out, recipe), dirs_exist_ok=True)

    csv_path = os.path.join(out, "summary.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"导入 {len(rows)} 个配方 -> {out}")
    print(f"汇总 -> {csv_path}\n")
    for r in rows:
        print(f"{r['recipe']}: {'OK' if r['ok'] else '有问题'}  pred={r['predictions']} ep={r['episodes']} "
              f"err={r['agent_errors']} empty={r['empty_patch']} blocked={r['blocked']} "
              f"attempts={r['avg_attempts']} findings={r['avg_findings']} ¥{r['cost_cny']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
