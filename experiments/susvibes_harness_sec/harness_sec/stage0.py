"""Stage 0：从候选任务里筛出可跑的（拉镜像 → 导出 /project → 查 .git 单 commit → 计时）。

用法：
  python -m harness_sec.stage0 --susvibes-dir ../susvibes --limit 5 --out runs/stage0
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time

PKG_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(PKG_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from harness_sec import sandbox  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--susvibes-dir", default=os.environ.get("SUSVIBES_DIR", "../susvibes"))
    ap.add_argument("--dataset", default="")
    ap.add_argument("--tasks", default="")
    ap.add_argument("--tasks-file", default="", help="JSON 列表（如 data/tasks_small.json）")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--out", default="runs/stage0")
    ap.add_argument("--skip-pull", action="store_true")
    args = ap.parse_args()

    dataset = args.dataset or os.path.join(args.susvibes_dir, "datasets", "default", "susvibes_dataset.jsonl")
    ids = {x.strip() for x in args.tasks.split(",") if x.strip()}
    if args.tasks_file:
        import json as _json
        ids |= set(_json.load(open(args.tasks_file, encoding="utf-8")))
    rows = []
    with open(dataset, encoding="utf-8") as f:
        for line in f:
            t = json.loads(line)
            if ids and t["instance_id"] not in ids:
                continue
            rows.append(t)
            if len(rows) >= args.limit:
                break

    os.makedirs(args.out, exist_ok=True)
    csv_path = os.path.join(args.out, "stage0.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["iid", "image", "ok", "pull_s", "extract_s", "git_commits", "note"])
        for t in rows:
            iid, image = t["instance_id"], t.get("image_name", "")
            pull_s = extract_s = -1
            ok, note, commits = False, "", ""
            try:
                if not args.skip_pull:
                    t0 = time.time()
                    last = None
                    for attempt in range(1, 4):  # 镜像站限流时重试
                        try:
                            sandbox.pull(image); last = None; break
                        except Exception as e:  # noqa: BLE001
                            last = e
                            print("  pull 失败（attempt " + str(attempt) + "/3）：" + str(e)[:120])
                            time.sleep(5 * attempt)
                    if last is not None:
                        raise last
                    pull_s = round(time.time() - t0, 1)
                t0 = time.time()
                repo = sandbox.extract_project(image, os.path.join(args.out, "_repos", iid), iid)
                extract_s = round(time.time() - t0, 1)
                commits = sandbox.git(repo, "rev-list", "--count", "HEAD", check=False).stdout.strip()
                ok = commits == "1"
                note = "" if ok else "git commits=" + commits + "（应=1）"
            except Exception as e:  # noqa: BLE001
                note = type(e).__name__ + ": " + str(e)[:200]
            w.writerow([iid, image, ok, pull_s, extract_s, commits, note])
            print(("OK  " if ok else "BAD ") + iid + " pull=" + str(pull_s) + "s extract=" + str(extract_s) + "s " + note)
    print("\nCSV ->", csv_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
