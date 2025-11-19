# 🏦 Personal Loan Advisor Agent

Production-ready AI Loan Advisory System with **Complete Evaluation Framework**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Agno 2.0](https://img.shields.io/badge/Agno-2.0-green.svg)](https://docs.agno.com)
[![DeepEval](https://img.shields.io/badge/DeepEval-Latest-purple.svg)](https://docs.confident-ai.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-green.svg)](https://www.mongodb.com/)

---

## 🌟 Highlights (Interview Highlights)

### ⭐ Complete Agent Evaluation System
This is the **biggest highlight** of the project - implemented a complete production-grade evaluation framework:

- 📊 **DeepEval Integration** - Multi-dimensional quality assessment (Relevancy, Faithfulness, Hallucination)
- 🔧 **Context Reconstruction** - Innovative approach to reconstruct context from tool call re-execution, solving the context requirement for Hallucination metric
- 📈 **Tool Call Validation** - Automatic extraction and validation of agent's tool calls and parameters
- 🎯 **Keyword Validation** - Ensures output contains expected key information
- 📝 **Complete Test Suite** - 42+ unit tests and integration tests

### ⭐ SOLID Architecture Design
- 🏗️ **Clear Layering** - tools (business logic) / agent (framework integration)
- 🔌 **Dependency Inversion** - Core business logic doesn't depend on specific frameworks
- 🧪 **Easy to Test** - Unit tests and integration tests completely separated
- 📦 **Modularized** - Configuration management and logging system as independent modules

---

## 📋 Overview

An intelligent loan advisory agent for consumer banking with **production-level quality assurance**. The agent not only helps customers with loan decisions but includes a comprehensive evaluation framework to ensure high-quality responses.

### ✨ Core Features

#### 💼 Loan Advisory (Core Functionality)
- ✅ **Loan Eligibility Assessment** - Rule-based checks (age, income, credit score, DTI)
- 💰 **Payment Calculations** - Accurate EMI using standard financial formulas
- 📊 **Amortization Schedules** - Detailed month-by-month breakdowns
- 📈 **Affordability Analysis** - DTI ratio assessment
- 🔄 **Loan Comparison** - Compare different terms side-by-side
- 🎯 **Max Loan Calculator** - Find maximum affordable amount

#### 🔬 Evaluation System (Evaluation Framework)
- 📊 **Multi-metric Evaluation** - DeepEval metrics (Relevancy, Faithfulness, Hallucination)
- 🔧 **Context Reconstruction** - Automatic context reconstruction from tool calls
- ✅ **Tool Call Validation** - Validate tool selection and parameter correctness
- 📝 **Output Validation** - Keyword matching validation
- ⚡ **Multiple Test Modes** - Unit tests, integration tests, DeepEval evaluation

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Personal Loan Advisor System               │
└───────────────┬─────────────────────────────────────────┘
                │
    ┌───────────┴───────────┐
    │                       │
┌───▼────┐            ┌─────▼──────┐
│ Tools  │            │   Agent    │
│ Layer  │            │   Layer    │
│        │            │            │
│Business│◀──────────│ AgentOS    │
│ Logic  │            │ 2.0 + GPT4 │
└────────┘            │ + MongoDB  │
                      └─────┬──────┘
                            │
                      ┌─────▼──────┐
                      │  Testing   │
                      │  DeepEval  │
                      └────────────┘
```

### Testing & Evaluation Architecture (Test and Evaluation Architecture)

```
Test Cases (2 categories)
    ├─── Unit Tests (42 tests)
    │    ├─ Loan Calculator (16 tests)
    │    └─ Loan Eligibility (26 tests)
    │
    └─── DeepEval Integration Tests (4 tests)
         ├─ Context Reconstruction
         │  └─ Re-execute tools to get retrieval_context
         ├─ DeepEval Metrics
         │  ├─ Answer Relevancy
         │  ├─ Faithfulness
         │  └─ Hallucination
         ├─ Tool Call Validation
         │  ├─ Tool selection verification
         │  └─ Parameter extraction
         └─ Output Validation
            └─ Keyword matching
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MongoDB (optional, for AgentOS UI and session persistence)
- OpenAI API Key
- [uv](https://github.com/astral-sh/uv) (recommended)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd personal-loan-advisor-agent

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Running the Agent

```bash
# Interactive mode
uv run python src/agent/loan_advisor_agent.py
```

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run unit tests only
uv run pytest tests/test_loan_calculator_simple.py tests/test_loan_eligibility_simple.py -v

# Run DeepEval integration tests
uv run pytest tests/test_loan_advisor_agent.py -v

# Run specific DeepEval test
uv run pytest tests/test_loan_advisor_agent.py::test_agent_with_reference_free_metrics -v
```

---

## 💡 Usage Examples

### Agent Usage

```python
# Example 1: Eligibility Check
You: I'm 35 years old, earn $8000/month, have a credit score of 720,
     work full-time for 5 years, and want to borrow $50,000 for 36 months.
     Am I eligible?

Agent: ## Loan Eligibility Assessment
       **Status**: ELIGIBLE ✅
       **Eligibility Score**: 85.2/100

       ### Assessment Details:
       - Age requirement: Met (35 years)
       - Income requirement: Met ($8,000/month)
       - Credit score: Good (720)
       - Employment: Stable (5 years)
       - DTI Ratio: 37.4% (within limit)

# Example 2: Payment Calculation
You: Calculate payment for $60,000 at 5.5% for 48 months

Agent: ## Loan Payment Calculation
       **Monthly Payment**: $1,388.31
       **Total Payment**: $66,639.08
       **Total Interest**: $6,639.08
       **Interest as % of Principal**: 11.1%
```

---

## 🧪 Testing & Evaluation

### Test Coverage

- ✅ **42 unit tests** for business logic
  - 16 tests for Loan Calculator
  - 26 tests for Loan Eligibility
- ✅ **4 DeepEval integration tests** for Agent quality
  - Reference-free metrics evaluation
  - Tool call validation
  - Output keyword validation
  - Individual case testing

### Evaluation Metrics

#### DeepEval Metrics
| Metric | Description | Threshold |
|--------|-------------|-----------|
| Answer Relevancy | How relevant is the answer to the question | ≥ 70% |
| Faithfulness | Answer is based on facts from context | ≥ 70% |
| Hallucination | Answer contradicts the context | ≤ 50% (lower is better) |

#### Tool Call Validation
| Metric | Description |
|--------|-------------|
| Tool Selection | Verifies correct tool is called for each scenario |
| Parameter Extraction | Validates all required parameters are extracted correctly |
| Output Keywords | Ensures critical information appears in agent response |

### Running Tests

```bash
# Run all tests (42 unit + 4 integration)
uv run pytest tests/ -v

# Run only unit tests (fast)
uv run pytest tests/test_loan_calculator_simple.py tests/test_loan_eligibility_simple.py -v

# Run only DeepEval tests (slower, requires OpenAI API)
uv run pytest tests/test_loan_advisor_agent.py -v
```

---

## 📁 Project Structure

```
personal-loan-advisor-agent/
├── src/
│   ├── agent/                      # Agent Layer
│   │   ├── loan_advisor_agent.py   # Main Agent (AgentOS integration)
│   │   └── loan_advisor_tools.py   # Tool wrappers for AgentOS
│   ├── tools/                      # Business Logic Layer
│   │   ├── loan_eligibility.py     # Eligibility checking logic
│   │   └── loan_calculator.py      # Loan calculation logic
│   └── utils/                      # Utilities
│       ├── config.py               # Configuration management
│       └── logger.py               # Logging system
├── tests/                          # ⭐ Testing & Evaluation
│   ├── test_loan_calculator_simple.py      # 16 unit tests for calculator
│   ├── test_loan_eligibility_simple.py     # 26 unit tests for eligibility
│   ├── test_loan_advisor_agent.py          # 4 DeepEval integration tests
│   ├── deepeval_config.py                  # DeepEval configuration
│   ├── README.md                           # Testing documentation
│   └── README_EVALUATION.md                # Evaluation guide
├── examples/                       # Usage examples
│   └── config_usage_demo.py        # Configuration usage demo
├── scripts/                        # Utility scripts
│   └── check_config.py             # Configuration checker
├── docs/                           # Documentation
│   ├── EVALUATION_GUIDE.md         # Evaluation system guide
│   ├── EVALUATION_THRESHOLDS.md    # Metric thresholds
│   ├── SETUP_MONGODB.md            # MongoDB setup guide
│   └── TEST_SUMMARY.md             # Test summary
├── pytest.ini                      # Pytest configuration
├── pyproject.toml                  # Project dependencies
├── .env.example                    # Environment variables template
└── README.md                       # This file
```

---

## 🎯 Framework & Design Choices

### 1. Why AgentOS 2.0?

- **Modern & Production-Ready** - Built specifically for production AI agents
- **Native Tool Calling** - Seamless OpenAI function calling integration
- **MongoDB Integration** - Built-in session and conversation persistence
- **Type Safety** - Strong Pydantic integration throughout

### 2. Two-Layer Architecture

**Clean separation of concerns:**

1. **Tools Layer** (`src/tools/`)
   - Pure business logic, framework-agnostic
   - Can be reused in any framework (LangChain, LlamaIndex, etc.)
   - Easy to unit test independently
   - Follows Dependency Inversion Principle

2. **Agent Layer** (`src/agent/`)
   - AgentOS framework integration
   - Tool orchestration and calling
   - Natural language understanding via GPT-4

### 3. Testing & Evaluation Design

**SOLID principles applied:**

- **Single Responsibility** - Each test file has one clear purpose
- **Context Reconstruction** - Re-execute tools to get accurate retrieval context for DeepEval
- **Separation of Concerns** - Unit tests separate from integration tests

**Key innovations:**
- **Context Reconstruction from Tool Calls** - Solves the context parameter problem for Hallucination metric
- **Automatic Tool Call Extraction** - Parses agent messages to verify correct tool selection
- **Multiple Test Layers** - Unit tests for business logic + DeepEval for agent quality

---

## 💼 For Interview: Key Talking Points

### 1. Context Reconstruction Innovation (Biggest Technical Highlight)

> **"I solved a critical challenge with DeepEval's Hallucination metric: it requires a `context` parameter, not just `retrieval_context`. To provide accurate context, I implemented an automatic context reconstruction system that re-executes the agent's tool calls with the exact parameters it used. This ensures the evaluation metrics have the precise information that was available to the agent when generating its response."**

**Technical Details:**
- Extract tool calls and parameters from agent responses
- Re-execute tools with same parameters to reconstruct context
- Provide both `context` and `retrieval_context` to LLMTestCase
- Handles all 6 loan advisor tools correctly
- Enables accurate Hallucination and Faithfulness evaluation

### 2. Comprehensive Testing Strategy (Testing Strategy)

> **"I implemented a multi-layer testing approach: 42 unit tests for pure business logic (loan calculations, eligibility rules), and 4 DeepEval integration tests that evaluate the agent's quality across Answer Relevancy, Faithfulness, and Hallucination metrics. The unit tests run fast (<1s) for rapid development, while DeepEval tests provide deep quality insights."**

**Testing Layers:**
- Unit tests: Pure business logic, framework-agnostic
- DeepEval tests: Agent quality with LLM-as-judge
- Tool call validation: Verify correct tool selection
- Output validation: Keyword matching for critical info

### 3. Clean Architecture (Architecture Design)

> **"I used a two-layer architecture following the Dependency Inversion Principle. The tools layer contains pure business logic that's completely framework-agnostic - you could drop these tools into LangChain or LlamaIndex without any changes. The agent layer handles AgentOS integration and orchestration. This makes the code highly testable and maintainable."**

**Benefits:**
- Business logic can be reused across frameworks
- Easy to unit test independently
- Clear separation of concerns
- Production-ready structure

### 4. Production Readiness (Production-Ready Code)

> **"This isn't just a demo - it's production-ready code. Every function has type hints, input validation with Pydantic, comprehensive error handling, structured logging, and environment-based configuration. The test coverage ensures reliability, and the DeepEval integration could easily be added to a CI/CD pipeline for continuous quality monitoring."**

**Production Features:**
- ✅ Type safety (100% type hints)
- ✅ Input validation (Pydantic models)
- ✅ Error handling & logging
- ✅ Environment-based config
- ✅ 46 automated tests
- ✅ CI/CD ready

---

## 🔮 Future Enhancements

### Testing & Evaluation
- [ ] Add more test cases covering edge scenarios
- [ ] Implement performance benchmarks (response time, token usage)
- [ ] Add bias detection metrics
- [ ] Dashboard for test results visualization

### Agent Features
- [ ] Integrate credit scoring model (XGBoost)
- [ ] Add RAG for bank policy documents
- [ ] Multi-language support
- [ ] Integration with real banking APIs

---

## 📚 Documentation

- **Testing Guides**:
  - [tests/README.md](tests/README.md) - Complete testing documentation
  - [tests/README_EVALUATION.md](tests/README_EVALUATION.md) - DeepEval evaluation guide
  - [tests/README_TESTS.md](tests/README_TESTS.md) - Test implementation notes

- **Setup Guides**:
  - [docs/EVALUATION_GUIDE.md](docs/EVALUATION_GUIDE.md) - Evaluation system guide
  - [docs/SETUP_MONGODB.md](docs/SETUP_MONGODB.md) - MongoDB configuration
  - [docs/TEST_SUMMARY.md](docs/TEST_SUMMARY.md) - Test summary

---

## 📄 License

MIT License

---

## 🤝 Contributing

This is a portfolio project demonstrating production-ready AI agent development with comprehensive testing. For production use, contributions would follow:
- Unit tests required for all business logic
- DeepEval integration tests for agent changes
- Type hints and input validation
- Code review process
- Documentation updates

---

## 🎓 What Makes This Project Stand Out

1. **Context Reconstruction Innovation** - Solved the DeepEval Hallucination metric context problem by re-executing tool calls
2. **Multi-Layer Testing** - 42 unit tests + 4 DeepEval integration tests
3. **Framework-Agnostic Design** - Business logic independent of AI framework
4. **Production-Ready Code** - Type hints, validation, error handling, logging throughout
5. **Clear Documentation** - Comprehensive guides for setup, testing, and evaluation

---

**Built with ❤️ using AgentOS 2.0, OpenAI GPT-4, DeepEval, MongoDB, and modern Python practices**

*Demonstrating production-level AI agent development with comprehensive testing and evaluation*
