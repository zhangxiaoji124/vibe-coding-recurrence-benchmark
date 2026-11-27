# Vibe Coding Recurrence Benchmark

这个仓库研究 AI 辅助代码修改中的安全回归，以及安全审查、验收门禁和修复循环对代码交付的影响。仓库包含多轮回归基准及 SusVibes 安全机制实验。

## 实验报告

SusVibes 主实验 **P1–P5 全部 48 组配方 × 8 个任务（384 项）** 已完成官方 `FuncPass / SecPass / Joint` 评测并全部归档；多轮安全回归历史记录同步保存于 `results/recurrence/`。[实验结果目录](results/) · [统一评分表与统计口径](experiments/susvibes_harness_sec/results/README.md)

| 分组 | 评测范围 | 最高 Joint | 入口 |
| --- | --- | ---: | --- |
| P1 | 10 配方 × 8 任务（另有无机制对照） | 2/8（`21` / `26` / `31`） | [P1 入口](results/P1/) · [报告](experiments/susvibes_harness_sec/results/P1/REPORT.md) |
| P2 | 10 配方 × 8 任务 | 2/8（`17` / `22` / `27` / `32`） | [P2 入口](results/P2/) · [报告](experiments/susvibes_harness_sec/results/P2/REPORT.md) |
| P3 | 10 配方 × 8 任务 | 2/8（`28`） | [P3 入口](results/P3/) · [报告](experiments/susvibes_harness_sec/results/P3/REPORT.md) |
| P4 | 9 配方 × 8 任务（Windows 试验，已清洗伪影） | 2/8（`19` / `29`） | [P4 入口](results/P4/) · [报告](experiments/susvibes_harness_sec/results/P4/REPORT.md) |
| P5 | 9 配方 × 8 任务（另附原版流程与合成复评） | **4/8**（`25`） | [P5 入口](results/P5/) · [主实验报告](experiments/susvibes_harness_sec/results/P5/EXPERIMENT_REPORT.md) |
| 多轮安全回归 | `DeepSeek Chat` / `Flash` / `Qwen2.5-Coder 7B` | — | [历史结果](results/recurrence/) |

## 项目架构

| 实验线 | 运行与配置 | 结果 |
| --- | --- | --- |
| 多轮安全回归 | [cases/](cases/) 定义场景和测试，[harness/](harness/) 负责模型调用与逐轮评测，[run_experiments.py](run_experiments.py) 提供批量入口 | [results/recurrence/](results/recurrence/) 保存逐轮结果，[workspaces/](workspaces/) 保存代码快照，[scripts/](scripts/) 提供汇总和绘图 |
| SusVibes 主实验 | [机制层](experiments/susvibes_harness_sec/harness_sec/) 通过配方编排知识输入、质量检测和反馈控制，调用上游评测器 | [主实验报告及评测数据](experiments/susvibes_harness_sec/results/) |

主实验中，[配方配置](experiments/susvibes_harness_sec/harness_sec/configs/) 选择要启用的机制，[编排器](experiments/susvibes_harness_sec/harness_sec/orchestrator.py) 依次运行知识输入、代理生成、质量检查和反馈控制，[评测入口](experiments/susvibes_harness_sec/harness_sec/evaluate.py) 将生成的补丁交给上游评测器。[机制层架构与调用链](experiments/susvibes_harness_sec/docs/ARCHITECTURE.md)

多轮回归基准的历史记录适合分析个别场景的逐轮变化。比较模型整体表现还需要匹配场景覆盖和重复次数。判断旧入口是否回归时，需要确认同一检查在此前轮次已通过。

## 运行入口

- 多轮回归的配置、测试和结果解释见 [配置与测试](docs/TESTING.md)。离线功能测试无需模型服务。
- SusVibes 主实验的 Docker、上游仓库和模型服务配置见 [实验手册](experiments/susvibes_harness_sec/docs/RUNBOOK.md)。
