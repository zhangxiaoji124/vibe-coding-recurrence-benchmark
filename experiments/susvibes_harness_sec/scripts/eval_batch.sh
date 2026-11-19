#!/usr/bin/env bash
# 调官方评测器（一行不改）+ 汇总
# 用法：bash scripts/eval_batch.sh <susvibes_dir> <arm> <predictions.jsonl> [max_workers]
set -e
SUSVIBES_DIR=${1:?susvibes dir}
ARM=${2:?arm}
PRED=${3:?predictions.jsonl}
WORKERS=${4:-3}
cd "$SUSVIBES_DIR"
python -m susvibes.eval.core \
  --run_id "E1_$ARM" \
  --predictions_path "$(cd "$(dirname "$PRED")" && pwd)/$(basename "$PRED")" \
  --max_workers "$WORKERS" --strategy none --resume
echo "logs -> $SUSVIBES_DIR/logs/eval/E1_$ARM/none/"
