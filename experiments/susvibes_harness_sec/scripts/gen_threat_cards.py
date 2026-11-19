#!/usr/bin/env python3
"""为目标任务生成 K2 威胁卡骨架（P2 负责补全，禁止写入具体 payload）。

用法：
  python3 scripts/gen_threat_cards.py \
    --dataset "$SUSVIBES_DIR/datasets/default/susvibes_dataset.jsonl" \
    --tasks-file data/tasks_8.json --out data/threat_cards_draft
"""
from __future__ import annotations

import argparse
import json
import os

CWE_INFO = {
    "CWE-22": ("路径遍历", "路径规范化并限制在允许目录内", "用户输入不能拼进文件路径后直接打开"),
    "CWE-79": ("跨站脚本", "输出到 HTML/模板时转义或使用安全渲染", "用户输入不能以可执行形式进入页面"),
    "CWE-173": ("转义处理不当", "对输入/输出做正确的转义与编码", "特殊字符不能改变解析语义"),
    "CWE-287": ("认证不当", "认证失败/异常路径必须拒绝", "未认证请求不能进入受保护逻辑"),
    "CWE-532": ("日志敏感信息", "日志脱敏，不写 token/密码", "敏感字段不得出现在日志/响应"),
    "CWE-601": ("开放重定向", "重定向目标白名单/同源校验", "外部可控 URL 不能成为跳转目标"),
    "CWE-613": ("会话过期", "会话失效/过期策略生效", "登出或过期后旧会话不能继续使用"),
    "CWE-250": ("权限过高", "用最小权限执行，校验外部输入", "不能沿用高权限环境执行外部输入"),
    "CWE-427": ("路径注入", "可执行文件路径必须受控", "PATH/命令查找不能被外部输入影响"),
    "CWE-770": ("资源耗尽", "限制资源使用", "外部输入不能导致无界资源消耗"),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--tasks-file", required=True)
    ap.add_argument("--out", default="data/threat_cards_draft")
    args = ap.parse_args()
    wanted = set(json.load(open(args.tasks_file, encoding="utf-8")))
    os.makedirs(args.out, exist_ok=True)
    rows = [json.loads(l) for l in open(args.dataset, encoding="utf-8")]
    n = 0
    for r in rows:
        if r["instance_id"] not in wanted:
            continue
        cwes = r.get("cwe_ids") or []
        threats = []
        checks = []
        for cwe in cwes:
            name, check, why = CWE_INFO.get(cwe, ("待补全", "待补全", "待补全"))
            threats.append({"cwe": cwe, "why": why, "name": name})
            checks.append(check)
        card = {
            "task_id": r["instance_id"],
            "cwe_ids": cwes,
            "entry_points": [{"name": "TODO：从代码定位入口函数/路由", "note": "该入口接受什么输入"}],
            "data_flow": "TODO：用户输入 -> 处理函数 -> 敏感 sink",
            "threats": threats,
            "required_checks": checks,
            "invariants": [{"id": "INV-1", "statement": "TODO：资源级/权限级不变式"}],
            "problem_statement_excerpt": (r.get("problem_statement") or "")[:500],
        }
        path = os.path.join(args.out, r["instance_id"] + ".yaml")
        with open(path, "w", encoding="utf-8") as f:
            f.write("# K2 威胁卡（P2 补全 TODO；不要写具体 payload，避免泄题）\n")
            f.write(json.dumps(card, ensure_ascii=False, indent=2) + "\n")
        n += 1
    print("生成 " + str(n) + " 张骨架 -> " + args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
