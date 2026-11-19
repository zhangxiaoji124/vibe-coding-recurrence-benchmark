"""Harness安全机制实验：在 SusVibes 之上新增的机制层。

上游 SusVibes 只读（见 README）；本包提供：
  - 11 块可插拔安全机制积木（M1 知识 / M2 检测 / M3 控制）
  - 一条命令跑一组（run_recipe）→ 官方 FuncPass/SecPass
  - 官方评测封装（evaluate）、统计（analyze）、Stage 0 预筛（stage0）
"""
__version__ = "0.1.0"
