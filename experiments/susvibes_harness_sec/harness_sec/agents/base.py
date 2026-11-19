"""所有 agent 的公共接口。"""
from __future__ import annotations


class AgentBase:
    """在宿主机仓库目录里读/改代码；返回最后一轮的自然语言回复。"""

    def run(self, ctx, prompt: str) -> str:
        raise NotImplementedError

    def close(self) -> None:
        pass
