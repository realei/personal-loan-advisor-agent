# 评估阈值配置指南

## 📋 概述

项目使用DeepEval进行Agent质量评估，所有评估指标的阈值都可以通过环境变量配置。阈值决定了Agent输出被认为是"通过"的最低标准。

## 🎯 阈值说明

### 标准DeepEval指标

这些是DeepEval内置的标准评估指标：

| 指标 | 环境变量 | 默认值 | 说明 | 越高越好 |
|------|----------|--------|------|---------|
| Answer Relevancy | `EVAL_THRESHOLD_ANSWER_RELEVANCY` | 0.7 | 答案与问题的相关性 | ✅ |
| Faithfulness | `EVAL_THRESHOLD_FAITHFULNESS` | 0.75 | 答案对上下文的忠实度 | ✅ |
| Hallucination | `EVAL_THRESHOLD_HALLUCINATION` | 0.3 | 幻觉程度 | ❌ |
| Bias | `EVAL_THRESHOLD_BIAS` | 0.3 | 偏见程度 | ❌ |
| Toxicity | `EVAL_THRESHOLD_TOXICITY` | 0.2 | 毒性程度 | ❌ |
| Contextual Relevancy | `EVAL_THRESHOLD_CONTEXTUAL_RELEVANCY` | 0.7 | 上下文相关性 | ✅ |
| Contextual Precision | `EVAL_THRESHOLD_CONTEXTUAL_PRECISION` | 0.7 | 上下文精确度 | ✅ |
| Contextual Recall | `EVAL_THRESHOLD_CONTEXTUAL_RECALL` | 0.7 | 上下文召回率 | ✅ |

### 自定义Agentic指标

这些是针对Agent特性设计的自定义指标：

| 指标 | 环境变量 | 默认值 | 说明 | 越高越好 |
|------|----------|--------|------|---------|
| Tool Accuracy | `EVAL_THRESHOLD_TOOL_ACCURACY` | 0.8 | 工具选择准确性 | ✅ |
| Parameter Correctness | `EVAL_THRESHOLD_PARAMETER_CORRECTNESS` | 0.9 | 参数正确性 | ✅ |
| Response Time | `EVAL_THRESHOLD_RESPONSE_TIME` | 15.0 | 最大响应时间（秒） | ❌ |
| Token Limit | `EVAL_THRESHOLD_TOKEN_LIMIT` | 5000 | Token使用上限 | ❌ |
| Tool Chain Logic | `EVAL_THRESHOLD_TOOL_CHAIN_LOGIC` | 0.85 | 工具链逻辑性 | ✅ |

**注意**:
- ✅ 越高越好：分数需要 **≥** 阈值才通过
- ❌ 越低越好：分数需要 **≤** 阈值才通过

## 🔧 配置方式

### 方式1: 使用默认值（推荐）

**不需要在 `.env` 中配置**，系统会自动使用上表中的默认值。

### 方式2: 自定义阈值

在 `.env` 文件中设置需要调整的阈值：

```bash
# 只配置需要改变的阈值，其他使用默认值

# 提高质量要求
EVAL_THRESHOLD_ANSWER_RELEVANCY=0.8    # 从0.7提高到0.8
EVAL_THRESHOLD_FAITHFULNESS=0.85       # 从0.75提高到0.85

# 降低性能要求（开发环境）
EVAL_THRESHOLD_RESPONSE_TIME=30.0      # 从15秒放宽到30秒

# 更严格的工具准确性
EVAL_THRESHOLD_TOOL_ACCURACY=0.9       # 从0.8提高到0.9
```

## 💡 使用场景

### 场景1: 开发环境（宽松标准）

```bash
# .env 配置
# 降低要求，便于快速迭代
EVAL_THRESHOLD_ANSWER_RELEVANCY=0.6
EVAL_THRESHOLD_FAITHFULNESS=0.65
EVAL_THRESHOLD_RESPONSE_TIME=30.0
EVAL_THRESHOLD_TOKEN_LIMIT=8000
```

