# 组员如何接手这份前期工作

> 目标：5 个人用同一份代码、同一批任务（`data/tasks_8.json`）、同一套规则，各自跑自己负责的配方，最后汇总。

## 0. 先明确结论

- **代码和任务集已经冻结**：以本仓库当前提交为准，不要再改 `harness_sec/`、`harness_sec/configs/`、`data/tasks_8.json`；
- 每个人只跑 **自己名下的配方**（见 `data/recipe_assignment.md`），输出到各自的 `runs/`；
- 评测可以各人本机做（不需要 API key），也可以统一由 P5 汇总后集中做。

## 1. 拿到代码（三选一）

| 方式 | 操作 |
|---|---|
| **GitHub 私有仓库（推荐）** | 仓库主人建 repo 后 `git push`；组员 `git clone <url>` |
| **zip 包** | 群/网盘发 `Harness安全机制实验_YYYYMMDD.zip`（约 180 KB），解压即用 |
| **共享云盘** | 不要用 iCloud 同步 `runs/`（容易冲突），只同步代码和结果汇总 |

## 2. 一次性环境准备（每台机器）

```bash
# 1) Python 3.11（推荐 conda 环境，名字随意）
conda create -n sv python=3.11 -y && conda activate sv

# 2) SusVibes（官方仓库，clone 到任意位置）
git clone https://github.com/LeiLiLab/susvibes.git
cd susvibes && pip install -e . --no-deps

# 3) Docker Desktop（macOS/Windows）或 docker engine（Linux），确认：
docker info

# 4) 回到本项目目录
cd Harness安全机制实验
export PY=$(which python)
export SUSVIBES_DIR=/绝对路径/susvibes
export DEEPSEEK_API_KEY=sk-...        # 自己的 key，禁止提交到仓库

# 5) 自检
bash scripts/env_check.sh
```

> 第一次跑某个任务时会自动拉任务镜像（每个 0.5–2 GB，8 个任务约 5–10 GB 磁盘）。

## 3. 每人跑什么

### 第一步：8 臂因子实验（先做，确认机制方向；建议 P1 一人跑完）

```bash
for arm in 000 100 010 001 110 101 011 111; do
  $PY -m harness_sec.run_recipe --config harness_sec/configs/$arm.yaml \
    --susvibes-dir "$SUSVIBES_DIR" --tasks-file data/tasks_8.json \
    --out runs/E1/$arm --resume --task-timeout 1800
done
```

### 第二步：48 组配方（5 人分工，见 `data/recipe_assignment.md`）

```bash
# 以 P1 的 10 个配方为例
for r in 01 06 11 16 21 26 31 36 41 46; do
  $PY -m harness_sec.run_recipe --config harness_sec/configs/recipes/$r.yaml \
    --susvibes-dir "$SUSVIBES_DIR" --tasks-file data/tasks_8.json \
    --out runs/R48/$r --resume --task-timeout 1800
done
```

跑批前建议 `caffeinate -dimsu &`（Mac）或 `systemd-inhibit`（Linux），防止睡眠把 API 连接挂死。

## 4. 规则（必须遵守，否则数据不可比）

1. **代码冻结**：用同一 commit；不改 configs、不改 `tasks_8.json`、不改评测器；
2. **预算固定**：`params.max_steps: 60`（configs 已写死）；不要传 `--max-steps` 覆盖；
3. **模型固定**：`deepseek-chat`；所有人一致；
4. **只跑自己名下的配方**，不要重复跑别人的（浪费钱、还可能覆盖结果）；
5. **失败重跑用 `--resume`**，不要删整个 `runs/`；
6. 不要把 API key、`runs/`、`data/official/*.jsonl` 提交进 git。

## 5. 结果怎么交（每人交 3 样）

每个配方跑完，目录 `runs/R48/<配方>/` 里至少有：

```
predictions.jsonl       # 最终 patch（评测用）
predictions_first.jsonl # 首版 patch（算 RescueRate）
<任务>/episode.json      # 每次运行的记录（attempts、findings、agent_error）
<任务>/trace.jsonl       # agent 行为日志（排查用）
```

**提交方式（三选一）**：
- 打一个小 zip：`zip -r R48_<你的名字>.zip runs/R48`，发群/网盘（**不要含 `_repos`**）；
- 推到自己的 git 分支：`git checkout -b results/<你的名字>`，只 add `runs/R48` 下的小文件；
- 直接把 `predictions.jsonl` 和 `episode.json` 打包发 P5 汇总。

## 6. 评测怎么分工

- 评测**不需要 API key**，任何人本机都能做；
- 每人评自己跑的配方（每台机器镜像都在本地）：
  ```bash
  for r in 01 06 11; do
    $PY -m harness_sec.evaluate --run-id "M0_R48_$r" \
      --predictions runs/R48/$r/predictions.jsonl \
      --susvibes-dir "$SUSVIBES_DIR" --max-workers 1 --local-images --no-rescue
  done
  ```
- 或者只交 `predictions.jsonl`，由 P5 在一台机器上统一评测（推荐，口径一致）。

## 7. 汇总（P1 / P5 做）

```bash
# 把所有人的 runs/R48/*/predictions.jsonl 收集到同一台机器后
python3 scripts/collect_results.sh      # 收集/检查
python3 scripts/analyze_recipes.py --results results/R48/results.csv
python3 scripts/compare_gains.py --results results/R48/results.csv   # 与官方策略增益对比
```

## 8. 成本参考（每人）

| 项目 | 数量 | 预计 |
|---|---|---|
| 8 臂（P1） | 64 次运行 | ¥2–10 |
| 48 组（每人 9–10 个配方 × 8 任务） | 72–80 次运行/人 | ¥3–20/人 |
| 镜像磁盘（8 任务） | — | 5–10 GB |

## 9. 出问题先看这里

- `HTTP 401`：API key 无效/过期/无余额（`run_recipe` 会提前中止）；
- 全部 `empty_patch`：先看 `episode.json` 的 `agent_error`；
- 评测 `?`：报告缺失，常见是镜像拉取 429（用 `--local-images`）或单个任务测试日志解析失败（`evaluate` 已容忍）；
- 任务卡住超过 30 分钟：`--task-timeout 1800` 会自动跳过，重跑 `--resume` 即可。
