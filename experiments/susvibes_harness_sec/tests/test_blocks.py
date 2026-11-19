"""11 块积木的单元测试（不联网、不 docker）。

运行：python tests/test_blocks.py
说明：l1/l2 用 monkeypatch 替换 LLM 调用；p 在没装 bandit 时返回 []；e 在没 key 时返回 []。
每个 owner 可以在这里加自己块的断言（或另建 test_<block>.py）。
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from harness_sec import llm, sandbox  # noqa: E402
from harness_sec.base import Ctx  # noqa: E402
import harness_sec.blocks  # noqa: E402,F401
from harness_sec.blocks.k1_generic import K1Generic  # noqa: E402
from harness_sec.blocks.k3_repo import K3Repo  # noqa: E402
from harness_sec.blocks.l1_self import L1SelfReview  # noqa: E402
from harness_sec.blocks.l2_reviewer import L2Reviewer  # noqa: E402
from harness_sec.blocks.e_exec import EExecProbe  # noqa: E402
from harness_sec.blocks.p_sast import PSast  # noqa: E402
from harness_sec.blocks.s_contract import SContract  # noqa: E402


def _repo(tmp):
    src = os.path.join(ROOT, "tests", "fixtures", "fake_repo")
    dst = os.path.join(tmp, "repo")
    shutil.copytree(src, dst)
    sandbox.ensure_git(dst)
    return dst


def test_k1_knowledge():
    ctx = Ctx(task_id="fixture", repo_dir=".", problem_statement="p")
    text = K1Generic().knowledge(ctx)
    assert "安全" in text and len(text) > 100


def test_k3_repo_knowledge():
    tmp = tempfile.mkdtemp()
    try:
        repo = _repo(tmp)
        ctx = Ctx(task_id="fixture", repo_dir=repo, problem_statement="p")
        text = K3Repo().knowledge(ctx)
        assert isinstance(text, str)  # fixture 仓库可能没有安全函数，允许空串
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_s_contract():
    tmp = tempfile.mkdtemp()
    try:
        ctx = Ctx(task_id="fixture", repo_dir=_repo(tmp), problem_statement="p")
        art = SContract().artifact(ctx)
        assert isinstance(art, dict) and art.get("invariants")
        assert "INV-1" in SContract().inject(ctx)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_l1_l2_with_mock_llm():
    tmp = tempfile.mkdtemp()
    try:
        repo = _repo(tmp)
        with open(os.path.join(repo, "app", "extra.py"), "w", encoding="utf-8") as f:
            f.write("def leak(user, nid):\n    return DB[nid]\n")
        ctx = Ctx(task_id="fixture", repo_dir=repo, problem_statement="p")

        fake = {"findings": [{"severity": "high", "entry": "get_note", "cwe": "CWE-639",
                              "payload": "get_note('alice',1)", "expected": "拒绝", "actual": "返回正文"}]}
        old = llm.chat_json
        try:
            llm.chat_json = lambda *a, **k: fake
            f1 = L1SelfReview().detect(ctx)
            f2 = L2Reviewer().detect(ctx)
        finally:
            llm.chat_json = old
        assert len(f1) == 1 and f1[0].cwe == "CWE-639"
        assert len(f2) == 1 and f2[0].severity == "high"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_e_no_key_returns_empty():
    tmp = tempfile.mkdtemp()
    try:
        ctx = Ctx(task_id="fixture", repo_dir=_repo(tmp), problem_statement="p")
        old_key = os.environ.pop("DEEPSEEK_API_KEY", None)
        try:
            assert EExecProbe().detect(ctx) == []
        finally:
            if old_key:
                os.environ["DEEPSEEK_API_KEY"] = old_key
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_p_no_bandit_returns_list():
    tmp = tempfile.mkdtemp()
    try:
        repo = _repo(tmp)
        ctx = Ctx(task_id="fixture", repo_dir=repo, problem_statement="p")
        assert isinstance(PSast().detect(ctx), list)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _main():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception as e:  # noqa: BLE001
            failed += 1
            print("FAIL", fn.__name__, "->", type(e).__name__, e)
    print("\n" + str(len(fns) - failed) + "/" + str(len(fns)) + " passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
