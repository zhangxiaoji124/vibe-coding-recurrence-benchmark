"""契约测试：接口 / 注册表 / 8 臂配置 / 禁用字段 / 一次假 episode / 48 配方。

运行：python tests/test_base.py
或：pytest tests/test_base.py -q
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from harness_sec import config as cfgmod  # noqa: E402
from harness_sec import sandbox  # noqa: E402
from harness_sec.agents.fake import FakeAgent  # noqa: E402
from harness_sec.base import Action, Ctx, Finding, build_many, register  # noqa: E402
from harness_sec.orchestrator import run_episode  # noqa: E402
import harness_sec.blocks  # noqa: E402,F401  触发注册

ALL = ["a", "c", "e", "f", "k1", "k2", "k3", "l1", "l2", "p", "s"]


@register("testdet")
class _TestDet:
    name = "testdet"

    def __init__(self):
        self.calls = 0

    def detect(self, ctx):
        self.calls += 1
        if ctx.attempt == 0:
            return [Finding(block="testdet", entry="get_note", severity="high",
                            payload="get_note('alice', 1)", expected="拒绝", actual="返回正文")]
        return []


@register("testdet_always")
class _TestDetAlways(_TestDet):
    name = "testdet_always"

    def detect(self, ctx):
        self.calls += 1
        return [Finding(block="testdet_always", entry="get_note", severity="high")]


def test_registry():
    for name in ALL:
        assert build_many(name)[0].name == name, name
    assert [b.name for b in build_many(["f", "c", "a"])] == ["f", "c", "a"]


def test_arms_config():
    d = os.path.join(ROOT, "harness_sec", "configs")
    for arm in ("000", "100", "010", "001", "110", "101", "011", "111"):
        cfg = cfgmod.load_arm(os.path.join(d, arm + ".yaml"))
        assert cfg["arm"] == arm
        for i, key in enumerate(("m1", "m2", "m3")):
            has = cfg.get(key) not in (None, "none", "")
            assert has == (arm[i] == "1"), (arm, key, cfg.get(key))


def test_recipes_48():
    d = os.path.join(ROOT, "harness_sec", "configs", "recipes")
    files = sorted(x for x in os.listdir(d) if x.endswith(".yaml"))
    assert len(files) == 48, len(files)
    m1, m2, m3 = set(), set(), set()
    for f in files:
        cfg = cfgmod.load_arm(os.path.join(d, f))
        m1.add(cfg.get("m1"))
        m2.add(cfg.get("m2"))
        m3.add((cfg.get("params") or {}).get("m3_level"))
        assert cfg.get("m3"), (f, cfg.get("m3"))
    assert m1 == {"k1", "k2", "k3"} and m2 == {"l1", "l2", "p", "e"} and m3 == {"F", "C", "A", "S"}, (m1, m2, m3)


def test_forbidden_meta():
    try:
        Ctx(task_id="t", repo_dir=".", problem_statement="p", meta={"test_patch": "x"})
    except ValueError:
        return
    raise AssertionError("Ctx.meta 应拒绝 test_patch")


def test_finding_roundtrip():
    f = Finding(block="l1", entry="get_note", severity="medium", payload="p", cwe="CWE-639")
    assert Finding.from_dict(f.to_dict()) == f
    assert f.is_blocking() and not Finding(block="l1", severity="low").is_blocking()
    try:
        Finding(block="l1", severity="critical")
    except ValueError:
        pass
    else:
        raise AssertionError("severity 应校验")


def _make_repo(tmp: str) -> str:
    src = os.path.join(ROOT, "tests", "fixtures", "fake_repo")
    dst = os.path.join(tmp, "repo")
    shutil.copytree(src, dst)
    sandbox.ensure_git(dst)
    return dst


def test_episode_retry_then_deliver():
    tmp = tempfile.mkdtemp()
    try:
        repo = _make_repo(tmp)
        task = {"instance_id": "fixture", "problem_statement": "修复 get_note 越权。", "cwe_ids": ["CWE-639"]}
        cfg = {"name": "000", "arm": "000", "m1": "none", "m2": "testdet", "m3": ["f", "c", "a"],
               "params": {"max_retries": 2}}
        out = os.path.join(tmp, "out")
        ep = run_episode(task, cfg, FakeAgent(), repo, out, pred_path=os.path.join(out, "predictions.jsonl"),
                         pred_first_path=os.path.join(out, "predictions_first.jsonl"))
        assert ep["attempts"] == 2 and ep["blocked"] is False, ep
        assert os.path.exists(os.path.join(out, "predictions.jsonl"))
        assert os.path.exists(os.path.join(out, "predictions_first.jsonl"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_episode_blocked():
    tmp = tempfile.mkdtemp()
    try:
        repo = _make_repo(tmp)
        task = {"instance_id": "fixture", "problem_statement": "修复越权。", "cwe_ids": ["CWE-639"]}
        cfg = {"name": "000", "arm": "000", "m1": "none", "m2": "testdet_always", "m3": ["f", "c", "a"],
               "params": {"max_retries": 1}}
        out = os.path.join(tmp, "out")
        ep = run_episode(task, cfg, FakeAgent(), repo, out, pred_path=os.path.join(out, "predictions.jsonl"))
        assert ep["blocked"] is True and ep["attempts"] == 2, ep
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_soft_retry_without_gate():
    """M3 里只有 F/C（没有 A 门禁）时，也应该能重做，且耗尽后交付（不 blocked）。"""
    tmp = tempfile.mkdtemp()
    try:
        repo = _make_repo(tmp)
        task = {"instance_id": "fixture", "problem_statement": "修复越权。", "cwe_ids": ["CWE-639"]}
        cfg = {"name": "01", "arm": "01", "m1": "none", "m2": "testdet", "m3": ["f", "c"],
               "params": {"max_retries": 2}}
        out = os.path.join(tmp, "out")
        ep = run_episode(task, cfg, FakeAgent(), repo, out, pred_path=os.path.join(out, "predictions.jsonl"))
        assert ep["attempts"] == 2, ep          # 第 1 次有发现 → 软重做；第 2 次无发现 → 交付
        assert ep["blocked"] is False, ep
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_gate_feedback_loop():
    from harness_sec.blocks.a_gate import AGate
    from harness_sec.blocks.f_feedback import FFeedback
    from harness_sec.blocks.c_loop import CLoop

    ctx = Ctx(task_id="t", repo_dir=".", problem_statement="p")
    f = Finding(block="l1", entry="get_note", severity="high", payload="get_note('alice',1)",
                expected="拒绝", actual="返回正文", cwe="CWE-639")
    assert AGate().decide([f], ctx).kind == "retry"
    assert AGate().decide([], ctx).kind == "deliver"
    assert AGate().decide([Finding(block="l1", severity="low")], ctx).kind == "deliver"
    assert "CWE-639" in FFeedback().feedback([f], ctx)
    assert CLoop(3).policy(ctx)["max_retries"] == 3


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
