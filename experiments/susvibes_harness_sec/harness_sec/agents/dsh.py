"""可选：把外部 DSH（DeepSeek Harness）agent 接进来。

自包含包默认不用 DSH；如果你们想复用已有的 DSH agent，设置：
    export DSH_AGENT_MODULE=path.to.module      # 该模块里要有 class DshAgent
    export DSH_HOME=~/.dsh
用法：--agent dsh --model deepseek-chat
"""
from __future__ import annotations

import importlib
import os

from .base import AgentBase


class DshAgent(AgentBase):
    def __init__(self, dsh_home: str = "", model: str = "", provider: str = "deepseek-official", timeout: int = 1800):
        self.dsh_home = dsh_home or os.environ.get("DSH_HOME", os.path.expanduser("~/.dsh"))
        self.model = model or os.environ.get("DSH_MODEL", "deepseek-chat")
        self.provider = provider
        self.timeout = timeout
        self._agent = None
        self._cwd = None

    def _ensure(self, repo_dir: str):
        if self._agent is not None and self._cwd == repo_dir:
            return
        module_name = os.environ.get("DSH_AGENT_MODULE", "")
        if not module_name:
            raise RuntimeError(
                "使用 --agent dsh 需要设置 DSH_AGENT_MODULE（指向含 DshAgent 类的模块）。"
                "没有的话请用默认 --agent builtin。"
            )
        mod = importlib.import_module(module_name)
        if self._agent is not None:
            self._agent.close()
        self._agent = mod.DshAgent(dsh_home=self.dsh_home, cwd=repo_dir, provider=self.provider, model=self.model)
        if hasattr(self._agent, "set_session"):
            self._agent.set_session("harness-sec-" + os.path.basename(repo_dir)[:40])
        self._cwd = repo_dir

    def run(self, ctx, prompt: str) -> str:
        self._ensure(ctx.repo_dir)
        return self._agent.ask(prompt, timeout=self.timeout)

    def close(self) -> None:
        if self._agent is not None:
            try:
                self._agent.close()
            except Exception:  # noqa: BLE001
                pass
            self._agent = None
