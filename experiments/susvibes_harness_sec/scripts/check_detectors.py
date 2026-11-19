#!/usr/bin/env python3
"""检查 M2 检测器依赖是否齐全（缺失会让对应机制静默返回空 = 实验无效）。

用法：python3 scripts/check_detectors.py
"""
from __future__ import annotations

import importlib.util
import shutil


def main() -> int:
    print("M2 检测器依赖检查\n" + "-" * 40)
    ok = True

    bandit = importlib.util.find_spec("bandit") is not None
    print(("✅" if bandit else "❌") + " bandit（P 块依赖）" +
          ("" if bandit else " → 安装：python3 -m pip install bandit"))
    ok = ok and bandit

    semgrep = shutil.which("semgrep") is not None
    print(("✅" if semgrep else "⚠️ ") + " semgrep（P 块可选，bandit 够用时可不装）")

    print("✅ L1/L2/E 使用 LLM，无额外依赖（需要 API key）")

    print("-" * 40)
    print("结论：" + ("全部就绪" if ok else "P 块不可用；M2=p 的配方（如 11/41）跑出来会是 0 findings"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
