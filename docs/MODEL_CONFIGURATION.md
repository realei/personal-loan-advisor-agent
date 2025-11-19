# 模型配置指南

## 📋 概述

项目支持分别配置两个模型：
- **Agent模型**: 用于实际对话和工具调用
- **DeepEval模型**: 用于评估Agent输出质量

这种分离设计允许您灵活选择成本和性能的平衡。

## 🔧 配置方式

### 方式1: 环境变量（推荐）

在项目根目录的 `.env` 文件中配置：

```bash
# Agent使用的模型（用于对话和工具调用）
AGENT_MODEL=gpt-4o-mini

# DeepEval评估使用的模型（用于质量评估）
DEEPEVAL_MODEL=gpt-4o-mini

# OpenAI API密钥
OPENAI_API_KEY=sk-your-api-key-here
```

### 方式2: 使用默认值

如果 `.env` 中没有配置，两个模型都默认使用 `gpt-4o-mini`。

## 💡 使用场景

### 场景1: 成本优化（推荐）

```bash
# Agent使用便宜的模型处理日常对话
AGENT_MODEL=gpt-4o-mini

# DeepEval也使用便宜的模型进行评估
DEEPEVAL_MODEL=gpt-4o-mini
```

**成本**: 最低
**适用**: 开发、测试、演示

### 场景2: 性能优先

```bash
# Agent使用高性能模型提供最佳用户体验
AGENT_MODEL=gpt-4o

# DeepEval使用便宜模型节省评估成本
DEEPEVAL_MODEL=gpt-4o-mini
```

**成本**: 中等
**适用**: 生产环境、面试演示

### 场景3: 全面评估

```bash
# Agent使用高性能模型
AGENT_MODEL=gpt-4o

# DeepEval也使用高性能模型确保评估准确性
DEEPEVAL_MODEL=gpt-4o
```

**成本**: 最高
**适用**: 质量审计、严格评估

## 📊 支持的模型

### OpenAI模型

| 模型 | 速度 | 成本 | 推荐用途 |
|------|------|------|----------|
| `gpt-4o-mini` | ⚡⚡⚡ | 💰 | 开发/测试 ✅ |
| `gpt-4o` | ⚡⚡ | 💰💰💰 | 生产环境 |
| `gpt-4-turbo` | ⚡⚡ | 💰💰💰 | 高质量需求 |

## 🧪 验证配置

运行配置检查脚本：

```bash
uv run python scripts/check_config.py
```

输出示例：
```
============================================================
配置检查
============================================================

📋 环境变量:
  OPENAI_API_KEY: ✅ 已设置
  AGENT_MODEL: gpt-4o-mini
  DEEPEVAL_MODEL: gpt-4o-mini

🔧 Config对象 (src/utils/config.py):
  agent_model: gpt-4o-mini
  deepeval_model: gpt-4o-mini
  temperature: 0.7

✅ 验证:
  Agent模型一致性: ✅ 一致
  DeepEval模型一致性: ✅ 一致

============================================================
✅ 配置检查通过！
```

## 📝 代码使用

### 在Agent中使用

```python
from src.utils.config import config

# Agent会自动使用配置的模型
agent = Agent(
    name="Personal Loan Advisor",
    model=OpenAIChat(
        id=config.api.agent_model,  # 使用AGENT_MODEL配置
        temperature=config.api.temperature
    ),
)
```

### 在DeepEval中使用

```python
from tests.deepeval_config import EVAL_MODEL

# DeepEval评估器使用配置的模型
from deepeval.metrics import AnswerRelevancyMetric

relevancy_metric = AnswerRelevancyMetric(
    model=EVAL_MODEL,  # 使用DEEPEVAL_MODEL配置
    threshold=0.7
)
```

## 🎯 最佳实践

### 开发阶段
```bash
AGENT_MODEL=gpt-4o-mini
DEEPEVAL_MODEL=gpt-4o-mini
```
- 成本低
- 迭代快
- 适合频繁测试

### 面试演示
```bash
AGENT_MODEL=gpt-4o-mini
DEEPEVAL_MODEL=gpt-4o-mini
```
- 性能足够好
- 成本可控
- 展示完整功能

### 生产环境
```bash
AGENT_MODEL=gpt-4o
DEEPEVAL_MODEL=gpt-4o-mini
```
- 用户体验最佳
- 评估成本可控
- 平衡性能和成本

## ⚠️ 注意事项

1. **API密钥**: 确保 `OPENAI_API_KEY` 已正确设置
2. **配额限制**: 注意OpenAI的API配额和速率限制
3. **成本控制**: 使用 `gpt-4o-mini` 可大幅降低成本
4. **模型兼容性**: 所有配置的模型必须支持function calling

## 🔍 故障排查

### 问题: Agent使用了错误的模型

**检查**:
```bash
# 1. 查看环境变量
echo $AGENT_MODEL

# 2. 运行配置检查
uv run python scripts/check_config.py

# 3. 查看.env文件
cat .env | grep AGENT_MODEL
```

**解决**:
```bash
# 在.env中添加或修改
AGENT_MODEL=gpt-4o-mini
```

### 问题: DeepEval评估失败

**检查**:
```bash
# 查看DeepEval模型配置
echo $DEEPEVAL_MODEL

# 运行配置检查
uv run python scripts/check_config.py
```

**解决**:
```bash
# 确保模型支持function calling
DEEPEVAL_MODEL=gpt-4o-mini
```

## 📚 相关文档

- [配置管理 (src/utils/config.py)](../src/utils/config.py)
- [DeepEval配置 (tests/deepeval_config.py)](../tests/deepeval_config.py)
- [MongoDB配置指南 (docs/MONGODB_CONFIG.md)](./MONGODB_CONFIG.md)
- [环境变量示例 (.env.example)](../.env.example)

---

**更新日期**: 2025-01-19
**版本**: 1.0
