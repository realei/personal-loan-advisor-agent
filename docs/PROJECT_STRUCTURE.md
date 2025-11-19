# 项目结构说明

## 📁 目录结构

```
personal-loan-advisor-agent/
├── src/                        # 源代码
│   ├── agent/                  # Agent层 - Agno框架集成
│   ├── tools/                  # 业务逻辑层 - 纯Python类
│   ├── api/                    # API层 - FastAPI REST服务
│   └── utils/                  # 工具层 - 配置、日志等
├── evaluation/                 # ⭐ 评估系统 (核心亮点)
├── tests/                      # 测试
├── scripts/                    # 脚本工具
├── docs/                       # 文档
└── 配置文件                    # pyproject.toml, pytest.ini等
```

## 🏗️ 架构分层

### 第一层：业务逻辑层 (`src/tools/`)

**作用**: 纯业务逻辑，与框架无关

```
src/tools/
├── __init__.py
├── loan_eligibility.py         # 贷款资格检查
└── loan_calculator.py          # 贷款计算工具
```

**设计原则**:
- ✅ 框架无关 - 不依赖Agno或任何AI框架
- ✅ 易于测试 - 纯Python类，单元测试简单
- ✅ 可复用 - 可以在其他项目中使用
- ✅ 类型安全 - 使用Pydantic进行数据验证

**示例**:
```python
from src.tools.loan_calculator import LoanCalculatorTool

calculator = LoanCalculatorTool(max_dti_ratio=0.43)
result = calculator.calculate_monthly_payment(
    loan_amount=50000,
    annual_interest_rate=0.05,
    loan_term_months=36
)
```

### 第二层：Agent层 (`src/agent/`)

**作用**: Agno框架集成，工具编排

```
src/agent/
├── __init__.py
├── loan_advisor_agent.py       # 主Agent定义
└── loan_advisor_tools.py       # 工具包装器 (Agno @tool装饰器)
```

**设计原则**:
- ✅ 框架适配 - 将业务逻辑包装为Agno工具
- ✅ 自然语言理解 - LLM处理用户意图
- ✅ 工具编排 - Agent自动选择和调用工具
- ✅ 会话管理 - 集成MongoDB存储

**示例**:
```python
from src.agent.loan_advisor_agent import loan_advisor_agent

# Agent自动选择工具并执行
loan_advisor_agent.chat("Calculate payment for $50,000 at 5% for 36 months")
```

### 第三层：API层 (`src/api/`)

**作用**: REST API服务

```
src/api/
├── __init__.py
└── chat_router.py              # FastAPI路由
```

**设计原则**:
- ✅ RESTful设计 - 标准HTTP接口
- ✅ 会话管理 - MongoDB持久化
- ✅ 错误处理 - 统一错误响应
- ✅ 异步支持 - FastAPI async/await

### 工具层 (`src/utils/`)

**作用**: 通用工具和配置

```
src/utils/
├── __init__.py
├── config.py                   # 配置管理 (Pydantic Settings)
├── logger.py                   # 日志配置
└── memory.py                   # 记忆管理
```

## ⭐ 评估系统 (`evaluation/`)

**这是项目的最大亮点！**

```
evaluation/
├── __init__.py
├── evaluation_framework.py     # SOLID架构评估框架
├── context_reconstructor.py    # Context重构 (创新)
└── mongodb_storage.py          # 结果持久化
```

**核心功能**:
1. **多维度评估**: DeepEval标准指标 + 自定义agentic指标
2. **Context重构**: 从工具调用重新执行获取retrieval context
3. **MongoDB集成**: 使用真实对话数据作为测试用例
4. **结果持久化**: 自动存储评估结果，支持趋势分析
5. **多种使用方式**: pytest / CLI / Python API

**架构设计**:
```python
# SOLID原则应用
class DataExtractor(ABC):           # 抽象接口
    def extract_runs(self) -> List[AgentRun]: ...

class MongoDataExtractor(DataExtractor):  # 具体实现
    # 从MongoDB提取数据

class Evaluator(ABC):                # 抽象接口
    def evaluate(self, run) -> Result: ...

class DeepEvalRelevancyEvaluator(Evaluator):  # 具体实现
class ToolAccuracyEvaluator(Evaluator):       # 自定义指标
```

## 🧪 测试 (`tests/`)

```
tests/
├── __init__.py
├── deepeval_config.py                          # ⭐ 评估配置 (阈值、规则)
├── test_mongodb_deepeval.py                    # ⭐ DeepEval集成测试
├── test_mongodb_deepeval_with_storage.py       # ⭐ 带存储的测试
├── test_agent_evaluation.py                    # Agent评估测试
└── ... (其他单元测试)
```

**测试类型**:
- **单元测试**: 业务逻辑层 (tools/)
- **集成测试**: Agent + MongoDB
- **评估测试**: DeepEval指标
- **性能基准**: 响应时间、Token使用

## 📜 脚本工具 (`scripts/`)

```
scripts/
├── run_evaluation.py           # ⭐ 快速评估脚本 (无需pytest)
├── analyze_agent_behavior.py   # 行为分析
├── view_evaluations.py         # 查看评估结果
└── download_data.py            # 数据下载
```

