# 测试文件说明

## 📋 测试文件总览

```
tests/
├── test_loan_calculator_simple.py     # 工具单元测试 - 贷款计算器
├── test_loan_eligibility_simple.py    # 工具单元测试 - 资格检查
├── test_loan_advisor_agent.py         # Agent 评估测试 (DeepEval)
└── README_EVALUATION.md               # Agent 评估详细文档
```

## 🎯 测试分类

### 1. 工具单元测试 (2 个文件)

**文件**:
- `test_loan_calculator_simple.py`
- `test_loan_eligibility_simple.py`

**用途**:
- 快速验证工具函数逻辑
- CI/CD 快速测试
- 不依赖 Agent、LLM 或 MongoDB

**运行**:
```bash
pytest tests/test_loan_calculator_simple.py -v
pytest tests/test_loan_eligibility_simple.py -v
```

---

### 2. Agent 评估测试 (1 个文件)

**文件**: `test_loan_advisor_agent.py`

**特点**:
- ✅ 使用 DeepEval 标准（Golden, Dataset, Metrics）
- ✅ 测试对象: `src/agent/loan_advisor_agent.py`
- ✅ 数据来源: MongoDB `agno_sessions` 真实对话
- ✅ 符合 SOLID 原则
- ✅ 简洁，一个文件完成所有评估

**运行**:
```bash
# 详细说明见 README_EVALUATION.md
pytest tests/test_loan_advisor_agent.py -v
```

**评估指标**:
- AnswerRelevancyMetric (回答相关性)
- FaithfulnessMetric (事实准确性)

---

## 🚀 快速开始

### 日常开发
```bash
# 验证工具逻辑
pytest tests/test_loan_*_simple.py -v
```

### Agent 评估
```bash
# 1. 先运行 Agent 产生对话数据
uv run python src/agent/loan_advisor_agent.py

# 2. 运行评估
pytest tests/test_loan_advisor_agent.py -v
```

---

## 📊 对比表

| 测试类型 | 文件 | 数据来源 | 依赖 | 用途 |
|---------|------|---------|------|------|
| 工具单元测试 | `test_loan_*_simple.py` | 硬编码 | pytest | CI/CD |
| Agent 评估 | `test_loan_advisor_agent.py` | MongoDB | DeepEval + pytest | 质量评估 |

---

## 📚 更多信息

- Agent 评估详细文档: [README_EVALUATION.md](./README_EVALUATION.md)
- DeepEval 官方文档: https://deepeval.com/docs/evaluation-introduction