**适用于**: 开发阶段，快速迭代，允许更多试错

### 场景2: 测试环境（默认标准）

```bash
# .env 配置
# 使用默认值，无需配置
```

**适用于**: 持续集成、自动化测试、常规质量检查

### 场景3: 生产环境（严格标准）

```bash
# .env 配置
# 提高标准，确保高质量
EVAL_THRESHOLD_ANSWER_RELEVANCY=0.85
EVAL_THRESHOLD_FAITHFULNESS=0.9
EVAL_THRESHOLD_HALLUCINATION=0.2
EVAL_THRESHOLD_TOOL_ACCURACY=0.95
EVAL_THRESHOLD_PARAMETER_CORRECTNESS=0.95
EVAL_THRESHOLD_RESPONSE_TIME=10.0
```

**适用于**: 生产发布前质量检查、重要功能验证

### 场景4: 性能优化（关注性能指标）

```bash
# .env 配置
# 重点优化性能指标
EVAL_THRESHOLD_RESPONSE_TIME=8.0      # 更严格的响应时间
EVAL_THRESHOLD_TOKEN_LIMIT=3000       # 更严格的Token限制
```

**适用于**: 性能优化阶段，成本控制

## 📊 阈值调整建议

### 调高阈值（更严格）的情况

1. **生产发布前** - 确保高质量
2. **发现质量问题** - 提高相关指标要求
3. **成本控制** - 降低Token和响应时间阈值
4. **用户反馈差** - 提高相关性和准确性要求

### 调低阈值（更宽松）的情况

1. **开发初期** - 快速迭代，允许试错
2. **实验性功能** - 探索可能性
3. **测试新模型** - 了解基准性能
4. **调试问题** - 便于定位具体问题

## 🔍 验证配置

### 查看当前阈值

```bash
# 运行配置检查脚本
uv run python scripts/check_config.py
```

输出示例：
```
📊 评估阈值配置:
  标准指标:
    answer_relevancy: 0.7 (默认值)
    faithfulness: 0.75 (默认值)
    ...

  自定义指标:
    tool_accuracy: 0.8 (默认值)
    parameter_correctness: 0.9 (默认值)
    ...
```

### 在代码中使用

```python
from tests.deepeval_config import METRIC_THRESHOLDS, CUSTOM_THRESHOLDS

# 获取特定指标的阈值
relevancy_threshold = METRIC_THRESHOLDS["answer_relevancy"]
tool_threshold = CUSTOM_THRESHOLDS["tool_accuracy"]

# 在评估中使用
from deepeval.metrics import AnswerRelevancyMetric

metric = AnswerRelevancyMetric(
    model="gpt-4o-mini",
    threshold=relevancy_threshold  # 使用配置的阈值
)
```

## 📈 阈值含义详解

### Answer Relevancy (答案相关性)

**含义**: 答案与用户问题的相关程度

**示例**:
- 问题: "如何计算月供？"
- 好答案 (0.9): "月供计算公式是...每月需还款..."
- 差答案 (0.3): "我们提供多种贷款产品..." (离题)

**建议阈值**:
- 开发: 0.6
- 测试: 0.7（默认）
- 生产: 0.8-0.9

### Faithfulness (忠实度)

**含义**: 答案是否忠实于提供的上下文，不编造信息

**示例**:
- 上下文: "最低年利率5%"
- 好答案 (0.95): "年利率最低为5%"
- 差答案 (0.4): "年利率可低至3%" (编造)

**建议阈值**:
- 开发: 0.65
- 测试: 0.75（默认）
- 生产: 0.85-0.95

### Hallucination (幻觉)

**含义**: 答案中编造或不准确信息的程度（越低越好）

**注意**: 这是"越低越好"的指标

**建议阈值**:
- 开发: 0.4
- 测试: 0.3（默认）
- 生产: 0.1-0.2

