#!/usr/bin/env bash
# 任务筛选：对候选任务跑 baseline，找出"功能过但安全不过"的目标任务
# 用法：bash scripts/screen_tasks.sh data/tasks_small.json
set -euo pipefail
cd "$(dirname "$0")/.."
TASKS=${1:-data/tasks_small.json}
SUSVIBES=${SUSVIBES_DIR:-../susvibes}
PY=${PY:-python3}
OUT=${OUT:-runs/screen}

echo "== 1) 拉镜像/导出仓库（并行度低，耐心等）=="
$PY -m harness_sec.stage0 --susvibes-dir "$SUSVIBES" --tasks-file "$TASKS" --limit 20 --out "$OUT/stage0"

echo "== 2) 跑 baseline（每个任务一次）=="
$PY -m harness_sec.run_recipe --config harness_sec/configs/baseline.yaml \
  --susvibes-dir "$SUSVIBES" --tasks-file "$TASKS" --out "$OUT/baseline"

echo "== 3) 官方评测（run_id 自动 M0_baseline）=="
bash scripts/eval_m0.sh "$OUT/baseline"

echo "== 4) 汇总（挑出目标场景）=="
$PY scripts/screen_results.py --susvibes-dir "$SUSVIBES" --out "$OUT/baseline"
