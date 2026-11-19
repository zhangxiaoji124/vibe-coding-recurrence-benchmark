# AI 说明书（每块一页）

用法：打开你负责那块对应的 `.md`，**整页粘给 AI**，让它实现；然后跑：

```bash
python3 tests/test_base.py
python3 tests/test_blocks.py
bash scripts/integration.sh
```

规则：
- AI 说"写完了"不算完成，**测试绿才算**；
- AI 改了 `base.py` 或 import 了别的 block → 直接拒绝；
- 每次会话把"说明书 + AI 输出 + 测试结果"存到 `notes/ai/`。
