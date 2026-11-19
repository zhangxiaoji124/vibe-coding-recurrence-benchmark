# P1 开工清单（你是 P1：让"机器能跑"变成"整组能跑"）

> P1 不写机制内容（那是 P2–P4），但要对**整条流水线不坏**负责：
> 环境 → M0 跑通 → 任务冻结 → GitHub 发布 → 每天集成 → 修所有集成类 bug。

---

## 0. 环境捷径（重要）

本机已有 conda 环境 **`sv`（Python 3.11.18）**，`susvibes` 已以 editable 方式安装，官方评测 CLI 可用；它的 checkout 在 `/Users/renlvran/Desktop/susvibes-main`，**数据集与你新 clone 的完全一致**（同 md5、186 任务）。

```bash
export PY=/Users/renlvran/miniconda3/envs/sv/bin/python
export SUSVIBES_DIR=/Users/renlvran/Desktop/susvibes-main
bash scripts/env_check.sh
```

**不要**用 base 的 Python 3.14 重新 `pip install`（缺 wheel 会卡住）；也不需要在 `大创论文/susvibes` 上再装一遍。

## 第 0 步：今天（2–3 小时）——把环境跑通

- [ ] **0.1 检查机器**：Python ≥3.10、Docker Desktop 已启动、磁盘 ≥20 GB
  ```bash
  python3 --version && docker --version && df -h . | tail -1
  ```
- [ ] **0.2 装上游 SusVibes（只读依赖）**
  ```bash
  cd "/Users/renlvran/Desktop/大创论文/Harness安全机制实验"
  git clone https://github.com/LeiLiLab/susvibes.git ../susvibes
  cd ../susvibes && pip install -r requirements.txt && pip install -e . && cd -
  ```
- [ ] **0.3 配模型 key（只在新终端有效；不要写进文件）**
  ```bash
  export DEEPSEEK_API_KEY=sk-...
  ```
- [ ] **0.4 自检三连（零 API 零 docker，必须全绿）**
  ```bash
  python3 tests/test_base.py        # 9/9
  python3 tests/test_blocks.py      # 6/6
  bash scripts/integration.sh       # 8 臂 + 3 配方 dry-run 全过
  ```
- [ ] **0.5 记录环境版本**：把 Python/Docker/上游 commit 写进 `docs/REPRODUCE.md`
  ```bash
  git -C ../susvibes rev-parse HEAD    # 填进 REPRODUCE.md
  ```
- [ ] **0.6 生成官方策略数据集（后面基线臂要用）**
  ```bash
  python3 scripts/prepare_official_strategies.py --susvibes-dir ../susvibes \
    --strategies generic self-selection oracle --out-dir data/official
  ```

**今天完成标准**：三连全绿 + `data/official/` 里有 3 个 jsonl。

---

## 第 1 步：Day 1–2 —— M0：1 个任务 × 4 臂

- [ ] 选 1 个任务（拉镜像 + 导出 /project）
  ```bash
  python3 -m harness_sec.stage0 --susvibes-dir ../susvibes --limit 1 --out runs/M0/stage0
  cat runs/M0/stage0/stage0.csv      # 记 iid；ok 必须 True
  ```
- [ ] 跑 4 臂（一键脚本自动跑 3 个，第 4 个手动补）
  ```bash
  bash scripts/m0_single_task.sh <iid>
  # 官方 generic 臂
  python3 -m harness_sec.run_recipe --config harness_sec/configs/baseline.yaml \
    --susvibes-dir ../susvibes --dataset data/official/generic.jsonl \
    --tasks <iid> --out runs/M0/baseline_generic
  python3 -m harness_sec.evaluate --run-id M0_generic \
    --predictions runs/M0/baseline_generic/predictions.jsonl --susvibes-dir ../susvibes
  ```
- [ ] 按 `docs/M0_SINGLE_TASK.md` 的**六个检查点**逐条核对
- [ ] 把结果填进模板（4 行：none / generic / self-selection / 第 1 组）

**完成标准**：4 臂都出 FuncPass/SecPass 布尔；第 1 组出现 `n_findings>0` 或 `attempts=2`。

---

## 第 2 步：Day 2–4 —— Stage 0 + 冻结任务 + 基线臂

- [ ] 多筛几个任务（16–20 个，挑 8 个 ok）
  ```bash
  python3 -m harness_sec.stage0 --susvibes-dir ../susvibes --limit 20 --out runs/stage0
  ```
- [ ] 冻结 8 个任务
  ```bash
  python3 scripts/freeze_tasks.py --stage0 runs/stage0/stage0.csv --n 8 --out data/tasks_8.json
  ```
- [ ] 跑 3 个官方基线臂（none / generic / self-selection）→ 交给 P5 评测
  ```bash
  for s in none generic self-selection; do
    ds=""; [ "$s" != "none" ] && ds="--dataset data/official/$s.jsonl"
    python3 -m harness_sec.run_recipe --config harness_sec/configs/baseline.yaml \
      --susvibes-dir ../susvibes $ds --tasks-file data/tasks_8.json --out "runs/R48/base_$s"
  done
  ```

**完成标准**：`data/tasks_8.json` 有 8 个 iid；3 个基线目录里都有 `predictions.jsonl`。

---

## 第 3 步：发布（M0 通过后）

- [ ] 推 GitHub 主仓库
  ```bash
  git init && git add -A && git commit -m "harness mechanism layer v0.1"
  git remote add origin <组仓库地址> && git push -u origin main
  ```
- [ ] 打 release zip 发群
  ```bash
  bash scripts/make_release_zip.sh
  ```
- [ ] 把 `START_HERE.md` + 群公告发群里（见上一条回复）
- [ ] 建共享结果目录 `incoming/`（已建）

---

## 第 4 步：你负责的 10 组配方（Week 1–2）

你的组号：**01, 06, 11, 16, 21, 26, 31, 36, 41, 46**

```bash
# 先试 2 个任务
python3 -m harness_sec.run_recipe --config harness_sec/configs/recipes/01.yaml \
  --susvibes-dir ../susvibes --tasks-file data/tasks_8.json --limit 2 --out runs/R48/01
# 全量 8 个任务
python3 -m harness_sec.run_recipe --config harness_sec/configs/recipes/01.yaml \
  --susvibes-dir ../susvibes --tasks-file data/tasks_8.json --out runs/R48/01
```

每组跑完回传：`predictions.jsonl` + `predictions_first.jsonl` + `*/episode.json`。

---

## 第 5 步：常驻职责（贯穿全程）

- [ ] **每天 17:00** 跑 `bash scripts/integration.sh`（红灯当天修，不隔夜）
- [ ] **跑批期间冻结代码**：谁改 `.py` 谁负责重跑该批
- [ ] **修所有集成类 bug**：`base.py`/`orchestrator.py`/`sandbox.py`/`agents/`/`config.py`
- [ ] 维护 `docs/REPRODUCE.md`（上游 commit、模型、任务集、run_id）
- [ ] 维护 `results/R48/results.csv` 的归档（P5 产出）

---

## 第 6 步：什么时候找别人

| 现象 | 找谁 |
|---|---|
| 检测器误报/漏报 | P3 |
| 探针跑不起来、门禁空转 | P4 |
| 威胁卡内容不对 | P2 |
| 评测数字异常、缺任务 | P5 |
| 组员环境装不上 | P1（你） |

---

## 一句话

**今天先把三连跑绿 + 生成官方策略数据集；明天做 M0（4 臂）；M0 通过再发群、开跑 48 组。**
