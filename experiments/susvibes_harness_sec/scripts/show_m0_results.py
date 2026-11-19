#!/usr/bin/env python3
"""把 M0 的结果真正读出来：FuncPass / SecPass / eval_status / attempts / findings / patch 字符数。

用法：
  python3 scripts/show_m0_results.py --susvibes-dir /path/to/susvibes --out runs/M0 --iid <iid>
"""
from __future__ import annotations

import argparse
import glob
import json
import os


def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return default


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
    ap.add_argument("--out", default="runs/M0")
    ap.add_argument("--iid", required=True)
    args = ap.parse_args()

    arms = []
    for name in sorted(os.listdir(args.out)):
        d = os.path.join(args.out, name)
        if os.path.isdir(d) and os.path.isdir(os.path.join(d, args.iid)):
            arms.append(name)
    if not arms:
        print("在", os.path.join(args.out, "*", args.iid), "没找到 episode.json")
        return 2

    rows = []
    for arm in arms:
        ep = load(os.path.join(args.out, arm, args.iid, "episode.json"), {}) or {}
        report_path = find_report(args.susvibes_dir, arm, args.iid)
        rep = load(report_path, {}) or {}
        run = rep.get("run") or {}
        func = (run.get("func") or {}).get("pass")
        sec = (run.get("sec") or {}).get("pass")
        rows.append({
            "arm": arm,
            "func": "PASS" if func else ("FAIL" if func is False else "?"),
            "sec": "PASS" if sec else ("FAIL" if sec is False else "?"),
            "status": rep.get("eval_status", "?"),
            "attempts": ep.get("attempts", "?"),
            "findings": ep.get("n_findings", "?"),
            "patch": ep.get("patch_chars", "?"),
            "wrote": "—",
            "err": (ep.get("agent_error") or "")[:40],
        })
        # 从 trace 里数 write_file 次数
        trace = os.path.join(args.out, arm, args.iid, "trace.jsonl")
        if os.path.exists(trace):
            n = 0
            for line in open(trace, encoding="utf-8"):
                try:
                    if json.loads(line).get("action") == "write_file":
                        n += 1
                except Exception:  # noqa: BLE001
                    pass
            rows[-1]["wrote"] = n

    print("| 臂 | FuncPass | SecPass | eval_status | attempts | findings | patch字符 | write_file次数 | agent_error |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print("| {arm} | {func} | {sec} | {status} | {attempts} | {findings} | {patch} | {wrote} | {err} |".format(**r))
    print()
    empty = [r["arm"] for r in rows if r["patch"] == 0]
    if empty:
        print("⚠️ patch 为空的臂：" + ", ".join(empty))
        print("   看它们的 trace：runs/M0/<臂>/" + args.iid + "/trace.jsonl")
        print("   - 有 write_file 但 patch=0 → 写到了仓库外/被 git 忽略")
        print("   - 没有 write_file，只有 nudge/max_steps → agent 没按协议写代码（换简单任务或换模型/加步数）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
