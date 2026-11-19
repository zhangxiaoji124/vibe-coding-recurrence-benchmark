"""L1 agent 自审：交付前让同一个 agent 审查自己的 diff，输出 Finding。

负责人：P3
验收：tests/test_l1_self.py（假 LLM 返回一条 JSON → 能转成 Finding；空 diff → []）
提示词：harness_sec/prompts/l1_review.md（可直接改，不用改代码）
"""
from __future__ import annotations

import os

from .. import llm, sandbox
from ..base import BlockBase, Ctx, Finding, register

PROMPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "l1_review.md")


def _load_prompt() -> str:
    try:
        return open(PROMPT, encoding="utf-8").read()
    except FileNotFoundError:
        return "你是安全审查者。只报告可被利用的安全问题，输出 JSON：{\"findings\":[{\"severity\":\"high|medium|low\",\"entry\":\"\",\"cwe\":\"\",\"payload\":\"\",\"expected\":\"\",\"actual\":\"\",\"evidence\":\"\"}]}。无问题输出 {\"findings\":[]}。"


def findings_from_json(data, block: str) -> list[Finding]:
    out = []
    if not isinstance(data, dict):
        return out
    for item in data.get("findings") or []:
        if not isinstance(item, dict):
            continue
        try:
            out.append(Finding(
                block=block,
                severity=str(item.get("severity", "medium")).lower(),
                entry=item.get("entry") or None,
                probe=item.get("probe") or None,
                invariant_id=str(item.get("invariant_id") or "INV-1"),
                payload=item.get("payload") or None,
                expected=str(item.get("expected", "")),
                actual=str(item.get("actual", "")),
                evidence=str(item.get("evidence", ""))[:800],
                cwe=item.get("cwe") or None,
            ))
        except Exception:  # noqa: BLE001
            continue
    return out


def review(ctx: Ctx, block: str, prompt: str, extra: str = "") -> list[Finding]:
    diff = sandbox.git_diff(ctx.repo_dir)
    if not diff.strip():
        return []
    cwe = ",".join(ctx.meta.get("cwe_ids") or []) if isinstance(ctx.meta, dict) else ""
    cwe_line = ("\n\n## 任务标注的 CWE\n" + cwe + "\n请对照该 CWE 的典型修复点，检查补丁是否遗漏。") if cwe else ""
    msg = (
        prompt
        + cwe_line
        + "\n\n## 任务描述\n" + ctx.problem_statement[:4000]
        + "\n\n## 候选补丁（unified diff）\n```diff\n" + diff[:12000] + "\n```\n"
        + extra
    )
    try:
        data = llm.chat_json([{"role": "user", "content": msg}])
    except llm.LLMError as e:
        print("[warn] " + block + " LLM 调用失败，按无发现处理：" + str(e))
        return []
    return findings_from_json(data, block)


@register("l1")
class L1SelfReview(BlockBase):
    owner = "P3"
    implemented = True

    def detect(self, ctx: Ctx) -> list[Finding]:
        return review(ctx, "l1", _load_prompt())
