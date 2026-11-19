"""L2 反馈过滤：去重 + 严重度排序 + top-k，避免越报越多把 patch 改坏。"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from harness_sec.base import Finding  # noqa: E402
from harness_sec.blocks.l2_reviewer import filter_findings  # noqa: E402


def F(sev, cwe="CWE-79", ev="e"):
    return Finding(block="l2", severity=sev, cwe=cwe, evidence=ev, expected="x", actual="y")


def main() -> int:
    got = [
        F("low", "CWE-1", "a"),
        F("high", "CWE-2", "b"),
        F("medium", "CWE-3", "c"),
        F("high", "CWE-2", "b"),  # 重复
        F("medium", "CWE-4", "d"),
        F("high", "CWE-5", "e"),
    ]
    out = filter_findings(got, max_n=3)
    assert len(out) == 3, len(out)
    assert out[0].severity == "high" and out[1].severity == "high"
    assert len({(f.cwe, f.evidence) for f in out}) == 3
    print("PASS L2 过滤：6 条 -> top-3（high 优先、去重）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
