# 怎么"和官方数据对比"又不违反可比性

> 你的要求我明白：**要证明"加上我们的安全机制，harness 生成/修复代码的安全表现更好了"，并且要能和 SusVibes 官方数据形成对照。**
>
> 两个术语先修正：① SusVibes 官方有 **5 个题面策略**（none/generic/self-selection/oracle/feedback-driven/sec-test），论文报告 3 个（generic/self-selection/oracle），后两个有泄漏只作上界；② 我们的 **48 不是"48 类机制"，是 11 个策略块的 3×4×4=48 组配方**。
> 直接比绝对数字不行（scaffold/模型/预算都不同），但有三条**可辩护的路径**，组合起来就能写进论文。

---

## 核心思想：不比"绝对水平"，比"三样东西"

1. **机制增益（Δ）**：同一 scaffold 下，加机制 vs 不加机制的安全率差；
2. **与官方策略的增益对比**：官方自己报告的题面策略增益（+2.7pp / +3.3pp）vs 我们的增益；
3. **同模型端到端对比**：用**同一个 DeepSeek 模型**跑官方 harness，得到"官方系统 + 同模型"的数字，再和我们的系统比。

---

## 路径 1（必做，零额外成本）：效应量对比

官方论文 Table 5（固定 SWE-agent + Claude 4 Sonnet，186 任务）：

| 官方策略 | FuncPass | SecPass | ΔFuncPass | ΔSecPass |
|---|---:|---:|---:|---:|
| generic（官方基线） | 57.0 | 11.8 | — | — |
| self-selection | 50.0 | 14.5 | **−7.0 pp** | **+2.7 pp** |
| oracle（不可部署） | 55.4 | 15.1 | −1.6 pp | **+3.3 pp** |

我们在同一批任务、同一 scaffold 下测：
- **我们的基线（无机制）**：FuncPass/SecPass；
- **我们的最优配方**：FuncPass/SecPass；
- **Δ_ours = 配方 − 基线**（配对，报区间）。

**论文可以这样写**：
> "在相同评测口径下，我们的机制组合把 SecPass 提升 **X pp**、FuncPass 代价 **Y pp**；作为参照，SusVibes 报告的最强题面策略（oracle）仅提升 3.3pp、且不可部署，可部署的 self-selection 提升 2.7pp 却损失 7.0pp 功能。**注意两者模型与 scaffold 不同，我们只比较增益的方向与幅度，不比较绝对水平。**"

这就是"和官方数据对比"的**合规版本**：比 effect size，不比 level。

**脚本**：`scripts/compare_gains.py` 自动生成这张对比表。

---

## 路径 2（强证明，建议做）：同模型、四组对照（修掉"scaffold 和机制混在一起"的坑）

⚠️ **只比"官方 Agent+DeepSeek" vs "我们的 harness+DeepSeek"会把两个变量混在一起**：差可能来自 scaffold，也可能来自机制，无法归因。
正确做法是**四组**，其中关键是第 ③ 组：**把官方策略放进我们的 harness**（用 `data/official/*.jsonl` 当题面），这样"我们的机制 vs 官方策略"就变成同 scaffold、同模型、同任务的干净对比。

| # | 系统（scaffold） | 模型 | 题面策略 / 机制 | 回答 |
|---|---|---|---|---|
| ① | 官方 harness（SWE-agent / Kimi CLI） | DeepSeek | 官方策略：generic、self-selection | 官方系统在**同模型**下的水平（锚点） |
| ② | 我们的 harness | DeepSeek | **无机制** | 我们的基线 |
| ③ | **我们的 harness** | DeepSeek | **官方策略**（generic / self-selection / oracle） | **同 scaffold 下，官方策略能拿多少** |
| ④ | 我们的 harness | DeepSeek | **我们的最优配方** | 我们的方案 |

要报的差（按证据强度排序）：

