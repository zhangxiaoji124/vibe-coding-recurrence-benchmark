"""验证 8 张 K2 威胁卡：存在、无占位符、能被 K2Threat 注入。"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from harness_sec.base import Ctx  # noqa: E402
from harness_sec.blocks.k2_threat import K2Threat  # noqa: E402

IDS = json.load(open(os.path.join(ROOT, "data", "tasks_8.json"), encoding="utf-8"))


def main() -> int:
    k2 = K2Threat()
    for iid in IDS:
        ctx = Ctx(task_id=iid, repo_dir=".", problem_statement="")
        text = k2.knowledge(ctx)
        assert text.strip(), "空知识：" + iid
        assert "TODO" not in text, "还有 TODO：" + iid
        assert "CWE-XXX" not in text, "还是模板占位：" + iid
        assert "required_checks" in text, "缺 required_checks：" + iid
        assert "本任务的安全威胁" in text
        print("PASS", iid[:50], "chars=", len(text))
    print("全部 8 张卡验证通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
