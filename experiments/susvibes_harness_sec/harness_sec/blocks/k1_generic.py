"""K1 通用安全知识：给 agent 一份通用安全编码规则（CWE/OWASP 摘要）。

负责人：P2
验收：在 case01/02 类任务上，注入文本里出现对应 CWE 编号；其他轮消息不变。
说明：官方 SusVibes 已有 GENERIC_PROMPT，本块是它的"可控版本"（可替换文本、可对比 A0 空知识）。
"""
from __future__ import annotations

import os

from ..base import BlockBase, Ctx, register

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge")


@register("k1")
class K1Generic(BlockBase):
    owner = "P2"
    implemented = True

    def __init__(self, path: str | None = None):
        self.path = path or os.path.join(KNOWLEDGE_DIR, "cwe_top25.md")

    def knowledge(self, ctx: Ctx) -> str:
        try:
            with open(self.path, encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            return ""
        return "## 安全编码要求（通用）\n\n" + text + "\n\n"
