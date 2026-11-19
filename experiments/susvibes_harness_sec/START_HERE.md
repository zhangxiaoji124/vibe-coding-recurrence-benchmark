# START HERE（发给 5 个人的第一页）

> 目标：在 SusVibes 的真实任务上，跑 48 组"安全机制配方"，比较 FuncPass / SecPass，并回答"harness 应如何提供知识、获取证据、控制过程"。

---

## 1. 你要发什么给组员（两种，按人分）

| 对象 | 发什么 | 怎么用 |
|---|---|---|
| **P1 + 需要改代码的人** | GitHub 仓库地址 | `git clone` / `git pull` |
| **只跑实验的人** | `Harness安全机制实验_YYYYMMDD.zip`（约 120 KB） | 解压即用，不需要 git |

> 发 zip 前先跑一次 `bash scripts/make_release_zip.sh`，确保是最新代码。
> **Docker 镜像（40 GB）和 API key 不在包里**，每人自己准备。

---

## 2. 每人 30–60 分钟上手（5 步）

```bash
# ① 拿代码
#    A) zip：解压后进目录
#    B) git：git clone <仓库地址> && cd Harness安全机制实验

# ② 装上游 SusVibes（只读依赖，只做一次）
git clone https://github.com/LeiLiLab/susvibes.git ../susvibes
cd ../susvibes && pip install -r requirements.txt && pip install -e . && cd -

# ③ 配模型 key（只在新终端有效，永远不要写进文件/提交）
export DEEPSEEK_API_KEY=sk-...

# ④ 自检三连（零 API 零 docker，必须全绿）
python3 tests/test_base.py        # 9/9
python3 tests/test_blocks.py      # 6/6
bash scripts/integration.sh       # 8 臂 + 3 个配方 dry-run 全过

# ⑤ 装 Docker（如果还没有）：Docker Desktop 启动，磁盘 ≥ 20 GB
```

**三连不绿 → 把报错截图发群里，不要自己改代码。**

---

## 3. 角色与分工

| 人 | 主责 | 跑哪些配方（48 组里） |
|---|---|---|
| **P1** | 总装、环境、集成、GitHub 主仓库 | 01, 06, 11, 16, 21, 26, 31, 36, 41, 46（10 组） |
| **P2** | M1 知识三块（K1/K2/K3） | 02, 07, 12, 17, 22, 27, 32, 37, 42, 47（10 组） |
| **P3** | M2 检测（L1/L2/P）+ llm | 03, 08, 13, 18, 23, 28, 33, 38, 43, 48（10 组） |
| **P4** | M2 执行验证 + M3 门禁/契约（E/A/S） | 04, 09, 14, 19, 24, 29, 34, 39, 44（9 组） |
| **P5** | 官方评测、统计、图表、结果汇总 | 05, 10, 15, 20, 25, 30, 35, 40, 45（9 组） |

完整分配见 `data/recipe_assignment.md`（组号 → 配置 → 负责人）。

---

## 4. 实验流程（六个阶段，每阶段有门槛）

| 阶段 | 时间 | 谁 | 做什么 | 门槛（不过不进下一阶段） |
|---|---|---|---|---|
| **P0 环境** | Day 0 | 全员 | 装上游、配 key、自检三连 | 三连全绿 |
| **P1 M0 单任务** | Day 1–2 | P1 跑，P5 评测 | 1 个任务 × 4 臂：无机制 / generic / self-selection / 我们的第 1 组 | 4 臂都出 FuncPass/SecPass 布尔 |
| **P2 任务冻结** | Day 2–4 | P5 | Stage 0 筛 16–20 个任务 → 冻结 `data/tasks_8.json` → 跑 3 个官方基线臂 | 8 个任务 ok；3 个基线 predictions 齐全 |
| **P3 48 配方** | Week 1–2 | 全员 | 每人按分配跑 9–10 组 × 8 任务 | 48 组都有 `predictions.jsonl` |
| **P4 评测+分析** | Week 2 | P5 | 官方评测 48 组 + 基线；`analyze_recipes` 出排名与边际效应 | 排名表 + 机制边际效应表 |
| **P5 确认** | Week 3 | 全员 | top-12 配方 × 24–40 任务重跑 | ΔSecPass 区间下界 > 0 且 FuncPass 下降 ≤5pp |
| **P6 写作** | Week 3–4 | 全员 | 论文/中期/答辩 | 数字可追溯、图表可复现 |

详细命令见 `docs/RUNBOOK.md`。

---

## 5. 每天怎么协作

1. **只改自己文件**（见 `docs/OWNERS.md`），别人文件只读；
2. **每天 17:00** P1 跑 `bash scripts/integration.sh`，红灯当天修；
3. **跑批期间冻结代码**：只允许换 `--config` 和 `--out`，不许改 `.py`；
4. **同一批任务**：所有人必须用 `data/tasks_8.json`；不许自己换任务；
5. **官方评测只由 P5 跑**（评测环境不同会污染结果）。

---

## 6. 结果怎么交（只交这三个，别交整个 runs/）

```
runs/R48/<组号>/predictions.jsonl          ← 最终补丁
runs/R48/<组号>/predictions_first.jsonl    ← 首版补丁（算 RescueRate）
runs/R48/<组号>/<iid>/episode.json         ← 每个任务的轨迹摘要
```

打包命名：`R48_<组号>_<你的名字>.zip`，发群里或传给 P5。

---

## 7. 出事找谁

| 现象 | 先查 | 找谁 |
|---|---|---|
| 三连不绿 | 报错截图 | P1 |
| 拉镜像失败/超时 | 网络、磁盘 | P1 |
| `patch_chars=0` | `episode.json` 的 `reply_chars` | P3 |
| `n_findings=0` | 是否有 `[warn]`（LLM key/网络） | P3 |
| 评测 `empty_model_patch` / `model_patch_error` | `report.json` 的 `eval_status` | P5 |
| 结果对不上/缺任务 | 是否用了同一批任务 | P5 |

---

## 8. 一句话

**先让 P1 打通 P0–P1（单任务 4 臂），再全员进 P3（48 配方）；P5 统一评测，最后 P5 出排名 + 边际效应，全员写论文。**