**使用示例**:
```bash
# 快速评估
uv run python scripts/run_evaluation.py --mode recent --hours 24 --limit 5 --with-tools

# 查看结果
uv run python scripts/view_evaluations.py --days 7
```

## 📚 文档 (`docs/`)

```
docs/
├── EVALUATION_GUIDE.md         # ⭐ 完整评估系统指南
├── CONTEXT_RECONSTRUCTION.md   # ⭐ Context重构技术说明
├── PROJECT_STRUCTURE.md        # 本文件
├── SETUP_MONGODB.md            # MongoDB设置
└── TEST_SUMMARY.md             # 测试总结
```

## 📋 配置文件

### `pyproject.toml`
项目配置和依赖管理 (uv)

### `pytest.ini`
Pytest配置，包括：
- markers定义 (benchmark, integration, unit)
- testpaths配置
- 输出选项

### `.env` / `.env.example`
环境变量:
```bash
OPENAI_API_KEY=sk-...
MONGODB_URI=mongodb://localhost:27017
AGNO_ENV=development
```

## 🔍 依赖关系图

```
┌─────────────────────────────────────────┐
│           Application Entry             │
│  src/agent/loan_advisor_agent.py        │
└──────────────┬──────────────────────────┘
               │
               │ imports
               ▼
┌──────────────────────────────────────────┐
│         Agent Tools Layer               │
│  src/agent/loan_advisor_tools.py        │
└──────────────┬──────────────────────────┘
               │
               │ imports
               ▼
┌──────────────────────────────────────────┐
│       Business Logic Layer              │
│  src/tools/loan_eligibility.py          │
│  src/tools/loan_calculator.py           │
└──────────────────────────────────────────┘

               │
               │ used by
               ▼
┌──────────────────────────────────────────┐
│        Evaluation System                │
│  evaluation/context_reconstructor.py    │
│  (re-executes tools for context)        │
└──────────────────────────────────────────┘
```

## 💡 设计模式和原则

### 1. 分层架构 (Layered Architecture)
- **表现层**: API (FastAPI)
- **业务层**: Agent (Agno)
- **数据访问层**: Tools (纯业务逻辑)

### 2. 依赖倒置原则 (Dependency Inversion)
```python
# ✅ 好的设计
src/tools/                  # 核心业务逻辑
    ↑
    │ 依赖
    │
src/agent/                  # 框架适配层
```

### 3. 单一职责原则 (Single Responsibility)
- `loan_calculator.py` - 只负责贷款计算
- `loan_eligibility.py` - 只负责资格检查
- `context_reconstructor.py` - 只负责context重构

### 4. 开放封闭原则 (Open/Closed)
评估系统易于扩展新指标，无需修改现有代码：
```python
# 添加新指标
class NewCustomMetric(Evaluator):
    def evaluate(self, run) -> Result:
        # 实现新指标逻辑
        ...
```

## 📊 代码统计

| 类别 | 文件数 | 行数 (估算) | 说明 |
|------|--------|-------------|------|
| 业务逻辑 | 2 | ~500 | tools/ |
| Agent层 | 2 | ~200 | agent/ |
| 评估系统 | 3 | ~800 | evaluation/ ⭐ |
| 测试 | 5+ | ~1500 | tests/ ⭐ |
| 文档 | 5 | ~2000 | docs/ ⭐ |
| 总计 | 20+ | ~5000 | - |

## 🎯 面试要点

### Q: "为什么要这样组织项目结构？"
**A**: 我采用了分层架构设计，主要考虑：
1. **关注点分离** - 每一层都有明确的职责
2. **依赖倒置** - 核心业务不依赖框架
3. **易于测试** - 每一层都可以独立测试
4. **可扩展性** - 可以轻松添加新功能

### Q: "src/tools层的作用是什么？"
**A**: tools层包含纯业务逻辑，与框架无关。这样设计的好处是：
- 易于单元测试 (不需要mock框架)
- 可以在其他项目中复用
- 更换框架时不需要重写业务逻辑
- 符合依赖倒置原则

### Q: "评估系统是如何工作的？"
**A**: 评估系统是我这个项目的核心亮点：
1. 从MongoDB提取真实对话作为测试用例
2. 使用DeepEval + 自定义指标进行多维度评估
3. 创新性地实现了context重构功能
4. 结果自动持久化到MongoDB
5. 支持历史趋势分析

特别要提的是context重构 - 我通过重新执行工具调用来获取retrieval context，解决了Faithfulness指标评估的问题。

### Q: "如果要添加新功能，你会怎么做？"
**A**: 取决于功能类型：
- **新的贷款工具**: 在tools/添加新类，在agent/loan_advisor_tools.py包装
- **新的评估指标**: 继承Evaluator抽象类，实现evaluate方法
- **新的API端点**: 在api/添加新路由
- **性能优化**: 先运行基准测试，再优化，最后验证

## 🔗 相关文档

- [README.md](../README.md) - 项目概述
- [EVALUATION_GUIDE.md](./EVALUATION_GUIDE.md) - 评估系统完整指南
- [CONTEXT_RECONSTRUCTION.md](./CONTEXT_RECONSTRUCTION.md) - Context重构技术细节
