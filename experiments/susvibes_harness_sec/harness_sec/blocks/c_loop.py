"""C 修复循环：重做轮数与停止条件（默认最多 2 轮）。

负责人：P5
验收：tests/test_c_loop.py（返回的 max_retries 与配置一致）
"""
from __future__ import annotations

from ..base import BlockBase, Ctx, register


@register("c")
class CLoop(BlockBase):
    owner = "P5"
    implemented = True

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries

    def policy(self, ctx: Ctx) -> dict:
        return {"max_retries": self.max_retries}