| 对比 | 算的是什么 | 论文里回答 |
|---|---|---|
| **④ − ③** | 同 scaffold、同模型下，**我们的机制 vs 官方策略** | **"我们的机制比官方策略更强/功能代价更小"（最干净）** |
| **③ − ②** | 官方策略在我们 scaffold 里的增益 | 官方策略在同 scaffold 下的效果（对照） |
| **④ − ②** | 我们的机制增益 | 主结论（路径 1） |
| **② − ①** | 同模型下 scaffold 的差异 | 校准：我们的 scaffold 没有系统性偏差 |
| ④ − ① | 端到端（系统 vs 系统） | 只能写"同模型端到端"，**不能归因给机制** |

具体怎么跑：
```bash
# ① 官方 harness + DeepSeek：装 SWE-agent（litellm 接 deepseek），用 data/official/*.jsonl 的题面
# ② 我们的基线
python3 -m harness_sec.run_recipe --config harness_sec/configs/baseline.yaml \
  --susvibes-dir "$SUSVIBES_DIR" --tasks-file data/tasks_8.json --out runs/E2/base_none
# ③ 我们的 harness + 官方策略（一键脚本）
bash scripts/run_official_strategy_arm.sh self-selection data/tasks_8.json runs/E2/ours_selfselect
# ④ 我们的 harness + 我们的配方
python3 -m harness_sec.run_recipe --config harness_sec/configs/recipes/XX.yaml \
  --susvibes-dir "$SUSVIBES_DIR" --tasks-file data/tasks_8.json --out runs/E2/ours_best
```

**成本**：装 SWE-agent 约 0.5–1 天；8 任务 × 2 策略 = 16 次运行，¥2–10。
**注意**：8 个任务样本小，②−① 校准只作**方向性证据**；主效应仍用 24–40 个任务的确认阶段。

---

## 路径 3（可选加分）：把机制接到官方 harness 上

把 M2/M3 做成官方 harness 的"插件"（在 patch 生成后插入检测/门禁），在**官方 scaffold 内**做 on/off 对照。
这是最强的"机制与 scaffold 无关"证明，但工程量大（2–3 天），建议放到论文后期/加分项。

---

## 论文里最终的对照表（建议格式）

| 系统 | 模型 | 安全策略 | FuncPass | SecPass | ΔSec vs 同系统基线 | ΔFunc |
|---|---|---|---:|---:|---:|---:|
| 官方 SWE-agent | DeepSeek | generic | | | — | — |
| 官方 SWE-agent | DeepSeek | self-selection | | | | |
| 我们的 harness | DeepSeek | 无机制 | | | — | — |
| 我们的 harness | DeepSeek | 官方 self-selection | | | | |
| 我们的 harness | DeepSeek | **最优配方（我们的机制）** | | | **+X pp** | **−Y pp** |
| *（背景）论文 SWE-agent* | *Claude 4 Sonnet* | *self-selection* | *50.0* | *14.5* | *+2.7* | *−7.0* |
| *（背景）论文 SWE-agent* | *Claude 4 Sonnet* | *oracle* | *55.4* | *15.1* | *+3.3* | *−1.6* |

> 最后两行标灰/斜体，注明"不同模型与 scaffold，仅作增益参照"。

---

## 三条必须写进 Limitations 的话

1. 绝对数值不可与 SusVibes 榜单直接比较（scaffold/模型/预算不同）；
2. 与官方策略的对比是**增益幅度**对比，不是同口径绝对水平；
3. 任务子集（8 个）较小，官方策略增益来自其 186 任务全量报告，非同口径。

---

## 建议执行顺序

1. **现在**：跑完 48 组 → 得到我们的 `Δ_mechanism`（路径 1，零成本）；
2. **本周**：P1 装 SWE-agent + DeepSeek，跑 8 任务 × 2 策略（路径 2，校准）；
3. **有余力**：路径 3（插件到官方 harness），作为论文加分/后续工作。
