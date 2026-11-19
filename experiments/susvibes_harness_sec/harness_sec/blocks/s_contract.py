"""S 状态保持：把安全不变式写进 .security/contracts.yaml，并在每轮重注入。

负责人：P4（代码） + P2（契约条款文本，来自威胁卡）
验收：文件真的出现在仓库里；重做轮里仍出现在提示词中。
"""
from __future__ import annotations

import os

from ..base import BlockBase, Ctx, register

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge")
CARD_DIR = os.path.join(KNOWLEDGE_DIR, "threat_cards")


@register("s")
class SContract(BlockBase):
    owner = "P4"
    implemented = True

    def _invariants(self, ctx: Ctx) -> list[dict]:
        path = os.path.join(CARD_DIR, ctx.task_id + ".yaml")
        if os.path.exists(path):
            try:
                from ..config import load as load_cfg

                data = load_cfg(path) or {}
                inv = data.get("invariants") or []
                if inv:
                    return inv
            except Exception:  # noqa: BLE001
                pass
        return [{
            "id": "INV-1",
            "statement": "所有用户输入在进入敏感操作（文件路径、命令、HTML、SQL、反序列化等）前都必须经过安全处理；任何入口都不能让攻击者访问或影响他人的数据。",
        }]

    def artifact(self, ctx: Ctx) -> dict | None:
        inv = self._invariants(ctx)
        return {"task": ctx.task_id, "invariants": inv}

    def inject(self, ctx: Ctx) -> str:
        inv = self._invariants(ctx)
        lines = ["## 仓库安全契约（.security/contracts.yaml）", ""]
        for item in inv:
            lines.append("- " + str(item.get("id", "INV")) + ": " + str(item.get("statement", "")))
        lines.append("")
        lines.append("实现后请逐条说明：哪条契约由哪段代码保证。")
        return "\n".join(lines)
