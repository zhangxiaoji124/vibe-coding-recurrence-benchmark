"""重试提示：必须保留 M1 知识、包含上一轮 diff、要求新改动。

运行：python3 tests/test_orchestrator_retry.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from harness_sec.orchestrator import _retry_prompt  # noqa: E402


def test_keep_base_prompt_and_diff():
    out = _retry_prompt("BASE_PROMPT_卡片", "1. [high] CWE-79 | 期望: 转义", "diff --git a/x.py b/x.py")
    assert "BASE_PROMPT_卡片" in out
    assert "CWE-79" in out
    assert "diff --git" in out
    assert "必须产生新的改动" in out


def test_empty_diff():
    out = _retry_prompt("BASE", "发现", "")
    assert "BASE" in out and "发现" in out


def _main():
    test_keep_base_prompt_and_diff()
    test_empty_diff()
    print("PASS test_keep_base_prompt_and_diff")
    print("PASS test_empty_diff")


if __name__ == "__main__":
    raise SystemExit(_main())
