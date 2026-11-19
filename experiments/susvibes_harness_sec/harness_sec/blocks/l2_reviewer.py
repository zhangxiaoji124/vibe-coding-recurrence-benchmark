"""L2 独立审查：换一个独立角色/会话审 diff，避免自审偏见。

负责人：P3
验收：tests/test_l2_reviewer.py（与 L1 使用不同 prompt；能转成 Finding）
提示词：harness_sec/prompts/l2_review.md
"""
from __future__ import annotations

import os

from ..base import BlockBase, Ctx, Finding, register

_SEV = {"high": 0, "medium": 1, "low": 2}


def filter_findings(findings: list[Finding], max_n: int | None = None) -> list[Finding]:
    """去重（同 CWE+入口只留一条）并按严重度排序，最多保留 max_n 条。"""
    import os
    if max_n is None:
        try:
            max_n = int(os.environ.get("HARNESS_L2_MAX_FINDINGS", "3"))
        except ValueError:
            max_n = 3
    seen, out = set(), []
    for f in sorted(findings, key=lambda x: _SEV.get(x.severity, 9)):
        key = (f.cwe, f.entry, f.evidence[:80])
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out[:max_n]
from .l1_self import review

PROMPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "l2_review.md")


def _load_prompt() -> str:
    try:
        return open(PROMPT, encoding="utf-8").read()
    except FileNotFoundError:
        return "你是独立安全审计员。假设这个补丁里一定藏着至少一个安全缺陷；只报告可被利用的问题，输出 JSON {\"findings\":[...]}；确实没有就输出 {\"findings\":[]}。"


@register("l2")
class L2Reviewer(BlockBase):
    owner = "P3"
    implemented = True

    def detect(self, ctx: Ctx) -> list[Finding]:
        got = review(ctx, "l2", _load_prompt(), extra="\n请特别检查：授权/越权、输入未校验、输出未编码、敏感信息泄漏。\n")
        return filter_findings(got)
