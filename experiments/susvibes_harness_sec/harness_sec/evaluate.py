"""官方评测封装：调 susvibes.eval.core，汇总 FuncPass / SecPass / SecPass|FuncPass / RescueRate。

上游评测器一行不改；本文件只负责「调用 + 读结果 + 汇总成 CSV」。

用法：
  # 单臂
  python -m harness_sec.evaluate --run-id E1_011 --predictions runs/E1/011/predictions.jsonl \
      --susvibes-dir ../susvibes --out runs/E1/011
  # 多臂汇总
  python -m harness_sec.evaluate --arms-root runs/E1 --susvibes-dir ../susvibes --csv results.csv
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import subprocess
import sys


def run_official_eval(susvibes_dir: str, predictions: str, run_id: str, max_workers: int = 3,
                      strategy: str = "none", resume: bool = True, local_images: bool = False,
                      force: bool = False) -> str:
    """调用官方评测 CLI，返回 logs 目录。

    local_images=True 时用 harness_sec.local_eval：从本地镜像评测、不联网拉取、不删镜像
    （上游默认硬编码 REMOTE + 评测后删镜像，国内镜像站限流时会失败）。
    """
    module = "harness_sec.local_eval" if local_images else "susvibes.eval.core"
    cmd = [sys.executable, "-m", module,
           "--run_id", run_id, "--predictions_path", os.path.abspath(predictions),
           "--max_workers", str(max_workers), "--strategy", strategy]
    if resume and not force:
        cmd.append("--resume")
    if force:
        cmd.append("--force")
    env = os.environ.copy()
    if local_images:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env["PYTHONPATH"] = root + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    print("[evaluate] " + " ".join(cmd) + ("  [local-images]" if local_images else ""))
    p = subprocess.run(cmd, cwd=susvibes_dir, env=env)
    log_dir = os.path.join(susvibes_dir, "logs", "eval", run_id)
    if p.returncode != 0:
        # 上游只要有一个实例内部报错（如测试日志解析失败）就会整批非零退出；
        # 已完成的 report.json 仍然有用，所以有报告就继续，只对“一个都没有”才报错。
        reports = glob.glob(os.path.join(log_dir, "*", "*", "*", "report.json"))
        if reports:
            print("[evaluate][warn] 官方评测 returncode=" + str(p.returncode)
                  + "（个别实例失败），已保留 " + str(len(reports)) + " 个报告，继续")
        else:
            raise RuntimeError("官方评测失败，returncode=" + str(p.returncode))
    return log_dir


def read_reports(log_dir: str) -> dict:
    """扫 logs/eval/<run>/<strategy>/<model>/<iid>/report.json，返回 {iid: report}。"""
    out = {}
    for base, _dirs, files in os.walk(log_dir):
        if "report.json" in files:
            iid = os.path.basename(base)
            try:
                out[iid] = json.load(open(os.path.join(base, "report.json"), encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
    return out


def summarize(reports: dict) -> dict:
    n = len(reports)
    func = sec = both = 0
    for r in reports.values():
        run = r.get("run") or {}
        f = bool((run.get("func") or {}).get("pass"))
        s = bool((run.get("sec") or {}).get("pass"))
        func += int(f); sec += int(s); both += int(f and s)
    return {
        "n": n,
        "func_pass": func,
        "sec_pass": sec,
        "sec_pass_given_func": (sec / func) if func else 0.0,
        "func_rate": (func / n) if n else 0.0,
        "sec_rate": (sec / n) if n else 0.0,
        "joint_rate": (both / n) if n else 0.0,
    }


def rescue_rate(first_log: str, final_log: str) -> dict:
    """RescueRate = 首版 SecFail 且最终 SecPass 的比例。"""
    first, final = read_reports(first_log), read_reports(final_log)
    iids = sorted(set(first) & set(final))
    rescued = eligible = 0
    for iid in iids:
        f_sec = bool((first[iid].get("run", {}).get("sec") or {}).get("pass"))
        l_sec = bool((final[iid].get("run", {}).get("sec") or {}).get("pass"))
        if not f_sec:
            eligible += 1
            rescued += int(l_sec)
    return {"rescue_eligible": eligible, "rescued": rescued,
            "rescue_rate": (rescued / eligible) if eligible else 0.0}


def bar(x: float) -> str:
    return ("%.3f" % x)


def evaluate_one(args) -> dict:
    log_dir = run_official_eval(args.susvibes_dir, args.predictions, args.run_id, args.max_workers,
                                local_images=getattr(args, "local_images", False),
                                force=getattr(args, "force", False))
    rep = read_reports(log_dir)
    s = summarize(rep)
    first = args.predictions.replace("predictions.jsonl", "predictions_first.jsonl")
    if os.path.exists(first) and not getattr(args, "no_rescue", False):
        run_official_eval(args.susvibes_dir, first, args.run_id + "_first", args.max_workers,
                          local_images=getattr(args, "local_images", False),
                          force=getattr(args, "force", False))
        s.update(rescue_rate(os.path.join(args.susvibes_dir, "logs", "eval", args.run_id + "_first"), log_dir))
    print("[evaluate] " + args.run_id + " " + json.dumps(s, ensure_ascii=False))
    return s


def summary_from_episodes(arm_dir: str) -> dict:
    blocked = attempts = findings = 0
    n = 0
    for base, _dirs, files in os.walk(arm_dir):
        if "episode.json" in files:
            try:
                ep = json.load(open(os.path.join(base, "episode.json"), encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            n += 1
            blocked += int(bool(ep.get("blocked")))
            attempts += int(ep.get("attempts") or 0)
            findings += int(ep.get("n_findings") or 0)
    return {"episodes": n, "blocked": blocked, "avg_attempts": (attempts / n) if n else 0.0,
            "avg_findings": (findings / n) if n else 0.0}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--susvibes-dir", default=os.environ.get("SUSVIBES_DIR", "../susvibes"))
    ap.add_argument("--run-id", default="")
    ap.add_argument("--predictions", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--arms-root", default="", help="多臂目录：<root>/<arm>/predictions.jsonl")
    ap.add_argument("--csv", default="results.csv")
    ap.add_argument("--max-workers", type=int, default=3)
    ap.add_argument("--force", action="store_true",
                    help="强制重评（覆盖已有 report；predictions 变了但 run_id 没变时必须用）")
    ap.add_argument("--no-rescue", action="store_true",
                    help="跳过首版补丁的评测（不算 RescueRate；筛选阶段用，省一半时间）")
    ap.add_argument("--local-images", action="store_true",
                    help="用本地镜像评测（不联网拉取、不删镜像；推荐国内网络/遇到 429 时用）")
    args = ap.parse_args()

    rows = []
    if args.arms_root:
        for arm in sorted(os.listdir(args.arms_root)):
            arm_dir = os.path.join(args.arms_root, arm)
            pred = os.path.join(arm_dir, "predictions.jsonl")
            if not os.path.exists(pred):
                continue
            a = argparse.Namespace(susvibes_dir=args.susvibes_dir, predictions=pred,
                                   run_id="eval_" + arm, max_workers=args.max_workers,
                                   local_images=args.local_images, no_rescue=args.no_rescue,
                                   force=args.force)
            s = evaluate_one(a)
            s.update(summary_from_episodes(arm_dir))
            s["arm"] = arm
            rows.append(s)
        if rows:
            keys = ["arm", "n", "func_rate", "sec_rate", "joint_rate", "sec_pass_given_func",
                    "rescue_eligible", "rescue_rate", "episodes", "blocked", "avg_attempts", "avg_findings"]
            with open(args.csv, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
                w.writeheader()
                for r in rows:
                    w.writerow(r)
            print("\nCSV ->", args.csv)
            for r in rows:
                print(r["arm"], "FuncPass=" + bar(r["func_rate"]), "SecPass=" + bar(r["sec_rate"]),
                      "SecPass|FuncPass=" + bar(r["sec_pass_given_func"]), "Rescue=" + bar(r.get("rescue_rate", 0.0)))
    elif args.predictions:
        evaluate_one(args)
    else:
        print("需要 --predictions 或 --arms-root")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
