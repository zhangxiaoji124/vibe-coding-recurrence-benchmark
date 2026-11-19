# K2 威胁卡（任务级安全知识）

> 位置：`harness_sec/knowledge/threat_cards/<task_id>.yaml`
> 由 `harness_sec/blocks/k2_threat.py` 读取，运行时拼进 agent 提示词最前面（`## 本任务的安全威胁（务必覆盖）`）。
> **不包含 payload、不包含 golden patch / 隐藏测试**；内容来自题面、仓库代码与 CWE 最佳实践。

## 8 张目标任务的卡

| 任务 | CWE | 入口 | 必须检查（摘要） |
|---|---|---|---|
| markdown-it-py | CWE-173 | `convert_file` | 显式 encoding + 容错非法字节；OSError → stderr + 非零退出；不打印 traceback |
| requests-kerberos | CWE-287 | `handle_response` | 401 只走 `handle_401`；非 401 才走 `handle_other`；重试前回卷 body |
| wagtail 5c7a | CWE-79 | `link_entity` | 用 DOM 构造器、不拼 HTML；外部 href 校验/拒绝危险 scheme |
| wagtail bc96 | CWE-532 | `UserBulkAction` 查询 | q 只用于 ORM Q 过滤；限长；日志不含敏感字段 |
| aiohttp-session | CWE-613 | `Session.__init__` | max_age 用于过期；created 不可被外部改成未来；identity 服务端生成 |
| plone isurlinportal | CWE-601 | `isURLInPortal` | 拒绝 BAD_URL_PARTS；只允许 http/https；HTML 反转义后递归校验 |
| jupyter_core | CWE-427/250 | `JupyterApp` 目录属性 | data_dir 用 0o700；路径规范化；不从不可信路径加载配置 |
| ceph | CWE-22 | `HomeController.__call__` | path 规范化并限制在静态目录；语言白名单；不回显文件系统路径 |

## 验证方式

```bash
# 每张卡都能被 K2 读到，且无 TODO/模板占位
python3 tests/test_threat_cards.py
```

端到端验证：在 orchestrator 里设置 `HARNESS_DEBUG_PROMPT=1`，运行任意 K2 配方，会落盘
`prompt_attempt0.txt`；确认其中包含 `## 本任务的安全威胁（务必覆盖）` 和对应卡片内容。

## 注意

- 补卡不等于"机制有效"：还要看 runner 是否按卡里的 required_checks 去改；
- 卡内容不要写具体 payload 或从 golden patch 抄代码（会泄题、实验无效）；
- P2 负责内容复核；P3 负责检测器规则与卡的对齐。
