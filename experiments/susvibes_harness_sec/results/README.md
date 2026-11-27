# P1–P5 实验评测汇总

按分工编号归档。P1、P2、P3、P4、P5 目录均包含主实验报告和逐任务数据；P5 同时保留历史合成流程实验与逐项证据。

| 实验 | 评测范围 | 配方或实例 | FuncPass | SecPass | Joint | 报告与数据 |
| --- | --- | --- | ---: | ---: | ---: | --- |
| P1 | SusVibes · 10 配方 × 8 任务，另有无机制对照 | 21 / 31 / 26 | 7/8 / 6/8 / 5/8 | 各 2/8 | 各 2/8 | [报告](P1/REPORT.md) · [CSV](P1/results.csv) · [原始报告](P1/eval_reports/) |
| P2 | SusVibes · 10 配方 × 8 任务 | 22 / 27 / 32 / 17 | 6/8 / 6/8 / 5/8 / 4/8 | 各 2/8 | 各 2/8 | [报告](P2/REPORT.md) · [CSV](P2/results.csv) · [原始报告](P2/eval_reports/) |
| P3 | SusVibes · 10 配方 × 8 任务 | 28 / 03 / 08 / 18 | 7/8 / 6/8 / 5/8 / 7/8 | 2/8 / 1/8 / 1/8 / 1/8 | 2/8 / 1/8 / 1/8 / 1/8 | [报告](P3/REPORT.md) · [CSV](P3/results.csv) · [原始报告](P3/eval_reports/) |
| P4 | SusVibes · 9 配方 × 8 任务，Windows 试验（已清洗伪影） | 19 / 29 / 04 / 39 | 5/8 / 3/8 / 6/8 / 6/8 | 2/8 / 2/8 / 1/8 / 1/8 | 2/8 / 2/8 / 1/8 / 1/8 | [报告](P4/REPORT.md) · [CSV](P4/results.csv) · [原始报告](P4/eval_reports/) · [清洗说明](P4/CLEANING_NOTE.md) |
| P5 | SusVibes · 9 配方 × 8 任务 | 25 | 5/8 | 4/8 | 4/8 | [报告](P5/REPORT.md) · [实验报告](P5/EXPERIMENT_REPORT.md) · [CSV](P5/results.csv) · [原始报告](P5/eval_reports/) |

## 评测口径

- **指标** · FuncPass 为功能通过，SecPass 为安全通过，Joint 要求同一任务或实例同时满足两项。
- **配方** · 表中列出各组最高或代表性 Joint 配方，分数按配方顺序展示（P1 最高 `21` / `26` / `31` 为 2/8，另有 `36` 为 1/8；P2 最高 `17` / `22` / `27` / `32` 为 2/8；P3 配方 `28` 唯一最高 2/8，其余 `03` / `08` / `18` / `23` / `38` 为 1/8；P4 配方 `19` / `29` 为 2/8，`04` / `24` / `39` 为 1/8；P5 配方 `25` 唯一最高 4/8，次高 `30` 为 2/8，`05` / `20` / `40` 为 1/8）。完整 48 组配方与逐任务记录见[主实验配方汇总](all_results.csv)及[逐任务长表](per_task.csv)。
- **范围** · P1–P5 覆盖全部分配的 48 组配方 × 8 个 SusVibes 仓库任务（共 384 项，外加 P1 无机制对照 `base_none`，后者功能 5/8、联合 0/8），均为单次种子运行。P4 原始 predictions 含 Windows 环境伪影（mode 变更、ceph symlink 删除），已清洗并重新评测 wagtail-5c7a 与 ceph，现为 8 任务口径；其余 6 个任务沿用原报告。[P4 清洗说明](P4/CLEANING_NOTE.md) · [P4 环境与实验记录](P4/EXPERIMENT_REPORT.md)
- **P5 归档状态** · 全部 9 个配方 × 8 个仓库任务（72 项）已完成单次运行与官方 SusVibes 评测（均 `eval_status=tested`，无容器失败或缺失），另保留 2026-11-13 与 2026-11-25 历史合成流程检查作为独立记录。[配方分配](../data/recipe_assignment.md) · [任务清单](../data/tasks_8.json) · [历史记录](P5/REPORT.md)

## 文件说明

| 路径 | 内容 |
|---|---|
| `results/P1/results.csv` / `REPORT.md` | P1 汇总与分析 |
| `results/P2/results.csv` / `REPORT.md` | P2 汇总与分析 |
| `results/P3/results.csv` / `REPORT.md` / `SUMMARY.csv` | P3 汇总与分析 |
| `results/P4/results.csv` / `REPORT.md` / `CLEANING_NOTE.md` | P4 清洗后的最终 8 任务结果 |
| `results/P5/results.csv` / `REPORT.md` / `EXPERIMENT_REPORT.md` | P5 结果与历史记录 |
| `results/<组>/eval_reports/<配方>/<iid>.json` | 每个任务的官方 `report.json`（原始证据） |
| `results/all_results.csv` | P1–P5 合并汇总 |
| `results/per_task.csv` | 五组逐任务 func/sec/joint（长表，便于画图） |

## 重要说明

1. **P4 是 trial**：Windows 兼容补丁未合入主线；原始 predictions 的 mode/symlink 伪影已清洗并重新评测 5c7a/ceph，P4 现为 8 任务口径。
2. 原始 `predictions.jsonl` / `trace.jsonl` **未入库**（体积原因，P4 的 ceph patch 原始约 38 万字符）；需要时可从各组 zip/云盘获取。
3. 所有结果均为单 seed、方向性结论；跨组比较请以 Joint 数和逐任务表为准。
