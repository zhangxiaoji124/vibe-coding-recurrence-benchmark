# vendor/：上游 SusVibes 的只读副本（可选）

本目录**不放代码**，只放一份"上游快照"，二选一：

## 方案 A：不 vendor（默认，仓库最小）

```bash
git clone https://github.com/LeiLiLab/susvibes.git ../susvibes
cd ../susvibes && pip install -r requirements.txt && pip install -e . && cd -
```

跑实验时用 `--susvibes-dir ../susvibes`。**需要联网 + 手动 clone**。

## 方案 B：vendor 只读副本（仓库 ~20 MB，一键/离线可看）

SusVibes 整个仓库只有 21 MB（数据集 13 MB，去掉 .git 约 17 MB），完全可以放进你们仓库：

```bash
# 在仓库根目录执行
rsync -a --exclude .git --exclude logs --exclude __pycache__ \
  /path/to/susvibes/ vendor/susvibes/
cp vendor/susvibes/LICENSE vendor/susvibes/LICENSE   # 保留 MIT 许可与版权声明
```

然后把 `docs/REPRODUCE.md` 里的 **commit 号**填上。跑实验时：

```bash
pip install -e vendor/susvibes
python3 -m harness_sec.run_recipe --config ... --susvibes-dir vendor/susvibes
```

**规则**：`vendor/susvibes/` 是**上游只读副本**，任何人不许改它；要升级就整目录替换并更新 commit 记录。

## 方案 C：git submodule（想跟上游同步）

```bash
git submodule add https://github.com/LeiLiLab/susvibes.git vendor/susvibes
git commit -m "add susvibes submodule"
# 别人 clone 时：
git clone --recursive <你们仓库>
```

缺点：子模块指针容易被误操作，答辩现场演示不如 vendor 直观。

## 不要做的事

- 不要把 Docker 镜像放进 git（每个 0.4–0.6 GB × 40 任务）；
- 不要把 `logs/`、`runs/` 原始输出放进 git；
- 不要改 `vendor/susvibes/` 里的文件（L1 方案就是"上游只读"）。
