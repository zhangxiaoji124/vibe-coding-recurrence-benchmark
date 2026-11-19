#!/usr/bin/env bash
# 打只读运行包：用 rsync 暂存再 zip，避免把 runs/_repos（可能几 GB）扫进去
set -euo pipefail
cd "$(dirname "$0")/.."
NAME="Harness安全机制实验_$(date +%Y%m%d).zip"
rm -f "$NAME"
TMP=$(mktemp -d)
rsync -a \
  --exclude '.git' --exclude '__pycache__' --exclude '*.pyc' \
  --exclude 'runs' --exclude 'logs' --exclude '.venv' --exclude '*.zip' \
  --exclude 'data/official/*.jsonl' --exclude 'incoming/*.zip' --exclude 'Harness安全机制实验_*' \
  ./ "$TMP/pkg/"
( cd "$TMP/pkg" && zip -rq "$OLDPWD/$NAME" . )
rm -rf "$TMP"
echo "生成：$PWD/$NAME"
du -h "$NAME"
