# 架构：从一条命令到 FuncPass/SecPass

```
run_recipe.py --config configs/011.yaml
  │
  ├─ config.load_arm()                 读 yaml → m1/m2/m3 三个列表
  ├─ agents.make_agent(builtin/dsh)    起 agent（在宿主机仓库目录里改代码）
  ├─ orchestrator.run_episode()
  │    ├─ blocks.build_many(m1/m2/m3)  按名字实例化积木（registry）
  │    ├─ M1: knowledge(ctx)           拼进题面（K1/K2/K3）
  │    ├─ S: artifact/inject           写 .security/contracts.yaml 并每轮重注入
  │    ├─ agent.run(ctx, prompt)       改代码（builtin = LLM + JSON 工具循环）
  │    ├─ M2: detect(ctx)              L1/L2/P/E → Finding[]
  │    ├─ M3: a.decide(f)              deliver / retry / block
  │    │      f.feedback(f)            结构化反例 / 自然语言
  │    │      c.policy → max_retries   最多重做几轮
  │    └─ sandbox.git_diff()           候选 patch
  ├─ predictions.jsonl / predictions_first.jsonl
  └─ evaluate.py → 官方 susvibes.eval.core → summary.json → results.csv / analyze
```

## 为什么评测器必须独立

- 机制层只决定"交什么 patch"；FuncPass/SecPass 只由官方评测器产出。
- `test_patch` / `security_patch` / `golden_patch` **永不进 Ctx、永不进检测器**（`base.py` 里有硬校验）。
- M2 的检测器只能看可见代码（仓库 + patch + 题面）——否则 M2 的效应不可解释。

## 两种 agent

| agent | 依赖 | 用途 |
|---|---|---|
| `builtin`（默认） | 只要 LLM API | 自包含，上传 GitHub 后可直接跑 |
| `dsh` | 外部 DSH + `DSH_AGENT_MODULE` | 复用你们已有的 DSH 环境 |
| `fake` | 无 | dry-run / 单测 |

## 数据流

- 输入：SusVibes `susvibes_dataset.jsonl`（只取 `instance_id / image_name / problem_statement / cwe_ids`，其余字段不进 agent）。
- 输出：`runs/<arm>/<iid>/episode.json`、`predictions.jsonl`、`predictions_first.jsonl`。
- 评测：`<susvibes>/logs/eval/<run_id>/.../<iid>/report.json` → `results.csv`。
