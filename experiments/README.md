# experiments/

| 目录 | 内容 | 状态 |
|---|---|---|
| [susvibes_harness_sec/](susvibes_harness_sec/) | 在 SusVibes 外部基准上比较 11 个安全机制积木的 8 臂 / 48 组组合（FuncPass / SecPass） | 准备完成，2026-11-14 冻结任务集 |

- 实验一（安全回归 benchmark）仍在根目录 `cases/` + `harness/` + `run_experiments.py`。
- 本目录的实验需要**外部依赖**（SusVibes 仓库、Docker、API key），与实验一互不影响。
