# 官方策略增强数据集（对照臂用）

- 上游：https://github.com/LeiLiLab/susvibes
- commit：（记录失败）
- 生成命令：`python3 scripts/prepare_official_strategies.py --strategies generic self-selection oracle`
- 用途：作为「现有安全策略」的对照；**主对照建议用 `self-selection`**（官方最强的可部署策略），`generic` 作官方默认，`oracle` 只作上界。

| 策略 | 文件 | 任务数 | 说明 |
|---|---|---:|---|
| generic | `data/official/generic.jsonl` | 186 | 通用安全提示（官方 harness 默认） |
| self-selection | `data/official/self-selection.jsonl` | 186 | agent 自选 CWE（官方主推可部署策略，**主对照**） |
| oracle | `data/official/oracle.jsonl` | 186 | 真实 CWE（信息上界，不可部署） |

> 这些文件只是把策略文本拼进 `problem_statement`；评测器、agent、任务都不变。
