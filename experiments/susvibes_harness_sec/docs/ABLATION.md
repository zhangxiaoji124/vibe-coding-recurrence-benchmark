# 消融实验（ablation）：验证"是哪个零件在起作用"

> 目的：31 号配方（K2 + E + A）在 2 个探针任务上把 SecPass 从 0 变成 1。
> 但"组合有效"不等于"每个零件都有用"。消融 = 把 31 的零件逐个拿掉/替换，看效果掉多少。

## 31 的零件

| 零件 | 是什么 | 在 31 里的作用 |
|---|---|---|
| **K2** | 任务级威胁卡（入口/数据流/必须检查/不变式） | 告诉模型"这个任务要防什么、检查什么" |
| **E** | 执行验证：生成 pytest 安全探针并真的跑 | 验证漏洞是否真的可触发 |
| **A** | 安全验收门禁：有 high 发现就重做/拦截 | 防止带高危交付 |
| F/C | 结构化反馈 + 重做循环（最多 2 轮） | 把发现反馈给模型并给预算 |

## 4 个消融配置（`harness_sec/configs/ablation/`）

| 配置 | 相对 31 改了什么 | 用来回答 |
|---|---|---|
| `k2_e_f` | **拿掉 A 门禁**（只反馈，不强制重做/拦截） | 门禁 A 有没有用？ |
| `k1_e_a` | **把 K2 卡换成 K1 通用知识** | 任务级 K2 卡是不是关键？ |
| `k2_l2_a` | **把 E 换成 L2**（LLM 独立审查） | 执行探针 E 是否比 LLM 审查好？ |
| `k2_a` | **拿掉检测器**（只剩 K2 卡 + A 门禁） | 检测本身有没有用？ |

## 怎么读结果（同样 2 个任务）

基线：**31 = 2/2 SecPass PASS**。

| 如果消融结果 | 说明 |
|---|---|
| `k1_e_a` 变成 0/2 | **K2 卡是决定性的**（换回通用知识就失效） |
| `k2_a` 变成 0/2 | **检测器（E）是必需的**（只有卡不行） |
| `k2_e_f` 变成 0/2 | **A 门禁是必需的**（只靠反馈不够） |
| `k2_l2_a` 变成 0/2 | **E 比 L2 更适合这类任务** |
| 四个消融都还是 2/2 | 收益可能来自"卡 + 门禁"以外的因素/偶然，需要重新设计 |

## 和 8 臂因子实验的区别

- **8 臂（000–111）**：M1/M2/M3 **开/关**的粗粒度主效应；
- **消融**：在同一类机制里**换具体策略**（K2 换成 K1、E 换成 L2、拿掉 A）的细粒度归因；
- 两者互补：8 臂回答"哪一层有用"，消融回答"为什么有用、哪个实现细节关键"。

## 跑法（2 个任务，约 ¥0.5，20–30 分钟）

```bash
T="plone__products.isurlinportal_d4fd34990d18adf05a10dc5e2bb4b066798280ba,executablebooks__markdown-it-py_53ca3e9c2b9e9b295f6abf7f4ad2730a9b70f68c"
for c in k2_e_f k1_e_a k2_l2_a k2_a; do
  $PY -m harness_sec.run_recipe --config harness_sec/configs/ablation/$c.yaml \
    --susvibes-dir "$SUSVIBES_DIR" --tasks "$T" \
    --out runs/ablation/$c --resume --task-timeout 1800
done

$PY -m harness_sec.evaluate --arms-root runs/ablation --susvibes-dir "$SUSVIBES_DIR" \
  --max-workers 1 --local-images --no-rescue --csv runs/ablation/results.csv
```

## 注意

- 消融必须用**同一批任务、同一 scaffold、同一模型**，否则不可比；
- 消融只在 2 个任务上做归因，不用于最终效果数字；最终数字用 8 任务/48 组；
- 如果消融显示某零件关键，后续 48 组可以把资源集中到该零件对应的策略上。
