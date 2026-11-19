#!/usr/bin/env bash
# 云主机（Ubuntu 22.04/24.04, x86_64）一键初始化：
#   Docker + Miniconda(py3.11) + 安装 susvibes + 自检
# 用法：在仓库根目录执行  bash scripts/setup_cloud.sh
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$(pwd)
CONDA_DIR=${CONDA_DIR:-/opt/miniconda3}
PY_VER=3.11

echo "== 1) 系统检查 =="
uname -m | grep -q x86_64 || echo "⚠️ 当前不是 x86_64，SusVibes 镜像会走模拟，建议换 x86 实例"
df -h "$ROOT" | tail -1

echo "== 2) 安装 Docker =="
if ! command -v docker >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y docker.io git curl
  sudo systemctl enable --now docker
  sudo usermod -aG docker "$USER" || true
  echo "提示：组权限要重新登录生效；临时可用 sudo docker"
fi
docker --version || true

echo "== 3) 安装 Miniconda + Python ${PY_VER} 环境 sv =="
if [ ! -x "$CONDA_DIR/bin/conda" ]; then
  curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /tmp/miniconda.sh
  sudo bash /tmp/miniconda.sh -b -p "$CONDA_DIR"
fi
"$CONDA_DIR/bin/conda" create -y -n sv "python=${PY_VER}" || true
PY="$CONDA_DIR/envs/sv/bin/python"
"$PY" -m pip install -U pip

echo "== 4) 安装上游 SusVibes（只读依赖）=="
if [ ! -d "../susvibes" ]; then
  git clone https://github.com/LeiLiLab/susvibes.git ../susvibes
fi
"$PY" -m pip install -r ../susvibes/requirements.txt
"$PY" -m pip install -e ../susvibes

echo "== 5) 自检 =="
export PY
export SUSVIBES_DIR="$ROOT/../susvibes"
bash scripts/env_check.sh || true

cat <<'TIP'

完成。以后每条命令前先：
  export PY=/opt/miniconda3/envs/sv/bin/python
  export SUSVIBES_DIR=../susvibes
  export DEEPSEEK_API_KEY=sk-...

国内拉镜像慢的话，给 Docker 配镜像加速器，或把实例换到香港/新加坡。
TIP
