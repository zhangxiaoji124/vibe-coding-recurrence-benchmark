#!/usr/bin/env python3
"""生成 SusVibes 官方策略增强数据集（作为对照臂），并复制到本仓库 data/official/。

官方策略（上游 susvibes/eval/strategies）：
  generic         通用安全提示（官方 agent harness 的默认行为）
  self-selection  agent 自选相关 CWE（官方主推的可部署策略）
  oracle          直接告诉真实 CWE（上界，不可部署）
  feedback-driven 用隐藏测试日志反馈（会泄漏，上界参考，官方标注 coming soon）
  sec-test        把隐藏安全测试给 agent（泄漏，上界参考）

用法：
  python3 scripts/prepare_official_strategies.py --susvibes-dir ../susvibes \
      --strategies generic self-selection oracle --run-id official
"""
from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--susvibes-dir", default=os.environ.get("SUSVIBES_DIR", "../susvibes"))
    ap.add_argument("--dataset-id", default="default")
    ap.add_argument("--strategies", nargs="+", default=["generic", "self-selection", "oracle"])
    ap.add_argument("--run-id", default="official")
    ap.add_argument("--out-dir", default="data/official")
    args = ap.parse_args()

    ds_dir = os.path.join(args.susvibes_dir, "datasets", args.dataset_id)
    if not os.path.isdir(ds_dir):
        print("找不到数据集目录：" + ds_dir, file=sys.stderr)
        return 2
    os.makedirs(args.out_dir, exist_ok=True)

    records = []
    for strat in args.strategies:
        cmd = [sys.executable, "-m", "susvibes.eval.core", "--prepare_dataset",
               "--dataset_id", args.dataset_id, "--strategy", strat, "--run_id", args.run_id]
        print("[prepare] " + " ".join(cmd))
        p = subprocess.run(cmd, cwd=args.susvibes_dir)
        if p.returncode != 0:
            print("生成失败：" + strat, file=sys.stderr)
            continue
        cands = sorted(glob.glob(os.path.join(ds_dir, "*_" + args.run_id + "_" + strat + ".jsonl")))
        if not cands:
            print("找不到生成的 jsonl（" + strat + "）", file=sys.stderr)
            continue
        src = cands[-1]
        dst = os.path.join(args.out_dir, strat + ".jsonl")
        shutil.copy2(src, dst)
        n = sum(1 for _ in open(dst, encoding="utf-8"))
        records.append((strat, dst, n))
        print("  -> " + dst + "（" + str(n) + " 行）")

    commit = ""
    try:
        commit = subprocess.run(["git", "-C", args.susvibes_dir, "rev-parse", "HEAD"],
                                capture_output=True, text=True).stdout.strip()
    except Exception:  # noqa: BLE001
        pass
    md = ["# 官方策略增强数据集（对照臂用）", "",
          "- 上游：https://github.com/LeiLiLab/susvibes",
          "- commit：" + (commit or "（记录失败）"),
          "- 生成命令：`python3 scripts/prepare_official_strategies.py --strategies " + " ".join(args.strategies) + "`",
          "- 用途：作为「现有安全策略」的对照；**主对照建议用 `self-selection`**（官方最强的可部署策略），`generic` 作官方默认，`oracle` 只作上界。",
          "",
          "| 策略 | 文件 | 任务数 | 说明 |", "|---|---|---:|---|"]
    notes = {
        "generic": "通用安全提示（官方 harness 默认）",
        "self-selection": "agent 自选 CWE（官方主推可部署策略，**主对照**）",
        "oracle": "真实 CWE（信息上界，不可部署）",
        "feedback-driven": "隐藏测试日志反馈（泄漏，仅上界参考）",
        "sec-test": "隐藏安全测试（泄漏，仅上界参考）",
    }
    for strat, dst, n in records:
        md.append("| " + strat + " | `" + dst + "` | " + str(n) + " | " + notes.get(strat, "") + " |")
    md += ["", "> 这些文件只是把策略文本拼进 `problem_statement`；评测器、agent、任务都不变。"]
    open(os.path.join(args.out_dir, "README.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n完成 ->", args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
