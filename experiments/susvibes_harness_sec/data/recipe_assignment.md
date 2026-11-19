# 48 组配方分配（轮转，每人 10/10/10/9/9）

> 用法：`python3 -m harness_sec.run_recipe --config harness_sec/configs/recipes/XX.yaml --susvibes-dir ../susvibes --limit 10 --out runs/R48/XX`

| 组号 | 配置 | M1 | M2 | M3 | 负责人 |
|---|---|---|---|---|---|
| 01 | recipes/01.yaml | K1-通用知识 | L1-自审 | F-反馈表示 | **P1** |
| 02 | recipes/02.yaml | K1-通用知识 | L1-自审 | C-修复循环 | **P2** |
| 03 | recipes/03.yaml | K1-通用知识 | L1-自审 | A-安全验收 | **P3** |
| 04 | recipes/04.yaml | K1-通用知识 | L1-自审 | S-状态保持 | **P4** |
| 05 | recipes/05.yaml | K1-通用知识 | L2-独立审查 | F-反馈表示 | **P5** |
| 06 | recipes/06.yaml | K1-通用知识 | L2-独立审查 | C-修复循环 | **P1** |
| 07 | recipes/07.yaml | K1-通用知识 | L2-独立审查 | A-安全验收 | **P2** |
| 08 | recipes/08.yaml | K1-通用知识 | L2-独立审查 | S-状态保持 | **P3** |
| 09 | recipes/09.yaml | K1-通用知识 | P-程序分析 | F-反馈表示 | **P4** |
| 10 | recipes/10.yaml | K1-通用知识 | P-程序分析 | C-修复循环 | **P5** |
| 11 | recipes/11.yaml | K1-通用知识 | P-程序分析 | A-安全验收 | **P1** |
| 12 | recipes/12.yaml | K1-通用知识 | P-程序分析 | S-状态保持 | **P2** |
| 13 | recipes/13.yaml | K1-通用知识 | E-执行验证 | F-反馈表示 | **P3** |
| 14 | recipes/14.yaml | K1-通用知识 | E-执行验证 | C-修复循环 | **P4** |
| 15 | recipes/15.yaml | K1-通用知识 | E-执行验证 | A-安全验收 | **P5** |
| 16 | recipes/16.yaml | K1-通用知识 | E-执行验证 | S-状态保持 | **P1** |
| 17 | recipes/17.yaml | K2-任务感知 | L1-自审 | F-反馈表示 | **P2** |
| 18 | recipes/18.yaml | K2-任务感知 | L1-自审 | C-修复循环 | **P3** |
| 19 | recipes/19.yaml | K2-任务感知 | L1-自审 | A-安全验收 | **P4** |
| 20 | recipes/20.yaml | K2-任务感知 | L1-自审 | S-状态保持 | **P5** |
| 21 | recipes/21.yaml | K2-任务感知 | L2-独立审查 | F-反馈表示 | **P1** |
| 22 | recipes/22.yaml | K2-任务感知 | L2-独立审查 | C-修复循环 | **P2** |
| 23 | recipes/23.yaml | K2-任务感知 | L2-独立审查 | A-安全验收 | **P3** |
| 24 | recipes/24.yaml | K2-任务感知 | L2-独立审查 | S-状态保持 | **P4** |
| 25 | recipes/25.yaml | K2-任务感知 | P-程序分析 | F-反馈表示 | **P5** |
| 26 | recipes/26.yaml | K2-任务感知 | P-程序分析 | C-修复循环 | **P1** |
| 27 | recipes/27.yaml | K2-任务感知 | P-程序分析 | A-安全验收 | **P2** |
| 28 | recipes/28.yaml | K2-任务感知 | P-程序分析 | S-状态保持 | **P3** |
| 29 | recipes/29.yaml | K2-任务感知 | E-执行验证 | F-反馈表示 | **P4** |
| 30 | recipes/30.yaml | K2-任务感知 | E-执行验证 | C-修复循环 | **P5** |
| 31 | recipes/31.yaml | K2-任务感知 | E-执行验证 | A-安全验收 | **P1** |
| 32 | recipes/32.yaml | K2-任务感知 | E-执行验证 | S-状态保持 | **P2** |
| 33 | recipes/33.yaml | K3-仓库感知 | L1-自审 | F-反馈表示 | **P3** |
| 34 | recipes/34.yaml | K3-仓库感知 | L1-自审 | C-修复循环 | **P4** |
| 35 | recipes/35.yaml | K3-仓库感知 | L1-自审 | A-安全验收 | **P5** |
| 36 | recipes/36.yaml | K3-仓库感知 | L1-自审 | S-状态保持 | **P1** |
| 37 | recipes/37.yaml | K3-仓库感知 | L2-独立审查 | F-反馈表示 | **P2** |
| 38 | recipes/38.yaml | K3-仓库感知 | L2-独立审查 | C-修复循环 | **P3** |
| 39 | recipes/39.yaml | K3-仓库感知 | L2-独立审查 | A-安全验收 | **P4** |
| 40 | recipes/40.yaml | K3-仓库感知 | L2-独立审查 | S-状态保持 | **P5** |
| 41 | recipes/41.yaml | K3-仓库感知 | P-程序分析 | F-反馈表示 | **P1** |
| 42 | recipes/42.yaml | K3-仓库感知 | P-程序分析 | C-修复循环 | **P2** |
| 43 | recipes/43.yaml | K3-仓库感知 | P-程序分析 | A-安全验收 | **P3** |
| 44 | recipes/44.yaml | K3-仓库感知 | P-程序分析 | S-状态保持 | **P4** |
| 45 | recipes/45.yaml | K3-仓库感知 | E-执行验证 | F-反馈表示 | **P5** |
| 46 | recipes/46.yaml | K3-仓库感知 | E-执行验证 | C-修复循环 | **P1** |
| 47 | recipes/47.yaml | K3-仓库感知 | E-执行验证 | A-安全验收 | **P2** |
| 48 | recipes/48.yaml | K3-仓库感知 | E-执行验证 | S-状态保持 | **P3** |

## 每人清单

- **P1**（10 组）：recipes/01.yaml，recipes/06.yaml，recipes/11.yaml，recipes/16.yaml，recipes/21.yaml，recipes/26.yaml，recipes/31.yaml，recipes/36.yaml，recipes/41.yaml，recipes/46.yaml
- **P2**（10 组）：recipes/02.yaml，recipes/07.yaml，recipes/12.yaml，recipes/17.yaml，recipes/22.yaml，recipes/27.yaml，recipes/32.yaml，recipes/37.yaml，recipes/42.yaml，recipes/47.yaml
- **P3**（10 组）：recipes/03.yaml，recipes/08.yaml，recipes/13.yaml，recipes/18.yaml，recipes/23.yaml，recipes/28.yaml，recipes/33.yaml，recipes/38.yaml，recipes/43.yaml，recipes/48.yaml
- **P4**（9 组）：recipes/04.yaml，recipes/09.yaml，recipes/14.yaml，recipes/19.yaml，recipes/24.yaml，recipes/29.yaml，recipes/34.yaml，recipes/39.yaml，recipes/44.yaml
- **P5**（9 组）：recipes/05.yaml，recipes/10.yaml，recipes/15.yaml，recipes/20.yaml，recipes/25.yaml，recipes/30.yaml，recipes/35.yaml，recipes/40.yaml，recipes/45.yaml
