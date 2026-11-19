#!/usr/bin/env bash
# 在我们的 harness 里跑官方题面策略（generic / self-selection / oracle）
# 用途：路径 2 的第 ③ 组——"同 scaffold 下，官方策略能拿多少"
# 用法：bash scripts/run_official_strategy_arm.sh <strategy> <tasks-file> <out-dir>
set -euo pipefail
cd "$(dirname "$0")/.."
STRATEGY=${1:?用法: bash scripts/run_official_strategy_arm.sh generic|self-selection|oracle <tasks-file> <out>}
TASKS=${2:?tasks-file}
OUT=${3:?out-dir}
SUSVIBES=${SUSVIBES_DIR:-../susvibes}
PY=${PY:-python3}
DS="data/official/$STRATEGY.jsonl"
if [ ! -f "$DS" ]; then
  echo "缺 $DS；先跑：python3 scripts/prepare_official_strategies.py --strategies $STRATEGY"
  exit 2
fi
echo "[official-strategy] strategy=$STRATEGY tasks=$TASKS -> $OUT"
$PY -m harness_sec.run_recipe \
  --config harness_sec/configs/baseline.yaml \
  --susvibes-dir "$SUSVIBES" \
  --dataset "$DS" \
  --tasks-file "$TASKS" \
  --out "$OUT"
echo "评测： bash scripts/eval_m0.sh $OUT"
