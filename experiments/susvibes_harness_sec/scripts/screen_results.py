#!/usr/bin/env python3
"""多任务筛选结果：读 runs/screen/<臂>/<iid>/episode.json + 官方 report.json，输出表 + 分类。

用法：
  python3 scripts/screen_results.py --susvibes-dir "$SUSVIBES_DIR" --out runs/screen/baseline
"""
from __future__ import annotations

import argparse
import glob
import json
import os


def load(p, d=None):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return d


def find_report(base: str, arm: str, iid: str) -> str:
    if not os.path.isdir(base):
        return ""
    cands = []
    for run in os.listdir(base):
        if not run.startswith("M0") or run.endswith("_first"):
            continue
        if not (run == "M0_" + arm or run.endswith("_" + arm)):
            continue
        cands.extend(glob.glob(os.path.join(base, run, "*", "*", iid, "report.json")))
    # 同一任务可能在多个 run 里都有报告（旧 run 残留）→ 取最新修改的那份
    return max(cands, key=lambda p: os.path.getmtime(p)) if cands else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--susvibes-dir", required=True)
    ap.add_argument("--out", required=True, help="runs/screen/<臂>")
    ap.add_argument("--set-name", default="")
    args = ap.parse_args()

    arm = os.path.basename(args.out.rstrip("/"))
    evals = os.path.join(args.susvibes_dir, "logs", "eval")
    rows = []
    for iid in sorted(os.listdir(args.out)):
        d = os.path.join(args.out, iid)
        if not os.path.isdir(d) or not os.path.isdir(os.path.join(d, "repo")):
            # 没有 repo 说明不是任务目录（_repos 等）
            if not os.path.exists(os.path.join(d, "episode.json")):
                continue
        ep = load(os.path.join(d, "episode.json"), {}) or {}
        rep = load(find_report(evals, arm, iid), {}) or {}
        run = rep.get("run") or {}
        f = (run.get("func") or {}).get("pass")
        s = (run.get("sec") or {}).get("pass")
        rows.append({
            "iid": iid,
            "func": "PASS" if f else ("FAIL" if f is False else "?"),
            "sec": "PASS" if s else ("FAIL" if s is False else "?"),
            "status": rep.get("eval_status", "?"),
            "patch": ep.get("patch_chars", "?"),
            "attempts": ep.get("attempts", "?"),
        })

    print("| iid | FuncPass | SecPass | eval_status | patch字符 | attempts |")
    print("|---|---|---|---|---:|---:|")
    for r in rows:
        print("| {} | {} | {} | {} | {} | {} |".format(r["iid"], r["func"], r["sec"], r["status"], r["patch"], r["attempts"]))

    both = [r for r in rows if r["func"] == "PASS" and r["sec"] == "PASS"]
    func_only = [r for r in rows if r["func"] == "PASS" and r["sec"] == "FAIL"]
    func_fail = [r for r in rows if r["func"] == "FAIL"]
    print("\n## 分类（这个集合有 {} 个任务）".format(len(rows)))
    print("- ✅ 功能+安全都过（天花板，只能测\"不破坏\"）：{}".format(len(both)))
    print("- 🎯 **功能过但安全不过（机制的目标场景！）**：{}".format(len(func_only)))
    for r in func_only:
        print("    - " + r["iid"])
    print("- ❌ 功能不过（任务太难/agent 不行，建议剔除）：{}".format(len(func_fail)))
    for r in func_fail:
        print("    - " + r["iid"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
