# A 安全验收（P4）

## 任务
实现 `harness_sec/blocks/a_gate.py` 里对应类的 `decide(findings, ctx)`，目的是：决定 deliver/retry/block。

## 输入
`findings, ctx`（字段见 `harness_sec/base.py`，**已冻结，不许改**）

## 输出
`Action`

## 接口
实现 `BlockBase` 的 `decide(findings, ctx)`；不要新增构造函数必填参数。

## 禁止
- 不许改 `base.py`；
- 不许 import 其他 block；
- 不许读 `test_patch`/`security_patch`/`golden_patch`（`Ctx` 里本来就没有）；
- 不许把隐藏测试或具体答案写进提示词。

## 验收
high/medium → retry；空/low → deliver；并且 `python3 tests/test_blocks.py` 通过。

## 给 AI 的一句话
> 按上面的接口实现，先读 `base.py` 的 `Finding`/`Ctx` 定义，再读同目录另一个已实现块（如 `f_feedback.py`）照风格写；完成后跑 `python3 tests/test_blocks.py`，把失败信息贴回来继续改。
