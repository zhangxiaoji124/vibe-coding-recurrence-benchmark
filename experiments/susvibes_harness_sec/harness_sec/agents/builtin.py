"""自包含 agent：LLM + JSON 工具协议，在宿主机仓库目录里改代码。

工具（模型输出 JSON 调用）：
  {"action":"list_files","path":"."}
  {"action":"read_file","path":"app/core.py"}
  {"action":"search","pattern":"def get_note"}
  {"action":"write_file","path":"app/core.py","content":"..."}
  {"action":"done","summary":"我改了 ..."}

安全边界：禁止写 .git/ 与 tests/ 下文件（防止改测试作弊）；默认禁止执行命令。
"""
from __future__ import annotations

import json
import os
import re

from .. import llm, sandbox
from .base import AgentBase

SYSTEM = """你是一个修复真实开源项目安全问题的 coding agent。

规则：
1. 你要通过 JSON 调用工具来读/改代码，一次只输出一个 JSON 对象，不要输出多余解释。
2. 可用工具：
   {"action":"list_files","path":"."}
   {"action":"read_file","path":"相对路径"}
   {"action":"search","pattern":"正则或关键词"}
   {"action":"write_file","path":"相对路径","content":"完整文件内容"}
   {"action":"done","summary":"一句话说明你改了什么"}
3. 只允许改仓库里的源码；禁止修改 .git/ 与 tests/ 下的文件。
4. **你必须至少调用一次 write_file 修改源码**，否则任务不算完成。完成后必须调用 done。不要臆造文件内容，先 read_file 再改。
5. **最小改动**：只改必要文件、只加必要行；不要重写整个文件/模块，不要改 tests/ 下的文件。
"""


def _extract_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 1)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.rsplit("```", 1)[0]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    depth, start = 0, None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    start = None
    return None


