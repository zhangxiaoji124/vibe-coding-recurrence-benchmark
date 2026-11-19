# 半天跑通 M0（拿到第一个真实 FuncPass/SecPass）

## 0. 用哪个 Python？（**先看这个，能省半小时**）

本机已有 conda 环境 **`sv`（Python 3.11.18）**，里面 **susvibes 已安装**、`docker/datasets/aiohttp` 齐全。**直接用它**，不要用 base 的 Python 3.14 重装（3.14 缺预编译 wheel，`pip install` 会卡很久）：

```bash
export PY=/Users/renlvran/miniconda3/envs/sv/bin/python
export SUSVIBES_DIR=/Users/renlvran/Desktop/susvibes-main   # 已安装的 checkout（数据集与官方一致）
bash scripts/env_check.sh        # 一键自检
```

> 如果以后想让新 clone（`大创论文/susvibes`，commit 5d957e6）成为正式上游：
> `cd 大创论文/susvibes && /Users/renlvran/miniconda3/envs/sv/bin/pip install -e . --no-deps --no-build-isolation`
> （不下载依赖，几秒完成），然后把 `SUSVIBES_DIR` 指向它。

## 0. 前置检查

- [ ] Python 3.10+
- [ ] Docker Desktop 已启动，磁盘 ≥ 100 GB（全量 40 任务约 40 GB 镜像）
- [ ] 能访问 `deepseek.com`（或你们用的模型 API）
- [ ] SusVibes 已 clone：`git clone https://github.com/LeiLiLab/susvibes.git ../susvibes`
- [ ] `cd ../susvibes && pip install -r requirements.txt && pip install -e .`

## 1. 零成本自检（5 分钟）

```bash
python3 tests/test_base.py
python3 tests/test_blocks.py
bash scripts/integration.sh
```

## 2. 官方评测器跑通（20 分钟）

```bash
cd ../susvibes
python -m susvibes.eval.core --run_id smoke \
  --predictions_path datasets/default/examples/sample_predictions.json --max_workers 1
```

看到 `logs/eval/smoke/none/.../summary.json` 就说明评测器 OK。

## 3. 拉 2 个镜像 + 导出仓库（10–40 分钟，取决于网速）

```bash
cd "Harness安全机制实验"
python3 -m harness_sec.stage0 --susvibes-dir ../susvibes --limit 2 --out runs/stage0
cat runs/stage0/stage0.csv     # 看 ok / pull_s / extract_s / git_commits
```

## 4. 跑一个真实任务（20–60 分钟）

```bash
export DEEPSEEK_API_KEY=sk-...
python3 -m harness_sec.run_recipe --config harness_sec/configs/000.yaml \
  --susvibes-dir ../susvibes --tasks <instance_id> --out runs/E1/000 --agent builtin
```

## 5. 官方评测（5–20 分钟）

```bash
python3 -m harness_sec.evaluate --run-id E1_000 \
  --predictions runs/E1/000/predictions.jsonl --susvibes-dir ../susvibes --out runs/E1/000
```

## 6. 判定

- **FuncPass ≥ 25%** → 可以继续（否则先解决 agent 能力/预算）
- 拿到数字后把 `runs/E1/000/episode.json` 与 `logs/eval/E1_000/` 一起存档
