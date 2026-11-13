# 配置与测试

以下命令使用 Windows PowerShell。先克隆仓库并进入根目录。示例已用 Python 3.14 验证。

```powershell
git clone https://github.com/zhangxiaoji124/vibe-coding-recurrence-benchmark.git
cd vibe-coding-recurrence-benchmark
python --version
```

## 离线启动功能测试

下面以已保存的 Qwen SQL 查询实现为例，检查普通查询、按角色筛选、排序、关键词查询和年龄筛选。SQLite 使用内存数据库。这个例子只依赖 Python 标准库。

```powershell
Push-Location workspaces/qwen2.5coder_7b/case2_cwe89_sql_query
try {
    python -m unittest discover -s tests -p test_func.py -v
} finally {
    Pop-Location
}
```

预期显示 5 个测试并输出 `OK`。这条命令验证该代码样本的功能，安全检查结果可在对应的 [逐轮 JSON](../results/qwen2.5coder_7b/case2_cwe89_sql_query.json) 中查看。

## 模型配置

| 后端 | 配置 |
| --- | --- |
| 本地 Ollama | 安装并启动服务，默认地址是 `http://127.0.0.1:11434`。评测代码会将名称中包含 `qwen` 的模型路由到 Ollama。 |
| DeepSeek API | 将密钥配置为当前进程的 `DEEPSEEK_API_KEY` 环境变量。模型标识需与账号可用的 API 模型一致。 |

可用下列 PowerShell 命令检查配置，命令只输出状态：

```powershell
Test-NetConnection 127.0.0.1 -Port 11434 -InformationLevel Quiet
[bool]$env:DEEPSEEK_API_KEY
```

批量实验入口是 [run_experiments.py](../run_experiments.py)，接受一个模型标识参数。每个模型与场景的工作目录和结果文件使用固定名称，重复运行前应先保存要保留的实验产物。现有结果可以直接用于离线分析，无需调用模型。

## 阅读结果

每个结果文件对应一个模型和场景。逐轮优先看 `func_pass`（功能测试）、`probe_pass`（安全检查）和 `latency_s`（耗时）。结合前后轮的检查记录解释 `recurrence_status`，区分持续失败和通过后再次失败。

仓库已包含 [PDF 图表](../results/visuals/recurrence_benchmark_report.pdf)。现有汇总和绘图脚本使用原作者机器上的绝对路径；在其他目录运行前需调整脚本内的 `results_root`。绘图脚本还依赖 NumPy 和 Matplotlib，且部分图表标注与计数是固定值。用新结果做报告时应以逐轮 JSON 为准。
