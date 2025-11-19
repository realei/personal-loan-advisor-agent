# 🎯 Agent评估系统使用指南

## 概述

本评估系统直接从MongoDB中提取Agent的真实运行数据，使用DeepEval框架进行多维度评估。**无需修改现有Agent代码**。

## 特性

✅ **从MongoDB直接获取测试数据** - 使用真实的生产数据进行评估
✅ **支持多个评估指标** - 每个testcase可以同时评估多个metrics
✅ **Reference-based和Referenceless混合** - 灵活的评估方式
✅ **自定义指标** - 工具准确性、参数验证等领域特定指标
✅ **CI/CD集成** - 支持pytest和自动化测试

## 快速开始

### 1. 运行快速评估

```bash
# 评估最近24小时的5个运行
uv run python run_evaluation.py --mode recent --hours 24 --limit 5

# 评估包含"计算月供"的运行
uv run python run_evaluation.py --mode pattern --pattern "计算月供" --limit 3

# 生成完整报告
uv run python run_evaluation.py --mode report --output evaluation_results.json
```

### 2. 运行Pytest测试

```bash
# 运行所有评估测试
uv run pytest tests/test_mongodb_deepeval.py -v

# 只运行质量测试
uv run pytest tests/test_mongodb_deepeval.py::TestMongoDBDeepEval::test_recent_runs_quality -v

# 运行性能基准测试
uv run pytest tests/test_mongodb_deepeval.py -m benchmark -v

# 生成测试报告
uv run pytest tests/test_mongodb_deepeval.py --html=report.html
```

### 3. 生成评估报告

```bash
# 直接生成报告（不运行测试）
uv run python tests/test_mongodb_deepeval.py report
```

## 评估指标说明

### DeepEval标准指标

| 指标 | 说明 | 阈值 | 数据源 |
|------|------|------|--------|
| Answer Relevancy | 回答与问题的相关性 | 0.7 | input vs output |
| Faithfulness | 回答基于事实的程度 | 0.75 | tool_responses vs output |
| Hallucination | 虚构信息检测 | 0.3↓ | 检查output中的虚构 |
| Bias | 偏见检测 | 0.3↓ | 分析output内容 |
| Contextual Relevancy | 上下文相关性 | 0.7 | context vs output |

### 自定义Agentic指标

| 指标 | 说明 | 阈值 | 评估方式 |
|------|------|------|----------|
| Tool Accuracy | 工具选择准确性 | 0.8 | actual vs expected tools |
| Parameter Correctness | 参数合理性 | 0.9 | Referenceless验证 |
| Tool Chain Logic | 工具调用顺序逻辑 | 0.85 | 顺序合理性检查 |
| Response Time | 响应时间 | 5.0s | 从metrics获取 |
| Token Efficiency | Token使用效率 | 4000 | 总token消耗 |

## 文件结构

```
evaluation/
├── evaluation_framework.py    # 评估框架（SOLID设计）
└── live_eval_agent.py        # 实时评估Agent工具

tests/
├── test_mongodb_deepeval.py  # MongoDB集成测试
├── test_agent_evaluation.py  # 原有测试（已更新）
└── deepeval_config.py       # 配置文件

run_evaluation.py            # 快速运行脚本
EVALUATION_GUIDE.md         # 本文档
```

## 配置说明

### 修改评估阈值

编辑 `tests/deepeval_config.py`:

```python
METRIC_THRESHOLDS = {
    "answer_relevancy": 0.7,    # 修改相关性阈值
    "faithfulness": 0.75,        # 修改忠实度阈值
    # ...
}
```

### 添加期望工具映射

```python
EXPECTED_TOOLS_MAP = {
    "新的关键词": ["expected_tool_name"],
    # ...
}
```

### 参数验证规则

```python
PARAMETER_VALIDATION_RULES = {
    "tool_name": {
        "param_name": {
            "type": "number",
            "min": 0,
            "max": 1,
            "format": "decimal"  # 特殊格式要求
        }
    }
}
```

## CI/CD集成

### GitHub Actions示例

```yaml
name: Agent Evaluation

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # 每天运行

jobs:
  evaluate:
    runs-on: ubuntu-latest

    services:
      mongodb:
        image: mongo:5
        ports:
          - 27017:27017

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install uv
          uv venv
          uv pip install -r requirements.txt

      - name: Run evaluations
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          uv run pytest tests/test_mongodb_deepeval.py -v

      - name: Generate report
        if: always()
        run: |
          uv run python run_evaluation.py --mode report --output report.json

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: evaluation-report
          path: report.json
```

## 实时评估集成

将评估工具添加到主Agent中：

```python
from evaluation.live_eval_agent import create_eval_tools

# 在Agent初始化时添加评估工具
agent = Agent(
    ...,
    tools=[
        ...existing_tools,
        *create_eval_tools()  # 添加评估工具
    ]
)
```

然后可以在对话中使用：
- "评估最近的响应质量"
- "检查会话的性能指标"
- "运行性能基准测试"

## 最佳实践

### 1. 定期评估
- 每日运行基准测试
- PR时自动评估
- 监控关键指标趋势

### 2. 测试用例管理
- 从生产数据中选择代表性用例
- 定期更新期望工具映射
- 调整阈值以反映实际需求

### 3. 性能优化
- 监控Token使用趋势
- 识别响应时间瓶颈
- 优化工具调用链

## 常见问题

### Q: 如何处理评估失败？
A: 检查失败原因，可能需要：
- 调整阈值（如果太严格）
- 优化Agent提示词
- 改进工具选择逻辑

### Q: 如何添加新的评估指标？
A: 在 `deepeval_config.py` 中添加配置，然后在测试中实现评估逻辑。

### Q: 评估需要多长时间？
A: 取决于测试用例数量和API调用：
- 快速评估（5个用例）：约30秒
- 完整测试（20个用例）：约2-3分钟
- 基准测试（100个用例）：约5-10分钟

## 评估结果解读

### 良好的指标范围

✅ **优秀**
- Answer Relevancy: > 0.85
- Faithfulness: > 0.85
- Tool Accuracy: > 0.90
- Response Time: < 2s

🟡 **可接受**
- Answer Relevancy: 0.70 - 0.85
- Faithfulness: 0.75 - 0.85
- Tool Accuracy: 0.80 - 0.90
- Response Time: 2-5s

❌ **需要改进**
- Answer Relevancy: < 0.70
- Faithfulness: < 0.75
- Tool Accuracy: < 0.80
- Response Time: > 5s

## 故障排除

### MongoDB连接失败
```bash
# 检查MongoDB是否运行
docker ps | grep mongo

# 启动MongoDB
docker run -d -p 27017:27017 --name mongodb mongo:5
```

### OpenAI API错误
```bash
# 确保设置了API密钥
export OPENAI_API_KEY="your-key-here"

# 或在.env文件中设置
echo "OPENAI_API_KEY=your-key-here" >> .env
```

### 没有测试数据
```bash
# 先运行Agent生成数据
uv run python src/agent/loan_advisor_agent.py

# 或使用analyze_agent_behavior.py生成
uv run python analyze_agent_behavior.py
```

## 总结

这个评估系统提供了：
1. ✅ **零侵入** - 不修改现有Agent代码
2. ✅ **真实数据** - 从MongoDB获取生产数据
3. ✅ **多维评估** - 质量、性能、工具使用等
4. ✅ **灵活配置** - 易于调整和扩展
5. ✅ **CI/CD友好** - 支持自动化测试

开始使用：
```bash
uv run python run_evaluation.py --mode recent
```

Happy Evaluating! 🚀