#!/usr/bin/env bash
# 给某个 M0 臂目录跑官方评测（run_id 自动 = M0_<目录名>，保证 show 脚本能找到）
# 用法：bash scripts/eval_m0.sh runs/M0/baseline2 [iid]
set -euo pipefail
cd "$(dirname "$0")/.."
DIR=${1:?用法: bash scripts/eval_m0.sh runs/M0/<臂目录> [iid]}
SUSVIBES=${SUSVIBES_DIR:-../susvibes}
PY=${PY:-python3}
ARM=$(basename "$DIR")
REL=${DIR#runs/}
RUN_ID="M0_$(echo "$REL" | tr '/' '_')"
PRED="$DIR/predictions.jsonl"
[ -f "$PRED" ] || { echo "找不到 $PRED"; exit 2; }
echo "[eval] run_id=$RUN_ID  predictions=$PRED"
$PY -m harness_sec.evaluate --run-id "$RUN_ID" --predictions "$PRED" --susvibes-dir "$SUSVIBES"
echo "完成。看结果："
echo "  $PY scripts/show_m0_results.py --susvibes-dir \"$SUSVIBES\" --out runs/M0 --iid ${2:-<iid>}"
