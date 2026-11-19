#!/usr/bin/env bash
# 每日集成：契约测试 + 积木测试 + 8 臂 dry-run（零 API 零 docker）
set -e
cd "$(dirname "$0")/.."
PY=${PY:-python3}
echo "== 1) 契约测试 =="
$PY tests/test_base.py
echo "== 2) 积木单测 =="
$PY tests/test_blocks.py
echo "== 3) 8 臂 dry-run =="
for arm in 000 100 010 001 110 101 011 111; do
  out="/tmp/hs_dry_$arm"
  rm -rf "$out"
  $PY -m harness_sec.run_recipe --config "harness_sec/configs/$arm.yaml" --dry-run --out "$out" >/dev/null
  echo "  $arm ok"
done
echo "== 4) 配方 dry-run（抽查 01/04/48）=="
for r in 01 04 48; do
  out="/tmp/hs_recipe_$r"
  rm -rf "$out"
  $PY -m harness_sec.run_recipe --config "harness_sec/configs/recipes/$r.yaml" --dry-run --out "$out" >/dev/null
  echo "  recipe $r ok"
done
echo "== 集成通过 =="
