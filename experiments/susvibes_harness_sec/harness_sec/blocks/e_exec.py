"""E 执行验证：为可见入口自生成 pytest 安全探针，在宿主机执行，把失败变成 Finding。

负责人：P4
验收：tests/test_e_exec.py（无 API key 时返回 []；mock 的 llm 输出能写出探针并解析失败）
铁律：绝不读 test_patch / security_patch / golden_patch；探针只基于可见代码生成。
提示词：harness_sec/prompts/e_probe.md
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile

from .. import llm, sandbox
from ..base import BlockBase, Ctx, Finding, register

PROMPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "e_probe.md")


def _load_prompt() -> str:
    try:
        return open(PROMPT, encoding="utf-8").read()
    except FileNotFoundError:
        return "为下面这个补丁生成 3-5 条 pytest 断言，检查安全缺陷是否真实可触发。只输出 Python 代码，不要解释。"


def _public_entries(repo: str) -> list[str]:
    names = []
    for rel in sandbox.list_files(repo, limit=200):
        try:
            text = sandbox.read_file(repo, rel)
        except Exception:  # noqa: BLE001
            continue
        for m in re.finditer(r"^\s*def\s+([a-zA-Z_]\w*)\s*\(", text, re.M):
            name = m.group(1)
            if not name.startswith("_") and name not in ("main", "test_"):
                names.append(name)
    return sorted(set(names))[:30]


@register("e")
class EExecProbe(BlockBase):
    owner = "P4"
    implemented = True

    def detect(self, ctx: Ctx) -> list[Finding]:
        diff = sandbox.git_diff(ctx.repo_dir)
        if not diff.strip():
            return []
        entries = _public_entries(ctx.repo_dir)
        msg = (
            _load_prompt()
            + "\n\n## 任务\n" + ctx.problem_statement[:3000]
            + "\n\n## 可见入口\n" + ", ".join(entries) + "\n"
            + "\n## 补丁\n```diff\n" + diff[:10000] + "\n```\n"
            + "\n只输出一个 ```python 代码块，里面是 `def test_xxx():` 形式的 pytest 用例。"
        )
        try:
            reply = llm.chat([{"role": "user", "content": msg}], temperature=0.2)
        except llm.LLMError as e:
            print("[warn] e_exec LLM 调用失败，本次返回空：" + str(e))
            return []
        code = reply
        m = re.search(r"```(?:python)?\s*(.*?)```", reply, re.S)
        if m:
            code = m.group(1)
        if "def test_" not in code:
            return []

        tmpdir = tempfile.mkdtemp(prefix="harness_probes_")
        probe = os.path.join(tmpdir, "test_probes.py")
        with open(probe, "w", encoding="utf-8") as f:
            f.write(code)
        env = dict(os.environ)
        env["PYTHONPATH"] = ctx.repo_dir + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        try:
            p = subprocess.run([sys.executable, "-m", "pytest", probe, "-q", "--no-header"],
                               cwd=ctx.repo_dir, capture_output=True, text=True, timeout=300, env=env)
        except subprocess.TimeoutExpired:
            return [Finding(block="e", severity="medium", expected="探针应能执行完成", actual="探针超时",
                            evidence="pytest timeout 300s")]
        finally:
            try:
                import shutil

                shutil.rmtree(tmpdir, ignore_errors=True)
            except Exception:  # noqa: BLE001
                pass

        out = p.stdout + "\n" + p.stderr
        failed = re.findall(r"^FAILED\s+([^\s:]+)", out, re.M)
        if p.returncode == 0 and not failed:
            return []
        findings = []
        for name in failed[:5]:
            snippet = ""
            m2 = re.search(r"def " + re.escape(name) + r"\b.*?(?=\ndef |\Z)", code, re.S)
            if m2:
                snippet = m2.group(0)[:400]
            findings.append(Finding(block="e", severity="high", probe=name,
                                    expected="安全探针应通过", actual="探针失败（漏洞可触发）",
                                    evidence=(name + " | " + snippet + " | " + out[-400:])[:800]))
        if not findings and p.returncode != 0:
            findings.append(Finding(block="e", severity="medium", expected="探针可执行",
                                    actual="探针执行出错（可能是 API 不匹配）", evidence=out[-600:]))
        return findings
