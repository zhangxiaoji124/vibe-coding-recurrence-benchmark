# 组员任务说明（可直接发群）

> 第二阶段实验：**SusVibes 安全机制实验**（8 臂 + 48 组配方）
> 代码与任务集已冻结：2026-11-14；负责人 P1（基础设施/汇总）。

## 1. 这个实验在做什么（一句话）

在 SusVibes 的 8 个"功能能修好、但安全测试过不了"的真实任务上，比较 **11 个安全机制积木**的不同组合，看哪种组合能让 **SecPass 提升、同时 FuncPass 不掉**。

- 8 臂 = M1/M2/M3 三个机制开/关的 2×2×2；
- 48 组 = M1 三选一 × M2 四选一 × M3 四选一；
- 评测 = SusVibes 官方评测（FuncPass / SecPass），所有人同一口径。

## 2. 每个人要做什么

| 人 | 任务 |
|---|---|
| **P1** | 先跑 **8 臂**（8 config × 8 任务 = 64 次），再跑自己名下 10 个配方；负责汇总 |
| P2 | 跑名下 10 个配方（见 `data/recipe_assignment.md`） |
| P3 | 跑名下 10 个配方 |
| P4 | 跑名下 9 个配方 |
| P5 | 跑名下 9 个配方 + 统一评测/统计 |

每个配方 = 一个 yaml，跑 8 个任务；输出在 `runs/R48/<配方>/`。

## 3. 一次性环境（每台机器 15–30 分钟）

```bash
# Python 3.11
conda create -n sv python=3.11 -y && conda activate sv

# SusVibes（官方仓库）
git clone https://github.com/LeiLiLab/susvibes.git ~/susvibes
cd ~/susvibes && pip install -e . --no-deps && cd -

# Docker Desktop（Mac/Windows）或 docker engine（Linux）
docker info

# 本仓库（在 PR 合并前进用 fork；合并后改回组仓库地址）
git clone https://github.com/Halina928/vibe-coding-recurrence-benchmark.git
cd vibe-coding-recurrence-benchmark/experiments/susvibes_harness_sec

# 记录版本（写入结果说明；应为 c6b25ee 或更新）
git rev-parse --short HEAD
# 自检：应有 10 个威胁卡文件（8 张任务卡 + 模板 + fixture）
ls harness_sec/knowledge/threat_cards | wc -l

export PY=$(which python)
export SUSVIBES_DIR=$HOME/susvibes
export DEEPSEEK_API_KEY=sk-...      # 自己的 key，禁止提交

bash scripts/env_check.sh            # 自检
```

> 第一次跑会自动拉任务镜像：8 个任务约 5–10 GB 磁盘，请预留空间。

## 4. 跑实验（照抄）

```bash
# 防止睡眠（Mac）
caffeinate -dimsu &

# P1：8 臂
for arm in 000 100 010 001 110 101 011 111; do
  $PY -m harness_sec.run_recipe --config harness_sec/configs/$arm.yaml \
    --susvibes-dir "$SUSVIBES_DIR" --tasks-file data/tasks_8.json \
    --out runs/E1/$arm --resume --task-timeout 1800
done

# 所有人：自己的配方（以 P1 为例，其他人在 recipe_assignment.md 里查自己的编号）
for r in 01 06 11 16 21 26 31 36 41 46; do
  $PY -m harness_sec.run_recipe --config harness_sec/configs/recipes/$r.yaml \
    --susvibes-dir "$SUSVIBES_DIR" --tasks-file data/tasks_8.json \
    --out runs/R48/$r --resume --task-timeout 1800
done
```

**中断了怎么办**：同一条命令加 `--resume` 再跑，会跳过已完成的任务，不会从头。

## 5. 交什么（每人）

每个配方目录 `runs/R48/<配方>/` 里交：

```
predictions.jsonl
predictions_first.jsonl
<任务>/episode.json
<任务>/trace.jsonl
```

打包（不要带 `_repos`）：

```bash
cd runs/R48 && zip -r ~/R48_<你的名字>.zip . -x "*/_repos/*"
```

发群/网盘，或推自己的 git 分支。

## 6. 评测（不需要 API key）

每人本机评自己的配方：

```bash
for r in 01 06 11; do
  $PY -m harness_sec.evaluate --run-id "M0_R48_$r" \
    --predictions runs/R48/$r/predictions.jsonl \
    --susvibes-dir "$SUSVIBES_DIR" --max-workers 1 --local-images --no-rescue
done
```

或者只交 `predictions.jsonl`，由 P5 统一评测（推荐，口径一致）。

## 7. 铁律（否则数据作废）

1. 代码冻结：同一个 commit；不改 `harness_sec/`、`configs/`、`data/tasks_8.json`；
2. 预算固定：`max_steps=60`（configs 已写死），不要加 `--max-steps`；
3. 模型固定：`deepseek-chat`；
4. 只跑自己名下的配方，不重复跑别人的；
5. 不把 API key、`runs/`、`data/official/*.jsonl` 提交到 git；
6. 跑批时保持机器不睡眠。

## 8. 时间与成本

| 项目 | 预计 |
|---|---|
| 环境准备 | 15–30 分钟（镜像下载看网速） |
| 8 臂（P1） | 1–1.5 小时，¥2–10 |
| 48 组（每人 9–10 配方 × 8 任务） | 1.5–3 小时，¥3–20/人 |
| 汇总 + 评测（P5） | 0.5–1 天 |

## 9. 常见问题

| 现象 | 处理 |
|---|---|
| `HTTP 401` | API key 无效/过期/无余额；`run_recipe` 会提前中止 |
| 全部 `empty_patch` | 看 `episode.json` 的 `agent_error` |
| 评测显示 `?` | 报告缺失：用 `--local-images`，或单个任务测试日志解析失败（已容忍） |
| 单个任务卡住 >30 分钟 | `--task-timeout 1800` 自动跳过；重跑 `--resume` |
| 容器/网络报错 | `docker info` 先确认 Docker 正常；重启 Docker Desktop |
