"""episode 主循环：M1 注入 → agent 改代码 → M2 检测 → M3 决定 → 落盘 predictions。

只做调度；机制全在 blocks/。会同时落两份预测：
  predictions.jsonl       最终交付的 patch（主端点）
  predictions_first.jsonl 第一次尝试的 patch（用于算 RescueRate）
"""
from __future__ import annotations

import json
import os
import time

from . import sandbox
from .base import Action, Ctx, Finding, build_many


def _render_findings(findings: list[Finding]) -> str:
    lines = []
    for i, f in enumerate(findings, 1):
        lines.append(str(i) + ". [" + f.severity + "] " + (f.cwe or f.invariant_id)
                     + ((" @ " + f.entry) if f.entry else "")
                     + " | 期望: " + f.expected + " | 实际: " + f.actual
                     + ((" | payload: " + f.payload) if f.payload else ""))
    return "\n".join(lines)


def _retry_prompt(base_prompt: str, feedback_text: str, prev_patch: str) -> str:
    """重试提示：必须保留 M1 知识/契约，并把当前 diff 明确给 agent（否则会写回同一版）。"""
    p = base_prompt + "\n\n---\n【上一轮检测结果，请据此修改】\n" + feedback_text
    if prev_patch.strip():
        p += ("\n\n【当前仓库已包含你上一轮的修改，不要回退；当前 diff 如下】\n```diff\n"
              + prev_patch[:8000] + "\n```\n"
              + "请在此基础上按检测结果修改，**必须产生新的改动**；改完调用 done。")
    return p


def _write_pred(path: str, instance_id: str, model: str, patch: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    row = {"instance_id": instance_id, "model_name_or_path": model, "model_patch": patch}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_episode(task: dict, cfg: dict, agent, repo_dir: str, out_dir: str,
                pred_path: str, pred_first_path: str | None = None) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    arm = cfg.get("arm") or cfg.get("name")
    params = cfg.get("params") or {}
    model = cfg.get("model") or os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    m1_blocks = build_many(cfg.get("m1"))
    m2_blocks = build_many(cfg.get("m2"))
    m3_blocks = build_many(cfg.get("m3"))
    contract = next((b for b in m3_blocks if getattr(b, "name", "") == "s"), None)
    gate = next((b for b in m3_blocks if getattr(b, "name", "") == "a"), None)
    feedback = next((b for b in m3_blocks if getattr(b, "name", "") == "f"), None)
    policy = next((b for b in m3_blocks if getattr(b, "name", "") == "c"), None)
    max_retries = int(params.get("max_retries", 2 if policy else 0))

    meta = {k: task.get(k) for k in ("cwe_ids", "expected_pf", "project", "language") if task.get(k) is not None}
    ctx = Ctx(task_id=task["instance_id"], repo_dir=repo_dir,
              problem_statement=task["problem_statement"], arm=arm, meta=meta)
    ctx.visible["files"] = sandbox.list_files(repo_dir)
    ctx.visible["trace_path"] = os.path.join(out_dir, "trace.jsonl")

    prefix = "".join(b.knowledge(ctx) or "" for b in m1_blocks)
    base_prompt = (prefix + "\n\n" if prefix else "") + task["problem_statement"]
    prompt = base_prompt
    if contract is not None:
        art = contract.artifact(ctx)
        if art:
            sandbox.write_file(repo_dir, ".security/contracts.yaml", str(art))
            prompt = (contract.inject(ctx) or "") + "\n\n" + prompt
            base_prompt = prompt  # 重试轮必须保留契约

    history, first_patch = [], ""
    blocked, blocked_reason = False, ""
    for attempt in range(max_retries + 1):
        ctx.attempt = attempt
        if os.environ.get("HARNESS_DEBUG_PROMPT"):
            with open(os.path.join(out_dir, "prompt_attempt" + str(attempt) + ".txt"), "w", encoding="utf-8") as f:
                f.write(prompt)
        t0 = time.time()
        reply = agent.run(ctx, prompt)
        dur = round(time.time() - t0, 1)
        patch_now = sandbox.git_diff(repo_dir)
        if attempt == 0:
            first_patch = patch_now

        findings: list[Finding] = []
        for b in m2_blocks:
            try:
                findings.extend(b.detect(ctx) or [])
            except Exception as e:  # noqa: BLE001
                print("[warn] 块 " + getattr(b, "name", "?") + " 检测失败：" + type(e).__name__ + ": " + str(e))
        if gate is not None:
            action = gate.decide(findings, ctx)
        elif findings and attempt < max_retries:
            action = Action("retry", "soft retry（无硬门禁：有发现且有重做预算）")
        else:
            action = Action("deliver", "no gate")

        history.append({"attempt": attempt, "duration_s": dur, "reply_chars": len(reply or ""),
                        "reply_preview": (reply or "")[:300],
                        "agent_error": getattr(agent, "last_error", "") or "",
                        "wrote_files": getattr(agent, "wrote", "?"),
                        "n_findings": len(findings), "action": action.kind,
                        "findings": [f.to_dict() for f in findings], "patch_chars": len(patch_now)})
        print("[episode] " + task["instance_id"] + " " + str(arm) + " attempt=" + str(attempt)
              + " findings=" + str(len(findings)) + " action=" + action.kind + " " + str(dur) + "s")

        if action.kind == "deliver":
            break
        if action.kind == "block":
            blocked, blocked_reason = True, action.reason
            break
        if attempt >= max_retries:
            if gate is not None:
                blocked, blocked_reason = True, "retry exhausted"
            break
        fb = feedback.feedback(findings, ctx) if feedback is not None else _render_findings(findings)
        prompt = _retry_prompt(base_prompt, fb or _render_findings(findings), patch_now)

    final_patch = sandbox.git_diff(repo_dir)
    _write_pred(pred_path, task["instance_id"], model, final_patch)
    if pred_first_path:
        _write_pred(pred_first_path, task["instance_id"], model, first_patch)

    agent_error = getattr(agent, "last_error", "") or ""
    if not final_patch.strip():
        print("[warn] " + task["instance_id"] + " " + str(arm) + " 的 patch 为空！"
              + " 看 trace：" + ctx.visible.get("trace_path", "") + "（agent 是否 write_file）")
    episode = {
        "instance_id": task["instance_id"], "arm": arm, "blocked": blocked, "blocked_reason": blocked_reason,
        "agent_error": agent_error, "trace_path": ctx.visible.get("trace_path", ""),
        "attempts": len(history),
        "retry_changed_patch": bool(len(history) > 1 and final_patch.strip() != first_patch.strip()),
        "n_findings": sum(h["n_findings"] for h in history),
        "patch_chars": len(final_patch), "first_patch_chars": len(first_patch),
        "final_patch_empty": not bool(final_patch.strip()), "history": history,
    }
    with open(os.path.join(out_dir, "episode.json"), "w", encoding="utf-8") as f:
        json.dump(episode, f, ensure_ascii=False, indent=2)
    return episode
