# 用云算力行不行？怎么用最划算

> 结论：**可以，而且比 Mac 更合适**——SusVibes 的镜像是 **x86_64**，云上 Linux 原生跑，不用 Rosetta 模拟（快 2–3 倍），也不占你们本地磁盘。
> 但**没必要全上云**：最划算的是「**队友本地跑 agent + 云上一台机器统一跑官方评测**」。

## 1. 三种用法

| 方案 | 云上跑什么 | 本地跑什么 | 适合 |
|---|---|---|---|
| **A. 全云** | agent + 官方评测 | 只写代码/看结果 | 队友电脑慢/不想装 Docker |
| **B. 只云评测（推荐）** | 官方评测（Docker 重活） | 每人跑自己那 9–10 组 agent，回传 `predictions.jsonl` | 大多数人 |
| **C. 混合** | Stage 0 拉镜像 + 评测 | M0、调参、小批量 agent | 想省云费 |

**为什么推荐 B**：agent 那步只需要 Python + API（不重）；官方评测才是"4 GB/4 核每 worker + 40 GB 镜像"的重活。把评测集中到云上一台机器，还能保证"所有臂同一评测环境"。

## 2. 买什么配置

| 用途 | CPU | 内存 | 磁盘 | 说明 |
|---|---|---|---|---|
| **只跑评测（P5）** | 8–16 vCPU | 32–64 GB | **≥200 GB** | 官方建议 4 GB+4 核/worker → 8 核约 2 worker，16 核约 4 worker |
| **agent + 评测全在一台** | 16 vCPU | 64 GB | **≥300 GB** | agent 轻，评测重 |
| 仅 Stage 0 拉镜像 | 4 vCPU | 16 GB | 200 GB | 拉完镜像可以关机，磁盘保留（按量磁盘另计） |

- **不需要 GPU**（模型走 API）；
- 必须 **x86_64**（不要买 ARM 实例）；
- 系统：**Ubuntu 22.04 / 24.04**。

## 3. 费用大概多少（按量付费，价格随厂商/地域浮动，以官网为准）

| 配置 | 按量约 | 跑 3 天约 | 说明 |
|---|---|---|---|
| 8 vCPU / 32 GB / 200 GB | ¥2–4 /小时 | ¥150–300 | 够跑评测 + 小队 agent |
| 16 vCPU / 64 GB / 300 GB | ¥4–8 /小时 | ¥300–600 | 并发更高，48 组更快 |
| 抢占式/竞价实例 | 约为按量 30–60% | ¥100–350 | 可能被回收，适合评测（可续跑） |

> 你本机已有 570 GB 磁盘、16 GB 内存，**够跑 M0 和筛选**；48 组那几天再租云机器最划算。
> **API 费用不变**（同一批 token），云只是多了一项"机器租金"。

## 4. 国内云的注意点

1. **Docker Hub 拉取可能慢/失败**：国内机器给 Docker 配镜像加速器，或选**香港/新加坡**地域；镜像总量约 40–80 GB。
2. **DeepSeek API 延迟**：国内云到 DeepSeek 更快；香港/新加坡也可以但每次调用多一点延迟（384 次 × 多步会放大）。
3. **API key 安全**：只放环境变量，不写进文件/仓库；SSH 用密钥登录。
4. **数据同步**：用 git 同步代码；`runs/`（predictions）小，用 zip/scp 回传；**不要把 40 GB 镜像打进 git**。

## 5. 一键初始化脚本（Ubuntu）

仓库里给了 `scripts/setup_cloud.sh`：

```bash
# 在云主机上（Ubuntu 22.04/24.04）
git clone <你们组仓库> && cd Harness安全机制实验
bash scripts/setup_cloud.sh
```

它会做：装 Docker → 装 Miniconda + Python 3.11 环境 `sv` → `pip install -e ./susvibes` → 自检。
（susvibes 代码要 clone 到旁边：`git clone https://github.com/LeiLiLab/susvibes.git ../susvibes`）

## 6. 在云上跑的标准流程

```bash
# 1) 环境
export PY=/opt/miniconda3/envs/sv/bin/python
export SUSVIBES_DIR=../susvibes
export DEEPSEEK_API_KEY=sk-...
bash scripts/env_check.sh

# 2) 只跑评测（方案 B，P5 在云上）
bash scripts/collect_results.sh incoming/
python3 -m harness_sec.evaluate --arms-root runs/R48 --susvibes-dir "$SUSVIBES_DIR" --csv results/R48/results.csv

# 3) 如果全云（方案 A）
python3 -m harness_sec.stage0 --susvibes-dir "$SUSVIBES_DIR" --limit 8 --out runs/stage0
python3 -m harness_sec.run_recipe --config ... --tasks-file data/tasks_8.json --out runs/R48/01
```

## 7. 建议的落地顺序

1. **这两天**：本机跑 M0 + 任务筛选（已在进行）；
2. **48 组开跑前 1 天**：租一台 **8 vCPU/32 GB/200 GB** 按量云主机（约 ¥2–4/小时），只用来做 Stage 0 + 官方评测；
3. **队友 agent 仍在本机跑**（成本最低、不用每人装云环境）；
4. 48 组跑完、评测完成，**当天释放云主机**（磁盘按量也计费）。
