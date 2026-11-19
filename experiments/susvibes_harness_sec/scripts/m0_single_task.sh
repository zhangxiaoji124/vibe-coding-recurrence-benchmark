#!/usr/bin/env bash
# M0：单任务 × 2 臂（基线 + 第 1 组）跑通验证
# 用法：bash scripts/m0_single_task.sh <instance_id>
set -euo pipefail
cd "$(dirname "$0")/.."

SUSVIBES=${SUSVIBES:-../susvibes}
OUT=${OUT:-runs/M0}
PY=${PY:-python3}
TASK=${1:-}

if [ -z "$TASK" ]; then
  echo "用法：bash scripts/m0_single_task.sh <instance_id>"
  echo "先跑：$PY -m harness_sec.stage0 --susvibes-dir $SUSVIBES --limit 1 --out $OUT/stage0"
  echo "然后从 $OUT/stage0/stage0.csv 里挑一个 ok=True 的 iid 传进来。"
  exit 2
fi
if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
  echo "⚠️  未设置 DEEPSEEK_API_KEY：真实跑 agent/检测器会失败。"
  echo "    export DEEPSEEK_API_KEY=sk-..."
  exit 2
fi

mkdir -p "$OUT"
run_arm () {
  local cfg=$1; local arm=$2
  echo ""
  echo "==================== [$arm] run ===================="
  $PY -m harness_sec.run_recipe --config "$cfg" --susvibes-dir "$SUSVIBES" \
      --tasks "$TASK" --out "$OUT/$arm"
  echo "==================== [$arm] eval ===================="
  $PY -m harness_sec.evaluate --run-id "M0_$arm" \
      --predictions "$OUT/$arm/predictions.jsonl" --susvibes-dir "$SUSVIBES" --out "$OUT/$arm"
}

run_arm harness_sec/configs/baseline.yaml baseline
run_arm harness_sec/configs/recipes/01.yaml 01

# 主对照：官方最强可部署策略 self-selection（若已生成）
if [ -f "data/official/self-selection.jsonl" ]; then
  echo ""
  echo "==================== [official self-selection] run ===================="
  $PY -m harness_sec.run_recipe --config harness_sec/configs/baseline.yaml \
      --susvibes-dir "$SUSVIBES" --dataset data/official/self-selection.jsonl \
      --tasks "$TASK" --out "$OUT/official_selfselect"
  $PY -m harness_sec.evaluate --run-id "M0_official_selfselect" \
      --predictions "$OUT/official_selfselect/predictions.jsonl" --susvibes-dir "$SUSVIBES" --out "$OUT/official_selfselect"
else
  echo ""
  echo "提示：想比官方策略，先跑 python3 scripts/prepare_official_strategies.py --strategies self-selection"
fi

echo ""
echo "==================== 汇总 ===================="
$PY scripts/show_m0_results.py --susvibes-dir "$SUSVIBES" --out "$OUT" --iid "$TASK"
