# 环境、镜像与资源

## 依赖

| 项 | 说明 |
|---|---|
| Python 3.10+ | 本包只用标准库；`bandit`/`semgrep`/`pyyaml`/`pytest` 按需 |
| Docker Desktop | 任务镜像是 x86_64；Apple Silicon 需 `--platform linux/amd64`（本包已默认） |
| 磁盘 | 40 任务 × 2 镜像 × ~0.5 GB ≈ 40 GB；官方评测建议 ≥100 GB 余量 |
| 内存/CPU | 官方评测 4 GB + 4 核/worker → 16 GB 机器建议 `--max-workers 3` |
| API key | `DEEPSEEK_API_KEY`（agent + 检测器共用） |
| SusVibes | clone 到旁边并 `pip install -e .`（只读依赖） |

## 镜像

- 任务镜像名在数据集 `image_name` 字段里，**不需要自己构建**。
- 拉取：`docker pull --platform linux/amd64 <image_name>`（`stage0.py` 会自动做）。
- 导出起点代码：`docker create` → `docker cp <cid>:/project` → `docker rm`（`sandbox.py` 已封装）。

## 常见坑

1. 镜像 `.git` 必须是单 commit（`stage0.py` 会检查 `git rev-list --count HEAD == 1`）。
2. 不要把 `env_image_name`（参考解镜像）当 agent 环境。
3. agent 在宿主机改代码 → 依赖与本机 Python 可能不一致，agent 跑不了仓库测试是正常的（写进局限）。
4. 跑批前 `docker image prune` 清理，避免磁盘爆。
