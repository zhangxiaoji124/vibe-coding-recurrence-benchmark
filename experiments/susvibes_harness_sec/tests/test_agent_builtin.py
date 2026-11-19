"""BuiltinAgent：JSON 工具协议、trace、'done 但没写文件' 的 nudge。

运行：python3 tests/test_agent_builtin.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from harness_sec import llm, sandbox  # noqa: E402
from harness_sec.agents.builtin import BuiltinAgent  # noqa: E402
from harness_sec.base import Ctx  # noqa: E402


def _repo(tmp):
    src = os.path.join(ROOT, "tests", "fixtures", "fake_repo")
    dst = os.path.join(tmp, "repo")
    shutil.copytree(src, dst)
    sandbox.ensure_git(dst)
    return dst


def test_nudge_then_write():
    tmp = tempfile.mkdtemp()
    try:
        repo = _repo(tmp)
        trace = os.path.join(tmp, "trace.jsonl")
        ctx = Ctx(task_id="fixture", repo_dir=repo, problem_statement="修复 get_note 越权")
        ctx.visible["trace_path"] = trace
        replies = [
            '{"action":"list_files","path":"."}',
            '{"action":"done","summary":"我觉得没问题"}',          # 没写文件 → 应被 nudge
            '{"action":"write_file","path":"app/core.py","content":"FIXED = 1\\n"}',
            '{"action":"done","summary":"已修复"}',
        ]
        calls = {"i": 0}
        def fake_chat(messages, **kw):
            i = calls["i"]
            calls["i"] += 1
            return replies[min(i, len(replies) - 1)]
        old = llm.chat
        try:
            llm.chat = fake_chat
            agent = BuiltinAgent()
            out = agent.run(ctx, "修复 get_note 越权")
        finally:
            llm.chat = old
        assert agent.wrote >= 1, (out, agent.wrote)
        patch = sandbox.git_diff(repo)
        assert "FIXED = 1" in patch, patch
        lines = [json.loads(x) for x in open(trace, encoding="utf-8") if x.strip()]
        assert any(x.get("kind") == "nudge_no_write" for x in lines), lines
        assert any(x.get("action") == "write_file" for x in lines), lines
    finally:
        shutil.rmtree(tmp, ignore_errors=True)



def test_write_deadline():
    tmp = tempfile.mkdtemp()
    try:
        repo = _repo(tmp)
        trace = os.path.join(tmp, "trace2.jsonl")
        ctx = Ctx(task_id="fixture", repo_dir=repo, problem_statement="修复")
        ctx.visible["trace_path"] = trace
        reads = '{"action":"read_file","path":"app/core.py"}'
        replies = [reads, reads, reads, reads,
                   '{"action":"write_file","path":"app/core.py","content":"FIXED = 1"}',
                   '{"action":"done","summary":"ok"}']
        calls = {"i": 0}
        def fake_chat(messages, **kw):
            i = calls["i"]; calls["i"] += 1
            return replies[min(i, len(replies) - 1)]
        old = llm.chat
        try:
            llm.chat = fake_chat
            agent = BuiltinAgent(write_deadline=3)
            agent.run(ctx, "修复")
        finally:
            llm.chat = old
        lines = [json.loads(x) for x in open(trace, encoding="utf-8") if x.strip()]
        assert any(x.get("kind") == "write_deadline" for x in lines), lines
        assert agent.wrote >= 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _main():
    test_nudge_then_write()
    test_write_deadline()
    print("PASS test_nudge_then_write")
    print("PASS test_write_deadline")


if __name__ == "__main__":
    raise SystemExit(_main())