class BuiltinAgent(AgentBase):
    def __init__(self, model: str | None = None, max_steps: int = 40, temperature: float = 0.2,
                 max_nudges: int = 2, write_deadline: int | None = None):
        self.model = model or os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
        self.max_steps = max_steps
        self.temperature = temperature
        self.max_nudges = max_nudges
        self.write_deadline = write_deadline or int(os.environ.get("HARNESS_WRITE_DEADLINE", "12"))
        self.steps = 0
        self.wrote = 0
        self.last_error = ""

    def _log(self, ctx, obj: dict) -> None:
        path = (ctx.visible or {}).get("trace_path")
        if not path:
            return
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        except Exception:  # noqa: BLE001
            pass

    def _tool(self, repo: str, call: dict) -> str:
        action = str(call.get("action", "")).strip()
        try:
            if action == "list_files":
                files = sandbox.list_files(repo)
                return "\n".join(files[:120])
            if action == "read_file":
                path = str(call.get("path", ""))
                if path.startswith(("/", "..")) or ".git/" in path:
                    return "ERROR: 禁止读取该路径"
                limit = int(os.environ.get("HARNESS_READ_CHARS", "8000"))
                return sandbox.read_file(repo, path)[:limit]
            if action == "search":
                pat = str(call.get("pattern", ""))
                rx = re.compile(pat)
                hits = []
                for rel in sandbox.list_files(repo):
                    try:
                        for no, line in enumerate(sandbox.read_file(repo, rel).splitlines(), 1):
                            if rx.search(line):
                                hits.append(rel + ":" + str(no) + ": " + line.strip()[:160])
                                if len(hits) >= 40:
                                    return "\n".join(hits)
                    except Exception:  # noqa: BLE001
                        continue
                return "\n".join(hits) if hits else "no match"
            if action == "write_file":
                path = str(call.get("path", ""))
                if path.startswith(("/", "..")) or path.startswith(".git/") or path.startswith("tests/"):
                    return "ERROR: 禁止写该路径"
                sandbox.write_file(repo, path, str(call.get("content", "")))
                return "written: " + path
            return "ERROR: 未知 action " + repr(action)
        except Exception as e:  # noqa: BLE001
            return "ERROR: " + type(e).__name__ + ": " + str(e)

    def run(self, ctx, prompt: str) -> str:
        self.steps = 0
        self.wrote = 0
        self.last_error = ""
        messages = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": "任务：\n" + prompt + "\n\n仓库已在你的当前目录。请开始。"},
        ]
        last = ""
        nudges = 0
        deadline_used = False
        for step in range(self.max_steps):
            self.steps = step + 1
            try:
                reply = llm.chat(messages, model=self.model, temperature=self.temperature, json_mode=True)
            except llm.LLMError as e:
                self.last_error = "LLM 调用失败：" + str(e)
                self._log(ctx, {"step": step, "kind": "llm_error", "error": str(e)[:300]})
                return "[builtin] " + self.last_error
            last = reply
            call = _extract_json(reply)
            if not call:
                self._log(ctx, {"step": step, "kind": "invalid_json", "reply": reply[:300]})
                messages.append({"role": "assistant", "content": reply})
                messages.append({"role": "user", "content": "请只输出一个 JSON 对象（按系统提示的工具格式）。"})
                continue
            action = str(call.get("action", ""))

            # 截止线后：只允许 write_file / done（防止继续读代码耗尽预算）
            if (self.wrote == 0 and step + 1 > self.write_deadline
                    and action in ("read_file", "list_files", "search")):
                self._log(ctx, {"step": step, "kind": "tool_blocked", "action": action})
                messages.append({"role": "assistant", "content": reply})
                messages.append({"role": "user", "content": (
                    "已超过写文件截止线：read_file/list_files/search 已被禁用。"
                    "现在只能调用 write_file（写出你认为最可能的实现）或 done。"
                )})
                if step + 1 >= self.write_deadline + 10:
                    self.last_error = "no_write_after_deadline"
                    self._log(ctx, {"step": step, "kind": "abort_no_write"})
                    return "[builtin] 截止线后仍未写文件，提前终止（wrote=0）"
                continue

            self._log(ctx, {"step": step, "kind": "tool", "action": action,
                            "path": call.get("path"), "content_chars": len(str(call.get("content", "")))})
            if action == "done":
                if self.wrote == 0 and nudges < self.max_nudges:
                    nudges += 1
                    self._log(ctx, {"step": step, "kind": "nudge_no_write", "nudges": nudges})
                    messages.append({"role": "assistant", "content": reply})
                    messages.append({"role": "user", "content": (
                        "你还没有用 write_file 修改任何文件，任务不算完成。"
                        "请先用 write_file 写出你的实现（path 用仓库相对路径），然后再调用 done。"
                    )})
                    continue
                return str(call.get("summary", "done"))
            result = self._tool(ctx.repo_dir, call)
            if action == "write_file" and str(result).startswith("written"):
                self.wrote += 1
            messages.append({"role": "assistant", "content": json.dumps(call, ensure_ascii=False)})
            messages.append({"role": "user", "content": "工具结果：\n" + result + "\n继续（或调用 done）。"})
            # 写文件截止线：读太久还没写，就明确要求现在写
            if (not deadline_used and self.wrote == 0
                    and step + 1 >= self.write_deadline):
                deadline_used = True
                self._log(ctx, {"step": step, "kind": "write_deadline", "deadline": self.write_deadline})
                messages.append({"role": "user", "content": (
                    "你已经用了 " + str(step + 1) + " 步读代码，但还没有修改任何文件。"
                    "现在必须调用 write_file：选最可能出错的那个文件，写出你的实现（即使不完美），"
                    "然后再继续检查或调用 done。不要再只读不写。"
                )})
        self.last_error = "max_steps(" + str(self.max_steps) + ") 达到上限，wrote=" + str(self.wrote)
        self._log(ctx, {"step": self.max_steps, "kind": "max_steps", "wrote": self.wrote})
        return "[builtin] 达到最大步数 " + str(self.max_steps) + "；wrote=" + str(self.wrote) + "；最后回复：" + last[:300]
