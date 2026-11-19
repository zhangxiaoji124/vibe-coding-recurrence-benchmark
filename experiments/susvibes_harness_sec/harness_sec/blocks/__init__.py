"""11 块积木的注册入口：只有 import 本包，所有块才会注册到 base._REGISTRY。"""
from . import (  # noqa: F401
    k1_generic,
    k2_threat,
    k3_repo,
    l1_self,
    l2_reviewer,
    p_sast,
    e_exec,
    a_gate,
    s_contract,
    f_feedback,
    c_loop,
)
