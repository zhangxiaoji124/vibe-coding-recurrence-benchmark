# 实验操作手册（RUNBOOK）

> 配套 `START_HERE.md`（给组员的第一页）。这里给每个阶段的**具体命令、产物、判据**。

## 通用约定

- 目录：`susvibes-dir` = 上游 clone 的目录（默认 `../susvibes`）
- 任务集：`data/tasks_8.json`（Stage 0 后冻结，所有人同一批）
- run_id 命名：`<阶段>_<臂>`，如 `M0_baseline`、`R48_01`、`CONF_01`
- 产物：`runs/<阶段>/<臂>/predictions.jsonl` + `<iid>/episode.json`
- **代码冻结**：跑批期间不改 `.py`；改了就重跑该批

---

## P0 环境（Day 0，每人 30–60 分钟）

```bash
git clone <仓库> && cd Harness安全机制实验     # 或解压 zip
git clone https://github.com/LeiLiLab/susvibes.git ../susvibes
cd ../susvibes && pip install -r requirements.txt && pip install -e . && cd -
export DEEPSEEK_API_KEY=sk-...
python3 tests/test_base.py && python3 tests/test_blocks.py && bash scripts/integration.sh
```

**门槛**：三连全绿。P1 把 Python/Docker/上游 commit 写进 `docs/REPRODUCE.md`。

---

## P1 M0：单任务 × 4 臂（Day 1–2，约 2–4 小时）

```bash
# 1) 选 1 个任务（P1）
python3 -m harness_sec.stage0 --susvibes-dir ../susvibes --limit 1 --out runs/M0/stage0
cat runs/M0/stage0/stage0.csv        # 记 iid；ok 必须 True

# 2) 生成官方策略数据集（P5，一次即可）
python3 scripts/prepare_official_strategies.py --susvibes-dir ../susvibes \
  --strategies generic self-selection oracle --out-dir data/official

# 3) 一键跑 4 臂（P1）
bash scripts/m0_single_task.sh <iid>        # 自动：地板 + 第1组 + self-selection
# 官方 generic 臂手动补：
python3 -m harness_sec.run_recipe --config harness_sec/configs/baseline.yaml \
  --susvibes-dir ../susvibes --dataset data/official/generic.jsonl \
  --tasks <iid> --out runs/M0/baseline_generic
python3 -m harness_sec.evaluate --run-id M0_generic \
  --predictions runs/M0/baseline_generic/predictions.jsonl --susvibes-dir ../susvibes
```

**门槛**：4 臂都出 FuncPass/SecPass；第 1 组出现 `n_findings>0` 或 `attempts=2`。
**产物**：`runs/M0/*/` + 结果模板（见 `docs/M0_SINGLE_TASK.md`）。

---

## P2 Stage 0 + 任务冻结（Day 2–4）

```bash
# 1) 多跑几个候选（P5）：16–20 个，挑 8 个 ok
python3 -m harness_sec.stage0 --susvibes-dir ../susvibes --limit 20 --out runs/stage0

# 2) 冻结 8 个任务（P5）
python3 scripts/freeze_tasks.py --stage0 runs/stage0/stage0.csv --n 8 --out data/tasks_8.json

# 3) 3 个官方基线臂（P5）：none / generic / self-selection
for s in none generic self-selection; do
  ds=""
  [ "$s" != "none" ] && ds="--dataset data/official/$s.jsonl"
  python3 -m harness_sec.run_recipe --config harness_sec/configs/baseline.yaml \
    --susvibes-dir ../susvibes $ds --tasks-file data/tasks_8.json --out "runs/R48/base_$s"
  python3 -m harness_sec.evaluate --run-id "R48_base_$s" \
    --predictions "runs/R48/base_$s/predictions.jsonl" --susvibes-dir ../susvibes
done
```

**门槛**：`tasks_8.json` 有 8 个 iid；3 个基线臂 predictions 齐全。

