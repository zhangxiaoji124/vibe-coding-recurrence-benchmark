"""F 反馈表示：把 Finding 渲染成结构化反例 / 自然语言两种反馈。

负责人：P5
验收：同一条 Finding 能渲染出 structured 与 plain 两版（用 fixture 断言）。
"""
from __future__ import annotations

from ..base import BlockBase, Ctx, Finding, register


@register("f")
class FFeedback(BlockBase):
    owner = "P5"
    implemented = True

    def __init__(self, style: str = "structured"):
        self.style = style

    def feedback(self, findings: list[Finding], ctx: Ctx) -> str:
        if not findings:
            return ""
        if self.style == "plain":
            heads = ["检测到以下安全问题，请修复："]
            for i, f in enumerate(findings, 1):
                heads.append(str(i) + ". " + (f.entry or f.block) + "：" + (f.evidence or f.actual or "存在漏洞"))
            return "\n".join(heads)

        lines = ["### 检测结果（结构化反例）", ""]
        for i, f in enumerate(findings, 1):
            lines.append("#### " + str(i) + ". [" + f.severity + "] " + (f.cwe or f.invariant_id))
            if f.entry:
                lines.append("- 入口：" + f.entry)
            if f.invariant_id:
                lines.append("- 契约：" + f.invariant_id)
            if f.payload:
                lines.append("- 复现 payload：" + f.payload)
            lines.append("- 期望：" + (f.expected or "不触发该问题"))
            lines.append("- 实际：" + (f.actual or "存在漏洞"))
            if f.evidence:
                lines.append("- 证据：" + f.evidence)
            lines.append("")
        lines.append("请只修改与上述发现相关的最小代码，不要改动测试文件。")
        return "\n".join(lines)
