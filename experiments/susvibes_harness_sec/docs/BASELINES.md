# 对照设计：跟"现有的 SusVibes 安全策略"比，而不是跟"无机制"比

> 你的质疑是对的：**主对照不该是 `baseline.yaml`（无机制）**，那是"地板"，用来证明"机制确实有用"；
> 但论文要主张的"我们更好"，必须跟 **SusVibes 自己已有的可部署策略**（`generic` / `self-selection`）比。

## 1. SusVibes 到底有没有"安全策略"？（基于本地仓库核实）

| 层 | 事实 | 含义 |
|---|---|---|
| **数据集默认** | `datasets/default/susvibes_dataset.jsonl` 的 `problem_statement` **不含任何安全提示** | 默认 = 无策略 |
| **官方 agent harness** | `evaluation_harness/common.py` 的 `apply_safety_hint()` **默认追加 `GENERIC_PROMPT`** | 用官方 harness 跑 = 自动带"通用安全提示" |
| **可选策略** | `susvibes/eval/strategies/`：`generic` / `self-selection` / `oracle` / `feedback-driven` / `sec-test`，通过 `--prepare_dataset` 注入 | 有 5 种，**但不是默认开** |
| **论文的缓解实验** | 这些策略的增益很小（oracle 只 +3.3pp 且功能 -1.6pp） | 说明"题面级提醒"不够，这正是你们机制层的空间 |
| **两个"泄漏型"** | `feedback-driven`（隐藏测试日志差异）/ `sec-test`（直接给隐藏测试） | **只能当上界**，不能当可部署对照 |

结论：**SusVibes 有安全策略，但它们是"题面级、可选的"；默认数据集没有。** 所以对照要分层。

## 2. 四层对照（预注册用）

| 层 | 臂 | 怎么跑 | 用途 |
|---|---|---|---|
| **L0 地板** | 无机制（`baseline.yaml`） | 原始数据集 | 证明"机制确实有用"（不是论文主对照） |
| **L1 官方默认** | `generic` | `--dataset data/official/generic.jsonl` | "现有工程实践"的水平 |
| **L2 主对照** | **`self-selection`** | `--dataset data/official/self-selection.jsonl` | **官方唯一可部署的"增强"策略**——论文要打败的对手（它相对 generic 的代价见下） |
| **L3 上界** | `oracle`（以及 `sec-test`） | 官方增强数据集 | 只作参考，**不主张可部署** |

> 论文写法：`我们的配方 vs self-selection` → 主张"**超过现有可部署增强策略，且功能代价更小**"；`vs generic` → 主张"超过工程默认"；`vs none` → 主张"机制有效"；`oracle` → 只报"离信息上界还差多少"。

## 2.1 论文 Table 5 的原数字（固定 SWE-Agent + Claude 4 Sonnet，186 任务）

| 策略 | FuncPass | SecPass | ΔFuncPass | ΔSecPass | 是否可部署 |
|---|---:|---:|---:|---:|---|
| **generic**（官方 harness 默认，也是论文表里的基线） | 57.0 | 11.8 | — | — | ✅ |
| **self-selection**（先自选 CWE 再写代码） | 50.0 | 14.5 | **−7.0 pp** | +2.7 pp | ✅ |
| **oracle**（直接告诉真实 CWE） | 55.4 | 15.1 | −1.6 pp | +3.3 pp | ❌ 拿不到真实 CWE |

**怎么读**：
1. 论文的对照基线是 **generic**，不是"无提示"——所以我们的对照至少要包含 generic；
2. `self-selection` 是唯一"可部署的增强策略"，但它是**用 7pp 功能换 2.7pp 安全**，性价比差；
3. `oracle` 的 SecPass 略高（15.1）但不可部署，只能当**上界**；
4. 这正是你们的空间：**用机制层（检测+门控+契约）而不是纯提示，去拿安全增益、同时少牺牲功能。**

## 3. 先生成官方增强数据集

```bash
cd "Harness安全机制实验"
python3 scripts/prepare_official_strategies.py \
  --susvibes-dir ../susvibes \
  --strategies generic self-selection oracle \
  --out-dir data/official
```

产出 `data/official/{generic,self-selection,oracle}.jsonl` + `README.md`（记录上游 commit 与任务数）。

## 4. 跑对照臂（同一个任务、同一个 agent、同一个评测器）

```bash
# 主对照：官方 self-selection
python3 -m harness_sec.run_recipe --config harness_sec/configs/baseline.yaml \
  --susvibes-dir ../susvibes \
  --dataset data/official/self-selection.jsonl \
  --tasks <iid> --out runs/R48/baseline_selfselect

# 我们的第 1 组（用原始数据集，K1 由机制层注入）
python3 -m harness_sec.run_recipe --config harness_sec/configs/recipes/01.yaml \
  --susvibes-dir ../susvibes --tasks <iid> --out runs/R48/01

# 官方评测（分别跑）
python3 -m harness_sec.evaluate --run-id R48_selfselect \
  --predictions runs/R48/baseline_selfselect/predictions.jsonl --susvibes-dir ../susvibes
python3 -m harness_sec.evaluate --run-id R48_01 \
  --predictions runs/R48/01/predictions.jsonl --susvibes-dir ../susvibes
```

注意：
- **任务必须同一批**（同 `iid`）；
- **agent/模型/评测器必须完全一致**，唯一变的是"题面里的策略文本" vs "我们的机制层"；
- `self-selection` 会让 agent 额外生成 `selected_cwes.json`，官方评测器会顺带评分——这是正常现象，不要当成我们的机制。

## 5. 分析时的对照

- `analyze_recipes.py --baseline eval_R48_selfselect`：主对照用官方 self-selection；
- 另外单独跑一次 `--baseline eval_R48_baseline`：地板对照，用于"机制有效性"；
- 论文表格建议三列：`vs none`、`vs generic`、`vs self-selection`。

## 6. 一句话

> **SusVibes 不是"没有安全策略"，而是"有 5 种题面级策略、但默认不开、且论文自己测出增益很小"。**
> 所以对照定稿：`generic`（论文基线，必须比）+ `self-selection`（唯一可部署的增强策略，主对照）+ `oracle`（上界，不可部署）；`none` 只用于证明"机制有用"。
