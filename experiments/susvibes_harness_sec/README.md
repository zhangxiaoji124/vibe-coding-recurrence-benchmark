# Harness安全机制实验

> 在 [SusVibes](https://github.com/LeiLiLab/susvibes) 之上新增的**机制层**：11 块可插拔安全机制积木 + 一条命令跑一组 + 官方 FuncPass/SecPass 评测。
> **上游只读**：本仓库不改 SusVibes 任何文件；把 SusVibes clone 到旁边即可。

## 评测结果

[实验评测汇总](results/README.md) 包含 P1–P5 全部 48 组配方 × 8 个任务的评测范围、FuncPass/SecPass/Joint 评分、逐组报告与原始 `report.json` 数据。

## 从哪开始（按顺序看）

| 顺序 | 文件 | 给谁 |
|---|---|---|
| 1 | [`START_HERE.md`](START_HERE.md) | **所有人**（第一页：怎么上手、角色、流程） |
| 2 | [`docs/RUNBOOK.md`](docs/RUNBOOK.md) | 每个阶段的**确切命令与判据** |
| 3 | [`docs/BASELINES.md`](docs/BASELINES.md) | 对照怎么设（generic / self-selection / oracle） |
| 4 | [`docs/EXPERIMENT_48.md`](docs/EXPERIMENT_48.md) | 48 组的设计、成本、分析 |
| 5 | [`docs/M0_SINGLE_TASK.md`](docs/M0_SINGLE_TASK.md) | 第一天：单任务跑通 |
| 6 | [`docs/OWNERS.md`](docs/OWNERS.md) | 5 人分工与防冲突 |

## 这个仓库解决什么

给定 SusVibes 的真实任务，跑不同"安全机制组合"，比较 **FuncPass / SecPass**：

- **M1 安全知识输入**：K1 通用规则 / K2 任务感知威胁卡 / K3 仓库感知
- **M2 安全质量检测**：L1 自审 / L2 独立审查 / P Bandit+Semgrep / E 自生成探针
- **M3 反馈与控制**：F 反馈表示 / C 重做循环 / A 门禁 / S 契约保持

**换组合 = 换一个 yaml，代码一行不改。**

## 安装（本机捷径）

本机已有 conda 环境 **`sv`（Python 3.11）**，`susvibes` 已安装：

```bash
export PY=/Users/renlvran/miniconda3/envs/sv/bin/python
export SUSVIBES_DIR=/Users/renlvran/Desktop/susvibes-main
bash scripts/env_check.sh
```

不要用 base 的 Python 3.14 重装依赖（缺预编译 wheel 会卡住）。

## 安装

```bash
git clone <本仓库> && cd Harness安全机制实验

# 1) 把 SusVibes clone 到旁边（或任意位置，用 --susvibes-dir 指定）
git clone https://github.com/LeiLiLab/susvibes.git ../susvibes
cd ../susvibes && pip install -r requirements.txt && pip install -e . && cd -

# 2) 可选依赖（用到哪块装哪块）
pip install -r requirements.txt
export DEEPSEEK_API_KEY=sk-...        # 真实跑 agent / 检测器需要
```

## 快速开始（零 API 零 docker，1 分钟）

```bash
python3 tests/test_base.py                       # 契约测试（8/8 应通过）
python3 tests/test_blocks.py                     # 11 块单测
bash scripts/integration.sh                      # 8 臂 dry-run 全过

# 单臂干跑
python3 -m harness_sec.run_recipe --config harness_sec/configs/011.yaml --dry-run --out /tmp/dry
```

## 真实跑（需要 docker + 镜像 + API key）

```bash
# Stage 0：先筛 5 个任务，确认镜像/导出/耗时
python3 -m harness_sec.stage0 --susvibes-dir ../susvibes --limit 5 --out runs/stage0

# 跑一个臂
python3 -m harness_sec.run_recipe --config harness_sec/configs/011.yaml \
  --susvibes-dir ../susvibes --tasks <instance_id> --out runs/E1/011

# 官方评测 + 汇总（FuncPass/SecPass/SecPass|FuncPass/RescueRate）
python3 -m harness_sec.evaluate --run-id E1_011 --predictions runs/E1/011/predictions.jsonl \
  --susvibes-dir ../susvibes --out runs/E1/011
```

## 两种实验设计（别混）

| 设计 | 配置 | 规模 | 回答什么 |
|---|---|---|---|
| **48 组配方**（你们的分工版本） | `harness_sec/configs/recipes/01–48.yaml` | 48 组 × 8–12 任务 | 哪种配方看起来最好、各机制水平的边际效应 |
| **8 臂因子**（确认版） | `harness_sec/configs/000–111.yaml` | 8 臂 × 40 任务 | 机制开关有没有用、交互项多大 |

- 48 组的分配见 `data/recipe_assignment.md`；设计与成本见 `docs/EXPERIMENT_48.md`；
- 分析：`python3 -m harness_sec.analyze_recipes --eval-root ../susvibes/logs/eval --out results/R48`。

## 目录

| 路径 | 内容 | owner |
|---|---|---|
| `harness_sec/base.py` | 契约层（Ctx/Finding/Action/BlockBase/registry），**冻结后只有 P1 改** | P1 |
| `harness_sec/sandbox.py` | 从镜像导出 `/project`、git diff/回滚、运行命令 | P1 |
| `harness_sec/orchestrator.py` | episode 主循环（M1→agent→M2→M3→落盘） | P1 |
| `harness_sec/run_recipe.py` | 一条命令跑一组 | P1 |
| `harness_sec/agents/` | builtin（自包含）/ dsh（可选）/ fake | P1 |
| `harness_sec/blocks/k1,k2,k3` | M1 知识 | P2 |
| `harness_sec/blocks/l1,l2,p` + `llm.py` | M2 检测（LLM/工具） | P3 |
| `harness_sec/blocks/e,a,s` | M2 执行验证 + M3 门禁/契约 | P4 |
| `harness_sec/blocks/f,c` + `evaluate.py`/`analyze.py` | M3 反馈/循环 + 评测统计 | P5 |
| `harness_sec/configs/` | 8 臂 + 48 配方 | P1 |
| `harness_sec/knowledge/` | CWE 清单、威胁卡、SAST 映射 | P2/P3 |
| `harness_sec/prompts/` | 各检测块提示词 | P3/P4 |
| `AI_SPECS/` | 11 块给 AI 的任务说明书 | 各自 |
| `docs/` | 架构、实验设计、分工、环境 | P1 |

## 文档

- `docs/QUICKSTART.md`：半天跑通 M0
- `docs/ARCHITECTURE.md`：从命令到 SecPass 的调用链
- `docs/EXPERIMENT_DESIGN.md`：8 臂、端点、48 配方、统计
- [张永基的九项合成安全审查实验](docs/RESULTS_ZHANG_YONGJI_2026-11-13.md)（2026-11-13）：流程、结果与原始证据
- `docs/OWNERS.md`：5 人分工与防冲突规则
- `docs/DOCKER_AND_ENV.md`：镜像、x86、磁盘、API key
- `AI_SPECS/`：每块一页，直接贴给 AI

## 上游 SusVibes 怎么处理（三选一，见 `vendor/README.md`）

| 方案 | 做法 | 仓库大小 | 适合 |
|---|---|---|---|
| **A 依赖（默认）** | 仓库只放机制层，clone 上游到旁边 | ~2 MB | 跟上游同步、组员会装环境 |
| **B vendor 只读副本（推荐）** | 把 SusVibes `rsync` 到 `vendor/susvibes/`（约 17 MB），保留 LICENSE | ~20 MB | 一键/答辩/离线看代码 |
| **C submodule** | `git submodule add` | ~2 MB + 指针 | 想固定版本又不想复制 |

> SusVibes 只有 21 MB（数据集 13 MB），**vendor 成本很低**；但 Docker 镜像（每个 0.4–0.6 GB）永远不进 git。
> 无论哪种，都要把上游 commit 写进 `docs/REPRODUCE.md`（当前：`5d957e6f1850595623d551d089193532e6fa60ce`）。

## 上转到你们组 GitHub 之前

```bash
git init && git add -A && git commit -m "harness mechanism layer v0.1"
git remote add origin <你们的仓库地址> && git push -u origin main
```

`.gitignore` 已排除 `runs/`、`logs/`、`.venv/`、`__pycache__/`、`.env`。

## 现状（v0.1）

- ✅ 11 块全部有实现（部分依赖外部工具/API，缺依赖时安全降级为空）
- ✅ 契约测试 + 积木单测 + 8 臂 dry-run
- ✅ 官方评测封装、RescueRate、Wilson 区间、M2×M3 DiD
- ✅ P1–P5 全部 48 组配方 × 8 个任务已完成生成与官方评测归档（见 [results/README.md](results/README.md)）
- ⏳ 本地复跑真实任务需要：docker 镜像、`DEEPSEEK_API_KEY`、DSH（可选）
