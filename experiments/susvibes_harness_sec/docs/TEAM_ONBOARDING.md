# 组员上手指南（发给 5 个人）

> 你们**不需要会写代码**，也不需要读源码。每人只需要：装环境 → 跑自己负责的 2 个臂 → 把结果打包回传。

## 0. 两种分发方式，先选一种

| 方式 | 谁用 | 优点 | 缺点 |
|---|---|---|---|
| **A. GitHub 仓库**（推荐给 P1 和改代码的人） | P1 + 负责写积木的人 | 有版本历史、能看到谁改了什么、不会互相覆盖 | 要会 `git clone/pull` |
| **B. 压缩包**（推荐给只跑实验的人） | 只跑实验的组员 | 解压即用、零 git 门槛 | 没有版本管理、**跑之前必须确认是同一份代码** |

> 结论：**代码阶段走 GitHub；跑实验阶段可以发"只读运行包"zip。**
> 但不管哪种，**Docker 镜像（40 GB）和 API key 都不在包里**，要各自准备（见第 2 节）。

## 1. 每个人拿到的"运行包"里有什么

```
Harness安全机制实验/
├── harness_sec/          机制层代码（不要改）
├── tests/                自检用
├── harness_sec/configs/  8 臂配置：000 100 010 001 110 101 011 111
└── docs/                 说明
```

包里**不含**：`runs/`（跑出来的数据）、`logs/`、Docker 镜像、API key。

## 2. 每台机器只装一次（约 20–40 分钟）

```bash
# ① 检查
python3 --version        # ≥3.10
docker --version         # 需要 Docker Desktop 已启动
git --version

# ② 拿上游 SusVibes（二选一）
#    方式1：clone
git clone https://github.com/LeiLiLab/susvibes.git ../susvibes
#    方式2：如果 P1 已经把 vendor/susvibes 放进包里，跳过这步

# ③ 装上游（只读依赖）
cd ../susvibes && pip install -r requirements.txt && pip install -e . && cd -

# ④ 配模型 key（不要写进任何文件、不要提交）
export DEEPSEEK_API_KEY=sk-...
```

## 3. 第一次先自检（5 分钟，零 API 零 docker）

```bash
cd "Harness安全机制实验"
python3 tests/test_base.py        # 应 8/8
python3 tests/test_blocks.py      # 应 6/6
bash scripts/integration.sh       # 8 臂 dry-run 应全过
```

**三个都绿了，再往下走。** 不绿 → 把报错截图发群里，不要自己改代码。

## 4. 每人负责哪两个臂（E1 主实验）

| 人 | 臂 | 含义 | 命令 |
|---|---|---|---|
| **P1** | `000` + `111` | 无机制基线 + 三件套全开 | 见下 |
| **P2** | `100` + `110` | 只有知识 / 知识+检测 | 见下 |
| **P3** | `010` + `011` | 只有检测 / 检测+门禁（核心闭环） | 见下 |
| **P4** | `001` + `101` | 只有门禁 / 知识+门禁（安慰剂） | 见下 |
| **P5** | 不跑 agent | 官方评测 + 汇总 | 见第 6 节 |

```bash
# 每个臂跑 40 个任务（--tasks 文件见 data/tasks_40.json，或直接用 --limit 40）
python3 -m harness_sec.run_recipe \
  --config harness_sec/configs/011.yaml \
  --susvibes-dir ../susvibes \
  --tasks "<instance_id1>,<instance_id2>,..." \
  --out runs/E1/011 \
  --agent builtin
```

**注意**：
- 两个人不要跑同一个臂（会重复花钱）；
- 跑之前 `git status` 确认代码没被改；**跑批期间不许改代码**；
- 每个任务 20–60 分钟，40 个任务建议分批跑（可以先 `--limit 5` 试）。

## 5. 跑完怎么把结果交回来

只交这三个，**不要交整个 runs/ 和 logs/**：

```
runs/E1/011/predictions.jsonl        ← 最终补丁（必须）
runs/E1/011/predictions_first.jsonl  ← 首版补丁（算 RescueRate，必须）
runs/E1/011/*/episode.json           ← 每个任务的轨迹摘要
```

打包：

```bash
cd "Harness安全机制实验"
zip -r "E1_011_<你的名字>.zip" runs/E1/011/predictions.jsonl runs/E1/011/predictions_first.jsonl \
  runs/E1/011/*/episode.json
```

发到群里 / 传给 P5。

## 6. 官方评测只在一台机器上跑（P5 负责）

> 为什么：评测环境不同会污染结果。**所有臂的官方评测必须由同一个人、同一台机器跑。**

```bash
# P5：把各人的 predictions 收齐后
python3 -m harness_sec.evaluate --arms-root runs/E1 --susvibes-dir ../susvibes --csv results/E1/results.csv
```

## 7. 常见问题

| 现象 | 原因 | 怎么办 |
|---|---|---|
| `docker: command not found` | Docker 没装/没启动 | 装 Docker Desktop 并启动 |
| 拉镜像极慢 / 失败 | 网络或 arm64 模拟 | 先 `--limit 1` 试；`SUSVIBES_PLATFORM=linux/amd64` 已默认 |
| `DEEPSEEK_API_KEY 未设置` | 忘了 export | 重新 export（只在新终端生效） |
| `pip install -e` 报错 | Python 版本/依赖 | 用 Python 3.10+，先 `pip install -r requirements.txt` |
| 跑出来 patch 为空 | agent 没改代码 | 看 `episode.json` 的 `reply_chars` 和 `agent_error` |
| 改了代码导致结果不可比 | 违反冻结规则 | 跑批期间**只允许**换 `--out` 和 `--config`，不许改 `.py` |
