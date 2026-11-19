#!/usr/bin/env bash
# 环境自检：用哪个 python、susvibes 是否可用、docker/磁盘是否就绪
set -u
PY=${PY:-python3}
echo "=== 解释器 ==="
$PY -V 2>&1
echo "   路径：$(command -v $PY)"
echo
echo "=== 版本检查（SusVibes 需要 Python 3.11；3.14 会因缺 wheel 而卡 pip）==="
$PY - <<'PYEOF'
import sys
v = sys.version_info
print("Python", "%d.%d.%d" % v[:3])
if v[:2] != (3, 11):
    print("⚠️  建议用 Python 3.11（本机已有 conda 环境 sv）")
PYEOF
echo
echo "=== susvibes 是否可导入 ==="
( cd /tmp && $PY -c "import susvibes; print('OK:', susvibes.__file__)" 2>&1 | tail -2 )
echo
echo "=== 官方评测 CLI ==="
( cd /tmp && $PY -m susvibes.eval.core --help >/dev/null 2>&1 && echo "OK" || echo "不可用（检查解释器/安装）" )
echo
echo "=== Docker ==="
docker --version 2>&1 | head -1
docker info >/dev/null 2>&1 && echo "Docker 已启动" || echo "⚠️ Docker 未启动"
echo
echo "=== 磁盘 ==="
df -h . | tail -1
echo
echo "=== 结论 ==="
echo "如果上面 susvibes/CLI 不可用，用 sv 环境的 python："
echo "  export PY=/Users/renlvran/miniconda3/envs/sv/bin/python"
