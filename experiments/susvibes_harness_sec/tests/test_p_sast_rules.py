"""P 自定义规则：不依赖 bandit，对逻辑型漏洞也能报 Findings。"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from harness_sec.blocks.p_sast import scan_diff  # noqa: E402

DIFF = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,2 +1,8 @@
 x = 1
+subprocess.run(cmd, shell=True)
+open(os.path.join(base, request.args["p"]))
+resp = redirect(request.args["next"])
+logger.info("token=%s", token)
+data = pickle.loads(raw)
+html = f"<div>{user_input}</div>"
+cur.execute(f"SELECT * FROM t WHERE id={uid}")
"""


def main() -> int:
    fs = scan_diff(DIFF)
    rules = {f.probe for f in fs}
    need = {"shell=True", "path join external", "redirect(url)", "log sensitive", "pickle.loads", "sql format"}
    missing = need - rules
    assert not missing, "缺少规则命中：" + str(missing)
    assert all(f.severity in ("high", "medium", "low") for f in fs)
    assert all(f.evidence for f in fs)
    print("PASS P 自定义规则命中", len(fs), "条：", sorted(rules))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
