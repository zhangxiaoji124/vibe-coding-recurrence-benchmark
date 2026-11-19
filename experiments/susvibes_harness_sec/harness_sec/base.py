"""harness_sec 契约层 —— W0 冻结后只能 P1 改。

四类类型：
  Ctx       一块积木能看到的一切（永远不含隐藏测试）
  Finding   所有检测块的统一输出（块与块之间唯一的通信格式）
  Action    门禁块的输出（deliver / retry / block）
  BlockBase 11 块积木的公共接口（默认实现 = 什么都不做）

三条铁律（写进代码，防止跑偏）：
  1) Ctx.meta 里永远没有 test_patch / security_patch / golden_patch / env_image_name；
  2) 块与块之间不许直接 import，只通过 Finding / Ctx 通信；
  3) 评测器不在本层：FuncPass / SecPass 只由候选 patch 经官方评测器决定。
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

FORBIDDEN_META_KEYS = ("test_patch", "security_patch", "golden_patch", "env_image_name")
SEVERITIES = ("high", "medium", "low")
ACTIONS = ("deliver", "retry", "block")


@dataclass
class Ctx:
    """一次 episode 里所有积木共享的上下文。"""

    task_id: str
    repo_dir: str
    problem_statement: str
    arm: str = ""
    round_id: str = "R1"
    attempt: int = 0
    meta: dict = field(default_factory=dict)      # cwe_ids / expected_pf / project 等可见信息
    visible: dict = field(default_factory=dict)   # 由 sandbox 填：文件列表、diff 统计等
    history: list = field(default_factory=list)   # 之前轮次的摘要（不含隐藏测试）

    def __post_init__(self):
        for k in FORBIDDEN_META_KEYS:
            if k in self.meta:
                raise ValueError("Ctx.meta 里禁止出现 " + k + "（隐藏测试/参考解不能进机制层）")

    def clone(self, **kw) -> "Ctx":
        data = asdict(self)
        data.update(kw)
        return Ctx(**data)


@dataclass
class Finding:
    """所有检测块（L1/L2/P/E）的统一输出格式。"""

    block: str
    severity: str = "high"
    invariant_id: str = "INV-1"
    entry: str | None = None
    probe: str | None = None
    payload: str | None = None
    expected: str = ""
    actual: str = ""
    evidence: str = ""
    cwe: str | None = None

    def __post_init__(self):
        if self.severity not in SEVERITIES:
            raise ValueError("severity 必须是 " + str(SEVERITIES) + "，收到 " + repr(self.severity))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Finding":
        known = {f: d[f] for f in cls.__dataclass_fields__ if f in d}
        return cls(**known)

    def is_blocking(self) -> bool:
        return self.severity in ("high", "medium")


@dataclass
class Action:
    """门禁块（A）的输出。"""

    kind: str = "deliver"
    reason: str = ""

    def __post_init__(self):
        if self.kind not in ACTIONS:
            raise ValueError("kind 必须是 " + str(ACTIONS) + "，收到 " + repr(self.kind))


class BlockBase:
    """11 块积木的公共接口；子类只实现自己需要的 hook，其余保持默认（无操作）。"""

    name: str = "block"
    owner: str = ""
    implemented: bool = False

    def knowledge(self, ctx: Ctx) -> str:
        """M1：返回要注入到题面前面的安全知识文本（默认不注入）。"""
        return ""

    def artifact(self, ctx: Ctx) -> dict | None:
        """S：返回要写进仓库的契约工件（默认不写）。"""
        return None

    def inject(self, ctx: Ctx) -> str:
        """S：每轮开头要重新注入的文本（默认不注入）。"""
        return ""

    def detect(self, ctx: Ctx) -> list[Finding]:
        """M2：检测当前代码，返回 findings（默认无发现）。"""
        return []

    def feedback(self, findings: list[Finding], ctx: Ctx) -> str:
        """F：把 findings 渲染成给 agent 看的反馈文本。"""
        return ""

    def decide(self, findings: list[Finding], ctx: Ctx) -> Action:
        """A：决定放行 / 重试 / 阻断。"""
        return Action("deliver")

    def policy(self, ctx: Ctx) -> dict:
        """C：返回重做策略参数，如 {"max_retries": 2}。"""
        return {"max_retries": 0}


_REGISTRY: dict[str, type[BlockBase]] = {}


def register(name: str):
    """积木注册装饰器：块名 -> 类。orchestrator 只认名字，不 import 具体块。"""

    def deco(cls):
        cls.name = name
        _REGISTRY[name] = cls
        return cls

    return deco


def available() -> list[str]:
    return sorted(_REGISTRY)


def _ensure_blocks_loaded() -> None:
    """惰性 import blocks/，让任何入口（run_recipe / tests）都能触发注册。"""
    if _REGISTRY:
        return
    import importlib

    importlib.import_module(__package__ + ".blocks")


def build(name: str) -> BlockBase:
    if not name or name == "none":
        raise ValueError("build() 不接受 none，请用 build_many()")
    _ensure_blocks_loaded()
    if name not in _REGISTRY:
        raise KeyError(
            "未注册的积木 " + repr(name) + "；已注册：" + str(available())
            + "（检查 harness_sec/blocks/__init__.py 是否 import 了它）"
        )
    return _REGISTRY[name]()


def normalize(value) -> list[str]:
    """配置里的 m1/m2/m3 允许 str / list / none。"""
    if value is None or value == "" or value == "none":
        return []
    if isinstance(value, str):
        return [value]
    return [v for v in value if v not in (None, "", "none")]


def build_many(value) -> list[BlockBase]:
    return [build(n) for n in normalize(value)]
