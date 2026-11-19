#!/usr/bin/env bash
# 收集组员回传的 zip（R48_<组号>_<名字>.zip）到 runs/R48/<组号>/
# 用法：bash scripts/collect_results.sh <incoming_dir>
set -euo pipefail
cd "$(dirname "$0")/.."
IN=${1:-incoming}
[ -d "$IN" ] || { echo "找不到目录：$IN"; exit 2; }
mkdir -p runs/R48
n=0
for z in "$IN"/*.zip; do
  [ -e "$z" ] || continue
  base=$(basename "$z" .zip)
  arm=$(echo "$base" | sed -E 's/^R48_([0-9]{2})_.*/\1/')
  if [ "$arm" = "$base" ]; then
    echo "跳过（文件名不符合 R48_<组号>_<名字>.zip）：$base"
    continue
  fi
  echo "解压 $base -> runs/R48/$arm"
  unzip -oq "$z" -d runs/R48/
  n=$((n+1))
done
echo "完成，共 $n 个包。检查每组是否有 predictions.jsonl："
for d in runs/R48/*/; do
  [ -f "${d}predictions.jsonl" ] && echo "  OK  $d" || echo "  MISS $d"
done
