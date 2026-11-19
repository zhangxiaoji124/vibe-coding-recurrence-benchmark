"""agent 适配层：builtin（自包含）/ dsh（可选）/ fake（dry-run）。"""
from .base import AgentBase
from .fake import FakeAgent
from .builtin import BuiltinAgent


def make_agent(kind: str = "builtin", dry_run: bool = False, **kw) -> AgentBase:
    if dry_run or kind == "fake":
        return FakeAgent()
    if kind == "builtin":
        return BuiltinAgent(**kw)
    if kind == "dsh":
        from .dsh import DshAgent

        return DshAgent(**kw)
    raise ValueError("未知 agent 类型：" + repr(kind) + "（builtin / dsh / fake）")
