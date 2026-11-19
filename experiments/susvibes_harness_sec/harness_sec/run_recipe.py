"""一条命令跑一组（一个臂 × 若干任务）。

用法：
  # 零 API 干跑（假 agent + fixtures 仓库）
  python -m harness_sec.run_recipe --config harness_sec/configs/011.yaml --dry-run --out runs/dry

  # 真实跑（需先 clone susvibes + 拉镜像 + 设 DEEPSEEK_API_KEY）
  python -m harness_sec.run_recipe --config harness_sec/configs/011.yaml \
      --susvibes-dir ../susvibes --tasks <iid> --out runs/E1/011
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import sys

PKG_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(PKG_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from harness_sec import config as cfgmod  # noqa: E402
from harness_sec import sandbox  # noqa: E402
from harness_sec.agents import make_agent  # noqa: E402
from harness_sec.orchestrator import run_episode  # noqa: E402

FIXTURE_REPO = os.path.join(REPO_ROOT, "tests", "fixtures", "fake_repo")


def load_tasks(path: str, ids: list[str] | None, limit: int | None) -> list[dict]:
    tasks = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            t = json.loads(line)
            if ids and t.get("instance_id") not in ids:
                continue
            tasks.append(t)
            if limit and len(tasks) >= limit:
                break
    return tasks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--susvibes-dir", default=os.environ.get("SUSVIBES_DIR", "../susvibes"))
    ap.add_argument("--dataset", default="")
    ap.add_argument("--tasks", default="", help="逗号分隔 instance_id；空=全部（配合 --limit）")
    ap.add_argument("--tasks-file", default="", help="JSON 列表或 CSV（含 instance_id/iid 列）——冻结任务集用")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--agent", default="builtin", choices=["builtin", "dsh", "fake"])
    ap.add_argument("--model", default="")
    ap.add_argument("--max-steps", type=int, default=0, help="0=用 configs 里的 params.max_steps（默认 60）")
    ap.add_argument("--keep-repo", action="store_true")
    ap.add_argument("--no-preflight", action="store_true", help="跳过 API key 预检")
    ap.add_argument("--allow-missing-detector", action="store_true",
                    help="检测器依赖缺失（如 bandit）时仍继续跑（结果会失真）")
    ap.add_argument("--resume", action="store_true", help="跳过已有 episode.json 的任务（断点续跑）")
    ap.add_argument("--task-timeout", type=int, default=1800,
                    help="单个任务的墙钟超时（秒，默认 1800=30 分钟；0=不限）")
    args = ap.parse_args()

    cfg = cfgmod.load_arm(args.config)
    cfg["dry_run"] = bool(args.dry_run)
    if args.model:
        cfg["model"] = args.model
    os.makedirs(args.out, exist_ok=True)
    os.environ["HARNESS_USAGE_LOG"] = os.path.join(args.out, "api_usage.jsonl")
    pred_path = os.path.join(args.out, "predictions.jsonl")
    pred_first = os.path.join(args.out, "predictions_first.jsonl")
    if not args.resume:
        for p in (pred_path, pred_first):
            if os.path.exists(p):
                os.remove(p)

    if args.dry_run:
        tasks = [{"instance_id": "fixture", "problem_statement": "在 app/core.py 里给 get_note 加权限检查。",
                  "cwe_ids": ["CWE-639"], "image_name": "dry-run"}]
        repo = os.path.join(args.out, "fixture", "repo")
        if os.path.exists(repo):
            shutil.rmtree(repo)
        shutil.copytree(FIXTURE_REPO, repo)
        sandbox.ensure_git(repo)
    else:
        dataset = args.dataset or os.path.join(args.susvibes_dir, "datasets", "default", "susvibes_dataset.jsonl")
        ids = [x.strip() for x in args.tasks.split(",") if x.strip()] or None
        if args.tasks_file:
            if args.tasks_file.endswith(".json"):
                ids = list(json.load(open(args.tasks_file, encoding="utf-8")))
            else:
                import csv as _csv
                with open(args.tasks_file, encoding="utf-8") as f:
                    rows = list(_csv.DictReader(f))
                ids = [r.get("instance_id") or r.get("iid") for r in rows if r.get("ok", "True") in ("True", "true", "1", "")]
        tasks = load_tasks(dataset, ids, args.limit or None)
        if not tasks:
            print("没有匹配到任务"); return 2

    params = cfg.get("params") or {}
    max_steps = args.max_steps or int(params.get("max_steps", 60))
    print("[budget] max_steps=" + str(max_steps) + "（所有臂必须一致；改动=换一批实验）")
    # 检测器依赖检查：P 块依赖 bandit，缺失时会静默返回空，必须先报错
    m2 = cfg.get("m2")
    m2_list = m2 if isinstance(m2, list) else ([m2] if m2 else [])
    if "p" in m2_list:
        import importlib.util as _ilu
        if _ilu.find_spec("bandit") is None and not args.allow_missing_detector:
            print("\n❌ 配置用到 P 检测器（bandit），但当前环境没装 bandit。")
            print("   这会让 P 检测永远返回空，M2=p 的实验无效。")
            print("   先执行： " + sys.executable + " -m pip install bandit")
            print("   或加 --allow-missing-detector 强行跑（不推荐，数据会失真）。")
            return 2

    if not args.dry_run and not args.no_preflight:
        from harness_sec import llm as _llm
        try:
            _llm.ping(model=cfg.get("model") or None)
            print("[preflight] API key OK")
        except _llm.LLMAuthError as e:
            print("\n❌ API key 无效/过期/无余额（" + str(e)[:120] + "）")
            print("   1) 去 https://platform.deepseek.com 检查 key 与余额")
            print("   2) 重新 export DEEPSEEK_API_KEY=sk-...（新终端要重设）")
            print("   3) 再跑：python3 -c \"from harness_sec import llm; llm.ping(); print('key OK')\"")
            print("   已中止，未产生任何 predictions（避免又出现一堆 empty_patch）。")
            return 2
        except _llm.LLMError as e:
            print("[preflight] 网络/服务异常，继续尝试：" + str(e)[:120])

    class TaskTimeout(Exception):
        pass

    def _on_timeout(signum, frame):
        raise TaskTimeout()

    if args.task_timeout and args.task_timeout > 0:
        signal.signal(signal.SIGALRM, _on_timeout)

    agent = make_agent(args.agent, dry_run=args.dry_run, model=cfg.get("model") or None, max_steps=max_steps)
    summaries = []
    try:
        for task in tasks:
            if args.dry_run:
                repo = os.path.join(args.out, "fixture", "repo")
            else:
                repo = sandbox.prepare_task(task, os.path.join(args.out, "_repos"))
            out_dir = os.path.join(args.out, task["instance_id"])
            if args.resume and os.path.exists(os.path.join(out_dir, "episode.json")):
                print("[resume] 跳过已完成：" + task["instance_id"])
                summaries.append({"instance_id": task["instance_id"], "attempts": "-", "n_findings": "-",
                                  "blocked": "-", "patch_chars": "-", "skipped": True})
                continue
            try:
                if args.task_timeout and args.task_timeout > 0:
                    signal.alarm(args.task_timeout)
                summaries.append(run_episode(task, cfg, agent, repo, out_dir, pred_path=pred_path,
                                             pred_first_path=pred_first))
            except TaskTimeout:
                print("[timeout] " + task["instance_id"] + " 超过 " + str(args.task_timeout)
                      + "s，跳过（任务目录保留但无 episode.json，重跑 --resume 会重试）")
                shutil.rmtree(out_dir, ignore_errors=True)
                continue
            finally:
                if args.task_timeout and args.task_timeout > 0:
                    signal.alarm(0)
            if not args.keep_repo and not args.dry_run:
                shutil.rmtree(os.path.dirname(repo), ignore_errors=True)
    finally:
        agent.close()

    print("\n=== 汇总（" + str(cfg["arm"]) + "）===")
    for s in summaries:
        print(s["instance_id"], "attempts=" + str(s["attempts"]), "findings=" + str(s["n_findings"]),
              "blocked=" + str(s["blocked"]), "patch_chars=" + str(s["patch_chars"]))
    print("predictions ->", pred_path)
    print("下一次：python -m harness_sec.evaluate --run-id <id> --predictions " + pred_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
