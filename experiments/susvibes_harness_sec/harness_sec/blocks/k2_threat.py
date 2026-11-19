"""K2 任务感知知识：按任务生成/读取威胁卡（入口、数据流、要防什么）。

负责人：P2
验收：40 个任务都有威胁卡；威胁卡不含具体 payload（防止把答案泄给 agent）。
说明：威胁卡是"人写的知识"，不要在运行时让 LLM 编造关键约束。
"""
from __future__ import annotations

import os

from ..base import BlockBase, Ctx, register

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge")
CARD_DIR = os.path.join(KNOWLEDGE_DIR, "threat_cards")


@register("k2")
class K2Threat(BlockBase):
    owner = "P2"
    implemented = True

    def card_path(self, task_id: str) -> str:
        return os.path.join(CARD_DIR, task_id + ".yaml")

    def knowledge(self, ctx: Ctx) -> str:
        path = self.card_path(ctx.task_id)
        if not os.path.exists(path):
            path = os.path.join(CARD_DIR, "_template.yaml")
        if not os.path.exists(path):
            return ""
        with open(path, encoding="utf-8") as f:
            text = f.read()
        return ("## 本任务的安全威胁（务必覆盖）\n\n" + text + "\n\n")
