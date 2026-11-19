# 步数预算与 agent scaffold：必须写进论文的口径

> 回答一个关键问题：**SusVibes 本身限不限制 agent 步数？我们加的 40 步限制是哪来的？两者一样吗？**

## 1. 事实

| 层 | 有没有步数限制 | 依据（本地仓库核实） |
|---|---|---|
| **SusVibes 数据集 / 官方评测器** | ❌ **没有** | 评测只看最终 patch，跑功能测试 + 隐藏安全测试 |
| **官方 SWE-agent runner** | ✅ 有：`per_instance_call_limit: 200`（调用次数上限），`per_instance_cost_limit: 0`（费用不限） | `evaluation_harness/swe_agent/setting.yaml` |
| **官方 OpenHands runner** | ✅ 建议 `--max-iterations ≈ 200` | `evaluation_harness/openhands/README.md` |
| **Kimi CLI / Claude Code / Gemini CLI** | 由各自 CLI 的默认值决定（仓库未统一规定） | `evaluation_harness/*/` |
| **我们的 `builtin` agent** | ✅ **自己设的**：`max_steps`（默认 40，现冻结为 **60**）+ 写文件截止线 12 步 | `harness_sec/agents/builtin.py`、`run_recipe.py` |

**结论**：
1. SusVibes **不限制**步数；限制来自你选的 agent scaffold；
2. 我们的 40/60 步是**自研 scaffold 的选择**，不是 SusVibes 的；
3. **和官方 harness（~200 次调用）不一样**——我们的预算低 3–5 倍。

## 2. 对实验结果的影响

| 比较 | 是否公平 | 说明 |
|---|---|---|
| **我们的臂 vs 我们的臂**（8 臂 / 48 组） | ✅ 公平 | 所有臂用同一个 agent、同一个 `max_steps`、同一个写文件截止线 |
| **我们的臂 vs SusVibes 论文/榜单** | ❌ **不可直接比** | scaffold 不同、预算不同（40/60 vs 200）、模型不同（DeepSeek Flash vs Claude 4 Sonnet） |
| **我们的臂 vs 官方 harness 跑出的数** | 只有同 scaffold 才公平 | 想对照就必须用官方 SWE-agent 重跑一遍 |

**M1/M2 不改步数**（知识注入、检测不消耗 agent 步数）；**M3 的重做会增加总调用次数**——这是"控制机制"这个处理本身的一部分，必须把成本（轮数/调用数）一起报出来。

## 2.5 写文件截止线的执行方式

`HARNESS_WRITE_DEADLINE=12`（默认）之后，如果还没写过文件：
1. 先给一次强提示（"必须 write_file"）；
2. 仍然只读不写时，**禁用 `read_file/list_files/search`**，只允许 `write_file/done`；
3. 再过 10 步还没写 → 提前终止（记为 `no_write_after_deadline`，patch 为空）。

这条规则在**所有臂上完全一致**，属于 scaffold 的固定策略，不作为处理变量。

## 3. 我们定死的规则（预注册）

1. **预算冻结**：所有正式实验统一 `max_steps: 60`（写在 `configs/*.yaml` 的 `params.max_steps`），写文件截止线 12 步；
2. **任何改动 = 换一批实验**：改了步数/截止线/模型，就不能和旧数据混在一起比较；
3. **论文 Setup 必须写**：agent scaffold（自研 builtin）、`max_steps=60`、write_deadline=12、模型 `deepseek-chat`、评测器官方；
4. **绝对数值只在本 scaffold 内解释**；引用 SusVibes 榜单数字时必须注明"不同 scaffold，不可直接比较"；
5. **成本一起报**：平均步数、调用次数、¥ 费用（`scripts/api_cost.py`）。

## 4. 必做的两个校准（否则答辩会被问）

1. **预算敏感性**：挑 2–3 个任务，对比 `max_steps=40 / 60 / 120` 的 FuncPass，说明"60 步是否够用"；
2. **scaffold 校准**：用官方 SWE-agent（或 Kimi CLI tutorial）在同一个任务上跑一遍，确认我们的 baseline FuncPass 与官方 harness **同量级**（不要求一样，但不能差一个数量级）。

## 5. 一句话

> **SusVibes 不限步数；40/60 步是我们 scaffold 的预算，远低于官方 SWE-agent 的 ~200 次调用。臂间比较公平，但与论文/榜单不能直接比——必须写进 Setup，并做一次预算敏感性和一次官方 scaffold 校准。**
