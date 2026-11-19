# 复现记录（每次跑实验前更新）

> 目的：任何人拿到仓库，能知道"你们用的是哪个版本的上游、哪个模型、哪批任务"。

## 1. 上游 SusVibes

| 项 | 值 |
|---|---|
| 仓库 | https://github.com/LeiLiLab/susvibes |
| **commit** | `5d957e6f1850595623d551d089193532e6fa60ce`（2026-11-12 拉取） |
| 获取方式 | ☐ 依赖 clone　☐ vendor 副本　☐ submodule（三选一，见 `vendor/README.md`） |
| 安装命令 | `pip install -e <susvibes>/` |

## 2. 运行环境

| 项 | 值 |
|---|---|
| Python | （填 `python3 --version`） |
| Docker | （填 `docker --version`；Apple Silicon 需 `--platform linux/amd64`） |
| 磁盘余量 | （填 `df -h`；建议 ≥100 GB） |
| 模型 | `deepseek-chat`（Flash）；检测器同模型、temperature=0 |
| API | `DEEPSEEK_API_KEY`（不要写进仓库） |
| **agent 预算** | `max_steps=60`、write_deadline=12（见 docs/BUDGET.md；改动=换一批实验） |

## 3. 任务与配置

| 项 | 值 |
|---|---|
| 任务清单 | `data/tasks_40.json`（Stage 0 后冻结） |
| Stage 0 结果 | `data/stage0.csv` |
| 臂配置 | `harness_sec/configs/000–111.yaml`（记录 config hash） |
| 跑批日期 | （填） |
| run_id | （填） |

## 4. 结果

| 文件 | 说明 |
|---|---|
| `results/E1/results.csv` | 每个臂的 FuncPass/SecPass/SecPass\|FuncPass/RescueRate |
| `results/E1/predictions/<arm>.jsonl` | 候选补丁（可用于官方评测复跑） |
| `results/E1/summary.md` | `harness_sec.analyze` 生成的表 |

## 5. 已知差异/坑

（例：arm64 跑 x86 镜像慢 2–3 倍；某个任务评测超时被剔除；agent 在宿主机跑不了仓库测试……）