---

## P3 48 配方（Week 1–2）

```bash
# 每人先拿自己第一组试 2 个任务（确认通路）
python3 -m harness_sec.run_recipe --config harness_sec/configs/recipes/01.yaml \
  --susvibes-dir ../susvibes --tasks-file data/tasks_8.json --limit 2 --out runs/R48/01

# 没问题后全量（8 个任务）
python3 -m harness_sec.run_recipe --config harness_sec/configs/recipes/01.yaml \
  --susvibes-dir ../susvibes --tasks-file data/tasks_8.json --out runs/R48/01
```

- 组号 → 人：`data/recipe_assignment.md`
- 每组约 8 个任务 × 20–60 分钟；每人 9–10 组 ≈ 2–3 天（可 2 并发）
- 回传：`R48_<组号>_<名字>.zip`（三个文件，见 START_HERE §6）

**门槛**：48 组 × 8 任务都有 predictions。

---

## P4 官方评测 + 分析（Week 2）

```bash
# 1) 收齐（P5）：把组员的 zip 解压到 runs/R48/<组号>/
#    每个 zip 里应含 predictions.jsonl 与 predictions_first.jsonl
bash scripts/collect_results.sh incoming/

# 2) 批量官方评测（P5）：对 runs/R48/<组号> 逐组跑
python3 -m harness_sec.evaluate --arms-root runs/R48 --susvibes-dir ../susvibes \
  --csv results/R48/results.csv

# 3) 排名 + 机制边际效应（主对照 = self-selection）
python3 -m harness_sec.analyze_recipes --eval-root ../susvibes/logs/eval \
  --baseline eval_R48_base_self-selection --out results/R48
```

产物：
- `results/R48/results.csv`：每组 n / FuncPass / SecPass / Joint / Rescue
- `results/R48/recipes_rank.md`：排名表 + M1/M2/M3 边际效应
- 论文可直接用：Δ vs none / Δ vs generic / Δ vs self-selection

---

## P5 确认（Week 3）

- 挑 top-12（SecPass 高、功能代价 ≤5pp、成本可接受）；
- 在 24–40 个任务上重跑（同命令，换 `--tasks-file data/tasks_24.json`）；
- 判据：**ΔSecPass vs self-selection 的 95% 区间下界 > 0**，且 **ΔFuncPass ≥ −5pp**；
- 可选：对 top-3 用 8 臂做机制归因（`configs/000–111.yaml`）。

---

## P6 写作（Week 3–4）

| 章节 | 主笔 | 数据来源 |
|---|---|---|
| Method（机制层 + 48 组设计） | P1 | `docs/ARCHITECTURE.md`、`docs/EXPERIMENT_48.md` |
| Related Work | P2 | 128 条标注 |
| 检测与效度 | P3 | `analyze_recipes` 的边际效应 + 检测器误报统计 |
| 控制与成本 | P4 | `results.csv` 的 attempts/blocked |
| 数据与统计 | P5 | `results/R48/*`、Wilson 区间 |
| 大创材料 | P1 统稿 | 全员 |

---

## 常见故障速查

| 现象 | 原因 | 处理 |
|---|---|---|
| `KeyError: 未注册的积木` | `blocks/__init__.py` 没 import | 检查是否有人动过；`python3 -c "import harness_sec.blocks"` |
| `DEEPSEEK_API_KEY 未设置` | 环境变量 | 重新 export（新终端要重设） |
| 拉镜像极慢 | 网络/arm64 | `--limit 1` 先试；别一次拉 40 个 |
| `patch_chars=0` | agent 没改代码 | 看 `episode.json` 的 `reply_chars`；0=API 没通 |
| `encoded_model_patch` 类错误 | patch 含二进制 | 让 agent 别改二进制；或换任务 |
| 结果缺任务 | 用了不同 tasks 文件 | 统一 `data/tasks_8.json` |
