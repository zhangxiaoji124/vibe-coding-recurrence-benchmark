"""零 API 假 agent：第一次写"漏洞版"，重做时写"修复版"。

只用于 tests/ 与 --dry-run：它证明的是接线正确，不是实验数据。
"""
from __future__ import annotations

import os

from .base import AgentBase


class FakeAgent(AgentBase):
    def __init__(self, mark_dir: str = "app", mark_file: str = "core.py"):
        self.mark_dir = mark_dir
        self.mark_file = mark_file

    def run(self, ctx, prompt: str) -> str:
        path = os.path.join(ctx.repo_dir, self.mark_dir, self.mark_file)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        state = "VULNERABLE" if ctx.attempt == 0 else "FIXED"
        with open(path, "w", encoding="utf-8") as f:
            f.write("# fake agent output\nSTATE = " + repr(state) + "\n")
        return "[fake-agent] attempt=" + str(ctx.attempt) + " state=" + state
