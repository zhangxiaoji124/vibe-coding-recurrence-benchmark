"""用本地已拉取的镜像跑官方评测（绕开 Docker Hub 限流 429）。

上游 `susvibes/eval/task.py` 把 `image_loc` 硬编码成 REMOTE，且评测后 `remove_image=True`：
- 每次都去 registry 拉镜像 → 国内镜像站限流（429）时评测失败，表现为 report 缺失、脚本显示 `?`；
- 评测后删镜像 → 下次又要拉。

本模块在**运行时**把 `Deployment.from_pull` 换成本地加载（`from_local`），并强制不删镜像。
**不修改上游任何文件**，只在进程内 monkeypatch。

用法（参数与官方评测器完全一致）：
  python -m harness_sec.local_eval --run_id X --predictions_path pred.jsonl --max_workers 1 --resume
"""
from __future__ import annotations

import sys

from susvibes.core.env import Deployment


def _from_pull_local(cls, logger, image_name, remove_image=False, remove_container=True, max_retries=3):
    return cls.from_local(logger=logger, image_name=image_name,
                          remove_image=False, remove_container=remove_container,
                          max_retries=max_retries)


# 运行时替换（不写上游文件）
Deployment.from_pull = classmethod(_from_pull_local)


def main() -> int:
    from susvibes.eval.core import main as official_main
    sys.argv = ["susvibes-eval-local"] + sys.argv[1:]
    official_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
