"""A 门禁策略：high 才强制 retry/block；medium 只首轮软重试；low 直接交付。"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from harness_sec.base import Ctx, Finding  # noqa: E402
from harness_sec.blocks.a_gate import AGate  # noqa: E402


def F(sev):
    return Finding(block="l2", severity=sev, expected="x", actual="y")


def _ctx(attempt):
    c = Ctx(task_id="t", repo_dir=".", problem_statement="")
    c.attempt = attempt
    return c


def main() -> int:
    g = AGate()
    assert g.decide([], _ctx(0)).kind == "deliver"
    assert g.decide([F("low")], _ctx(0)).kind == "deliver"
    # medium：首轮软重试，第二轮交付（不再把预算耗尽后 block）
    assert g.decide([F("medium")], _ctx(0)).kind == "retry"
    assert g.decide([F("medium")], _ctx(1)).kind == "deliver"
    # high：始终 retry（是否最终 block 由 orchestrator 决定）
    assert g.decide([F("high")], _ctx(0)).kind == "retry"
    assert g.decide([F("high")], _ctx(3)).kind == "retry"
    print("PASS 门禁策略：high=retry/block；medium 仅首轮软重试；low=deliver")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
