# 5 人分工与防冲突

| 人 | 负责文件（只改这些） | 交付 | 验收 |
|---|---|---|---|
| **P1** | `base.py` `sandbox.py` `orchestrator.py` `run_recipe.py` `agents/` `configs/` | 编排 + 真实跑通 | 1 个任务出 patch 且被官方评测 |
| **P2** | `blocks/k1_generic.py` `k2_threat.py` `k3_repo.py` + `knowledge/cwe_top25.md` `knowledge/threat_cards/` | M1 三块 + 知识文件 | `tests/test_blocks.py` 相关断言 + 40 任务威胁卡 |
| **P3** | `blocks/l1_self.py` `l2_reviewer.py` `p_sast.py` + `llm.py` + `knowledge/sast_map.yaml` + `prompts/l1_review.md` `l2_review.md` | M2 LLM/工具检测 | 已知漏洞 patch 能报出；参考解误报 ≤1 |
| **P4** | `blocks/e_exec.py` `a_gate.py` `s_contract.py` + `prompts/e_probe.md` | 执行验证 + 门禁 + 契约 | 探针真跑；门禁真阻断 |
| **P5** | `blocks/f_feedback.py` `c_loop.py` `evaluate.py` `analyze.py` `stage0.py` `scripts/` | 反馈/循环 + 评测统计 | 评测可续跑；CSV/表能生成 |

## 每天

1. 只改自己文件；别人文件只读。要改 → 群里 @owner。
2. 接口不够用 → P1 扩 `base.py`，当天通知。
3. **每天 17:00 P1 跑 `bash scripts/integration.sh`**，红灯当天修。
4. 跑批期间冻结代码（yaml 可换）。

## 三条铁律

1. 上游 `../susvibes` 一个文件都不改；
2. `base.py` 冻结后只有 P1 能改；
3. AI 说"写完了"不算完成——测试绿才算。
