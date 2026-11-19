"""K3 仓库感知知识：检索仓库里已有的安全实现与规范，拼成注入文本。

负责人：P2
验收：tests/test_k3_repo.py（能从 fixture 仓库里找到权限校验/转义函数并引用；找不到返回空串）
"""
from __future__ import annotations

import os
import re

from .. import sandbox
from ..base import BlockBase, Ctx, register

SEC_NAME = re.compile(r"(auth|permission|perm|escape|sanitiz|validat|safe|security|csrf|token|password|path|quote|serializ|sql)", re.I)
DOC_NAMES = ("SECURITY.md", "security.md", "CONTRIBUTING.md", "docs/security.md")


@register("k3")
class K3Repo(BlockBase):
    owner = "P2"
    implemented = True

    def knowledge(self, ctx: Ctx) -> str:
        repo = ctx.repo_dir
        lines = ["## 仓库里已有的安全实现（优先复用，不要另发明一套）", ""]
        found = 0
        for rel in sandbox.list_files(repo, limit=400):
            if not SEC_NAME.search(rel):
                continue
            try:
                text = sandbox.read_file(repo, rel)
            except Exception:  # noqa: BLE001
                continue
            defs = [m.group(1) for m in re.finditer(r"^\s*def\s+(\w+)", text, re.M) if SEC_NAME.search(m.group(1))]
            if defs:
                lines.append("- " + rel + "：" + "；".join(sorted(set(defs))[:6]))
                found += 1
            if found >= 12:
                break
        for doc in DOC_NAMES:
            path = os.path.join(repo, doc)
            if os.path.exists(path):
                try:
                    text = open(path, encoding="utf-8").read()
                except Exception:  # noqa: BLE001
                    continue
                lines.append("")
                lines.append("### " + doc + " 摘录")
                lines.append(text[:1200])
        if found == 0 and len(lines) <= 2:
            return ""
        return "\n".join(lines)[:3200] + "\n\n"