### Tool Accuracy (工具准确性)

**含义**: Agent选择的工具是否符合用户意图

**示例**:
- 输入: "计算月供"
- 正确工具: `calculate_loan_payment`
- 错误工具: `check_loan_eligibility`

**建议阈值**:
- 开发: 0.7
- 测试: 0.8（默认）
- 生产: 0.9-0.95

### Response Time (响应时间)

**含义**: Agent完整响应所需的时间（秒）

**建议阈值**:
- 开发: 30.0
- 测试: 15.0（默认）
- 生产: 8.0-10.0

## ⚠️ 注意事项

### 1. 阈值不是越高/越低越好

- 过高的阈值可能导致大量误报（false negatives）
- 过低的阈值可能漏掉真实问题（false positives）
- 建议根据实际数据调整

### 2. 不同指标的权重

并非所有指标同等重要：

**高优先级** (关键指标):
- Faithfulness - 防止编造信息
- Tool Accuracy - 确保功能正确
- Parameter Correctness - 保证参数准确

**中优先级**:
- Answer Relevancy - 用户体验
- Response Time - 性能指标

**低优先级** (参考指标):
- Contextual Precision/Recall - 辅助指标

### 3. 环境变量类型

确保使用正确的类型：

```bash
# ✅ 正确 - 浮点数
EVAL_THRESHOLD_ANSWER_RELEVANCY=0.7

# ❌ 错误 - 整数（会被转换为0.0）
EVAL_THRESHOLD_ANSWER_RELEVANCY=1

# ✅ 正确 - 整数（Token限制）
EVAL_THRESHOLD_TOKEN_LIMIT=5000

# ❌ 错误 - 浮点数（Token必须是整数）
EVAL_THRESHOLD_TOKEN_LIMIT=5000.5
```

### 4. 阈值调整流程

1. **基准测试** - 先用默认值运行评估，了解当前性能
2. **分析结果** - 查看哪些指标未通过，通过率如何
3. **调整阈值** - 根据业务需求调整
4. **重新测试** - 验证调整效果
5. **持续优化** - 根据反馈不断调整

## 🚀 快速开始

### 1. 使用默认配置（推荐）

```bash
# 无需配置，直接运行评估
uv run pytest tests/test_mongodb_deepeval_with_storage.py -v
```

### 2. 自定义配置

```bash
# 在 .env 中添加
EVAL_THRESHOLD_ANSWER_RELEVANCY=0.8
EVAL_THRESHOLD_TOOL_ACCURACY=0.9

# 验证配置
uv run python scripts/check_config.py

# 运行评估
uv run pytest tests/test_mongodb_deepeval_with_storage.py -v
```

## 📚 相关文档

- [DeepEval官方文档](https://docs.deepeval.com/)
- [评估系统指南 (EVALUATION_GUIDE.md)](./EVALUATION_GUIDE.md)
- [配置管理 (MODEL_CONFIGURATION.md)](./MODEL_CONFIGURATION.md)
- [环境变量示例 (.env.example)](../.env.example)

## 💡 最佳实践

### 开发阶段
```bash
# 宽松标准，快速迭代
EVAL_THRESHOLD_ANSWER_RELEVANCY=0.6
EVAL_THRESHOLD_FAITHFULNESS=0.65
EVAL_THRESHOLD_RESPONSE_TIME=30.0
```

### CI/CD测试
```bash
# 使用默认值，无需配置
# 或略微放宽性能要求
EVAL_THRESHOLD_RESPONSE_TIME=20.0
```

### 生产发布
```bash
# 严格标准，确保质量
EVAL_THRESHOLD_ANSWER_RELEVANCY=0.85
EVAL_THRESHOLD_FAITHFULNESS=0.9
EVAL_THRESHOLD_TOOL_ACCURACY=0.95
EVAL_THRESHOLD_RESPONSE_TIME=10.0
```

---

**更新日期**: 2025-01-19
**版本**: 1.0
