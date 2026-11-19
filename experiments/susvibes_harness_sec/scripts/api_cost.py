#!/usr/bin/env python3
"""统计 API 花费：读 run 目录下的 api_usage.jsonl 并估算费用（人民币）。

用法：
  python3 scripts/api_cost.py runs/R48 --input-miss 2 --input-hit 0.5 --output 8
（单价单位：元 / 百万 tokens；请以 platform.deepseek.com 当前价目为准。）
"""
from __future__ import annotations

import argparse
import glob
import json
import os


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", help="目录（会递归找 api_usage.jsonl）")
    ap.add_argument("--input-miss", type=float, default=2.0, help="输入未命中缓存 元/M")
    ap.add_argument("--input-hit", type=float, default=0.5, help="输入命中缓存 元/M")
    ap.add_argument("--output", type=float, default=8.0, help="输出 元/M")
    args = ap.parse_args()

    files = glob.glob(os.path.join(args.root, "**", "api_usage.jsonl"), recursive=True)
    if not files:
        print("没找到 api_usage.jsonl（下次跑 run_recipe 会自动记录）")
        return 1
    total = {"calls": 0, "prompt": 0, "hit": 0, "miss": 0, "completion": 0}
    for path in files:
        for line in open(path, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            total["calls"] += 1
            total["prompt"] += r.get("prompt_tokens", 0)
            total["hit"] += r.get("prompt_cache_hit_tokens", 0)
            total["miss"] += r.get("prompt_cache_miss_tokens", 0) or max(
                0, r.get("prompt_tokens", 0) - r.get("prompt_cache_hit_tokens", 0))
            total["completion"] += r.get("completion_tokens", 0)
    cost = (total["miss"] / 1e6 * args.input_miss
            + total["hit"] / 1e6 * args.input_hit
            + total["completion"] / 1e6 * args.output)
    print("文件数:", len(files))
    print("调用次数:", total["calls"])
    print("输入 tokens: %d（命中 %d / 未命中 %d）" % (total["prompt"], total["hit"], total["miss"]))
    print("输出 tokens:", total["completion"])
    print("估算费用: ¥%.3f" % cost)
    print("（单价：输入未命中 %.2f / 命中 %.2f / 输出 %.2f 元每百万 tokens）" % (
        args.input_miss, args.input_hit, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
