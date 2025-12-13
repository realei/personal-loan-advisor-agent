# 🏦 Personal Loan Advisor Agent

Production-ready AI Loan Advisory System with **Complete Evaluation Framework**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Agno 2.0](https://img.shields.io/badge/Agno-2.0-green.svg)](https://docs.agno.com)
[![DeepEval](https://img.shields.io/badge/DeepEval-Latest-purple.svg)](https://docs.confident-ai.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-green.svg)](https://www.mongodb.com/)

An AI-powered loan advisory system built with **AgentOS 2.0** and **GPT-4**, designed to help customers make informed personal loan decisions. This production-ready system combines intelligent loan advisory capabilities with a comprehensive evaluation framework using **DeepEval** for quality assurance.

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Usage](#-usage)
  - [Interactive Mode](#1️⃣-interactive-mode-cli-chat)
  - [API Mode](#2️⃣-api-mode-rest-api-server)
- [Testing](#-testing)
  - [Unit Tests](#1️⃣-unit-tests)
  - [DeepEval Evaluation](#2️⃣-deepeval-evaluation)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Development](#-development)

---

## ✨ Features

### 💼 Loan Advisory Capabilities

This agent provides **11 loan advisory tools**:

**Personal Loan Tools:**
1. **Check Loan Eligibility** - Evaluate customer profiles against banking criteria (age, income, credit score, employment, DTI ratio)
2. **Calculate Loan Payment** - Compute accurate monthly payments, total costs, and interest
3. **Generate Payment Schedule** - Create detailed month-by-month amortization breakdowns
4. **Check Affordability** - Analyze debt-to-income ratios
5. **Compare Loan Terms** - Side-by-side comparison of different loan options
6. **Calculate Max Loan Amount** - Find the maximum affordable loan

**Mortgage Tools (NEW):**
7. **Calculate Home Affordability** - Determine max home price based on income and UAE residency rules
8. **Calculate Mortgage Payment** - Compute mortgage payments with dynamic LTV based on residency status

**Auto Loan Tools (NEW):**
9. **Calculate Car Loan** - Calculate auto loan payments with vehicle-type-specific LTV rules
10. **Compare Car Loan Terms** - Compare different term lengths (36/48/60/72 months)

**Cross-Loan Tools (NEW):**
11. **Calculate Early Payoff** - Analyze interest savings from extra monthly payments

### 📤 Structured Output Mode (NEW)

Configurable output formatting with SOLID design principles:

| Mode | Description | Use Case |
|------|-------------|----------|
| `markdown` | Human-readable, streaming-friendly | CLI, demos, interactive use |
| `structured` | Pydantic-validated JSON responses | API integration, programmatic access |

**Design Patterns:**
- **Strategy Pattern**: MarkdownFormatter vs StructuredFormatter
- **Factory Pattern**: `get_formatter()` creates appropriate instance
- **Protocol**: OutputFormatter defines the contract
- **Single Config**: `OUTPUT_MODE=markdown|structured`

### 📋 Rule-Based LTV Engine

Dynamic Loan-to-Value (LTV) calculation based on **UAE Central Bank regulations**:

| Residency | Property | Max LTV | Min Down Payment |
|-----------|----------|---------|------------------|
| UAE Citizen | First (≤5M) | 85% | 15% |
| UAE Citizen | First (>5M) | 80% | 20% |
| Expat | First | 80% | 20% |
| Expat | Second | 65% | 35% |
| Non-Resident | Any | 50% | 50% |

### 🔬 Evaluation Framework

- **231 Automated Tests** (134 unit + 48 response models + 49 formatter tests)
- **DeepEval Metrics** - Answer Relevancy ≥70%, Faithfulness ≥70%, Hallucination ≤50%
- **Context Reconstruction** - Innovative approach to reconstruct context from tool call re-execution
- **Tool Call Validation** - Automatic validation of tool selection and parameters

### 🚀 Deployment Modes

- **Interactive CLI** - Real-time chat interface for development and demos
- **REST API** - FastAPI server for production integration

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MongoDB (optional, for session persistence)
- OpenAI API Key
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd personal-loan-advisor-agent

# 2. Install dependencies using uv
uv sync

# 3. Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY (required)

# 4. (Optional) Start MongoDB for session persistence
# See Configuration section below for MongoDB setup
```

### Quick Test

```bash
# Run unit tests to verify installation
uv run pytest tests/test_loan_calculator_simple.py tests/test_loan_eligibility_simple.py -v
```

---

## ⚙️ Configuration

### Environment Variables (.env file)

Create a `.env` file from the template:

```bash
cp .env.example .env
```

#### Required Configuration

```bash
# OpenAI API Key (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here
```

#### Optional Configuration

**Model Settings:**
```bash
# Model for agent conversations (default: gpt-4o-mini)
AGENT_MODEL=gpt-4o-mini

# Model for DeepEval evaluation (default: gpt-4o-mini)
DEEPEVAL_MODEL=gpt-4o-mini

# LLM Temperature (default: 0.7)
TEMPERATURE=0.7
```

**Output Mode Settings:**
```bash
# Output format: markdown (default) or structured
# markdown: Human-readable streaming output for CLI/demos
# structured: Pydantic-validated JSON for API integration
OUTPUT_MODE=markdown
```

**MongoDB Settings (Optional - for session persistence):**
```bash
# MongoDB connection URI
MONGODB_URI=mongodb://admin:password@localhost:27017/

# Database and collection names
MONGODB_DATABASE=loan_advisor
MONGODB_SESSION_COLLECTION=agno_sessions
MONGODB_MEMORY_COLLECTION=agno_memories
MONGODB_METRICS_COLLECTION=agno_metrics
```

**Loan Configuration (Optional - uses defaults if not set):**
```bash
MIN_AGE=18
MAX_AGE=65
MIN_INCOME_AED=5000
MIN_CREDIT_SCORE=600
MAX_DTI_RATIO=0.5
MAX_LOAN_AMOUNT_AED=1000000
```

**DeepEval Thresholds (Optional):**
```bash
EVAL_THRESHOLD_ANSWER_RELEVANCY=0.7
EVAL_THRESHOLD_FAITHFULNESS=0.75
EVAL_THRESHOLD_HALLUCINATION=0.3
```

### MongoDB Setup (Optional)

MongoDB is **optional**. The agent works without it, but you'll lose session persistence and conversation history.

#### Option 1: Docker (Recommended)

```bash
# Start MongoDB using Docker
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  mongo:6.0
```

#### Option 2: Local Installation

```bash
# Install MongoDB (macOS)
brew install mongodb-community@6.0
brew services start mongodb-community@6.0

# Install MongoDB (Ubuntu/Debian)
sudo apt-get install mongodb
sudo systemctl start mongodb
```

---

## 🎮 Usage

The agent can run in **two modes**: Interactive Mode (CLI chat) and API Mode (REST API server).

### 1️⃣ Interactive Mode (CLI Chat)

Start a conversational interface in your terminal:

```bash
uv run python src/agent/loan_advisor_agent.py
```

**Example conversation:**
```
You: I want to borrow $50,000 for 36 months at 5% interest. What's my monthly payment?

Agent: ## Loan Payment Calculation

**Loan Amount**: $50,000.00
**Interest Rate**: 5.00% per year
**Loan Term**: 36 months (3.0 years)

### Monthly Payment: $1,498.88

**Total Payment**: $53,959.68
**Total Interest**: $3,959.68
**Interest as % of Principal**: 7.9%
```

**Features:**
- Real-time chat interface
- Session persistence (if MongoDB is configured)
- Tool execution displayed in real-time
- Natural language queries
- Type `exit` or `quit` to end the session

**Use cases:**
- Development and testing
- Demos and presentations
- Quick loan calculations
- Debugging agent behavior

---

### 2️⃣ API Mode (REST API Server)

Launch the FastAPI server for programmatic access:

```bash
uv run python src/agent/loan_advisor_agent.py --api
```

**Server endpoints:**
- **API Server**: `http://localhost:8000`
- **Interactive API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`
- **AgentOS UI**: `http://localhost:3000` (web interface)

**Example API usage:**

```bash
# Create a new session
curl -X POST "http://localhost:8000/sessions" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}'

# Send a query
curl -X POST "http://localhost:8000/sessions/{session_id}/runs" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Check eligibility for $30,000 loan, age 25, income $6000/month, credit score 720"
  }'
```

**Use cases:**
- Web/mobile application integration
- Customer-facing loan advisory interfaces
- Batch processing of loan queries
- Production deployment

---

## 🧪 Testing

The project includes **two testing layers**: Unit Tests (business logic) and DeepEval Tests (agent quality).

### Test Summary

| Test Type | Files | Count | Coverage | Speed |
|-----------|-------|-------|----------|-------|
| **Unit Tests** | `test_loan_calculator_simple.py`<br>`test_loan_eligibility_simple.py`<br>`test_loan_rules.py`<br>`test_loan_calculator_extended.py` | **134 tests** | All 11 tools + rules | ~0.5s |
| **Response Model Tests** | `test_response_models.py` | **48 tests** | Pydantic response models | ~0.2s |
| **Formatter Tests** | `test_output_formatter.py` | **49 tests** | Output formatters (SOLID) | ~0.2s |
| **DeepEval Tests** | `test_loan_advisor_agent.py` | **4 tests** | Agent quality | ~30s |

---

### 1️⃣ Unit Tests

Test the **core business logic** of all 11 tools and rule engine (no AI, no agent).

#### Run Unit Tests

```bash
# Run all unit tests (134 tests, fast)
uv run pytest tests/test_loan_*.py -v --ignore=tests/test_loan_advisor_agent.py

# Run with coverage report
uv run pytest tests/test_loan_*.py --ignore=tests/test_loan_advisor_agent.py --cov=src/tools --cov-report=term-missing

# Generate HTML coverage report
uv run pytest tests/test_loan_*.py --ignore=tests/test_loan_advisor_agent.py --cov=src/tools --cov-report=html
open htmlcov/index.html
```

#### What's Tested

**Calculator Tests** (16 tests) - Personal loan tools:
- ✅ Monthly payment calculations
- ✅ Amortization schedules
- ✅ DTI ratio and affordability
- ✅ Loan term comparisons
- ✅ Maximum loan calculations
- ✅ Edge cases (zero interest, large amounts)

**Eligibility Tests** (26 tests) - Eligibility tool:
- ✅ Age requirements
- ✅ Income thresholds
- ✅ Credit score validation
- ✅ Employment status
- ✅ DTI limits
- ✅ Boundary conditions

**Loan Rules Tests** (46 tests) - Rule engine:
- ✅ MortgageRule model validation
- ✅ UAE Central Bank regulation matching
- ✅ Price-based LTV boundaries (5M AED)
- ✅ Residency-based rule selection
- ✅ Auto loan rules by vehicle type
- ✅ Default fallback behavior

**Extended Calculator Tests** (46 tests) - Mortgage/Auto tools:
- ✅ Home affordability calculations
- ✅ Mortgage payment with LTV rules
- ✅ Car loan calculations
- ✅ Term comparison (36/48/60/72 months)
- ✅ Early payoff interest savings
- ✅ Factory pattern (get_calculator)

---

### 2️⃣ DeepEval Evaluation

Evaluate the **complete agent system** using LLM-as-judge metrics.

#### Run DeepEval Tests

```bash
# Run all DeepEval tests (requires OpenAI API key)
uv run pytest tests/test_loan_advisor_agent.py -v -s

# Run specific tests
uv run pytest tests/test_loan_advisor_agent.py::test_agent_with_reference_free_metrics -v
uv run pytest tests/test_loan_advisor_agent.py::test_tool_calls_info -v
```

#### Evaluation Metrics

| Metric | Threshold | Purpose |
|--------|-----------|---------|
| **Answer Relevancy** | ≥ 70% | Ensures agent stays on topic |
| **Faithfulness** | ≥ 70% | Response based on facts from tools |
| **Hallucination** | ≤ 50% | Prevents false claims |
| **Tool Call Accuracy** | 100% | Validates correct tool selection |
| **Output Keywords** | 100% | Critical information present |

#### Run All Tests

```bash
# Run everything (231 tests total)
uv run pytest tests/ -v

# Quick validation (unit tests only)
uv run pytest tests/test_loan_*.py -v --ignore=tests/test_loan_advisor_agent.py

# Run formatter and response model tests
uv run pytest tests/test_output_formatter.py tests/test_response_models.py -v
```

---

## 🏗️ Architecture

### System Architecture

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

### Key Design Principles

1. **Two-Layer Architecture**
   - **Tools Layer** (`src/tools/`) - Pure business logic, framework-agnostic
   - **Agent Layer** (`src/agent/`) - AgentOS integration and orchestration

2. **Rule-Based Engine (SOLID)**
   - **Single Responsibility** - Each rule handles one condition set
   - **Open/Closed** - Add new rules without modifying existing code
   - **Liskov Substitution** - MortgageRule and AutoLoanRule are interchangeable
   - First-match algorithm for efficient rule lookup

3. **Dependency Inversion**
   - Business logic doesn't depend on AI frameworks
   - Tools can be reused in LangChain, LlamaIndex, etc.

4. **Testing Pyramid**
   - Fast unit tests for business logic (134 tests)
   - Comprehensive DeepEval tests for agent quality (4 tests)

---

## 📁 Project Structure

```
personal-loan-advisor-agent/
├── src/
│   ├── agent/                          # Agent Layer (AgentOS)
│   │   ├── loan_advisor_agent.py       # Main agent (interactive + API)
│   │   ├── loan_advisor_tools.py       # Tool wrappers for AgentOS
│   │   ├── response_models.py          # Pydantic response models (NEW)
│   │   └── output_formatter.py         # SOLID output formatter (NEW)
│   ├── tools/                          # Business Logic Layer
│   │   ├── loan_eligibility.py         # Eligibility checking logic
│   │   ├── loan_calculator.py          # Loan calculation (personal/mortgage/auto)
│   │   ├── loan_rules.py               # UAE mortgage & auto loan LTV rules
│   │   └── loan_types.py               # Loan type enums
│   └── utils/                          # Utilities
│       ├── config.py                   # Configuration management
│       └── logger.py                   # Logging system
├── tests/                              # Testing & Evaluation
│   ├── test_loan_calculator_simple.py  # 16 personal loan calculator tests
│   ├── test_loan_eligibility_simple.py # 26 eligibility tests
│   ├── test_loan_rules.py              # 46 rule engine tests
│   ├── test_loan_calculator_extended.py# 46 mortgage/auto calculator tests
│   ├── test_response_models.py         # 48 response model tests (NEW)
│   ├── test_output_formatter.py        # 49 output formatter tests (NEW)
│   ├── test_loan_advisor_agent.py      # 4 DeepEval integration tests
│   └── deepeval_config.py              # DeepEval configuration
├── docs/                               # Documentation
│   └── MULTI_LOAN_TYPE_DESIGN_CN.md    # Multi-loan design (Chinese/English)
├── .env.example                        # Environment variables template
├── pyproject.toml                      # Project dependencies
├── pytest.ini                          # Pytest configuration
└── README.md                           # This file
```

---

## 🛠️ Development

### Adding New Tools

1. **Create tool in `src/tools/`** (business logic)
2. **Add wrapper in `src/agent/loan_advisor_tools.py`** (AgentOS integration)
3. **Write unit tests** in `tests/`
4. **Update DeepEval tests** to include new tool scenarios

### Code Quality Standards

- ✅ Type hints for all functions
- ✅ Pydantic models for input validation
- ✅ Comprehensive error handling
- ✅ Structured logging
- ✅ Unit tests for all business logic
- ✅ DeepEval tests for agent changes

### Running Development Server

```bash
# Interactive mode with auto-reload (for development)
uv run python src/agent/loan_advisor_agent.py

# API mode with auto-reload
uv run uvicorn src.agent.loan_advisor_agent:app --reload
```

---

## 🎓 What Makes This Project Stand Out

1. **Multi-Loan Support** - Personal loans, mortgages, and auto loans with UAE regulations
2. **Rule-Based LTV Engine** - Dynamic LTV calculation based on residency and property type
3. **Structured Output Mode** - Configurable output with Strategy/Factory patterns (SOLID)
4. **SOLID Design Principles** - Extensible rule system and output formatters
5. **Comprehensive Testing** - 231 tests (134 unit + 48 response + 49 formatter + DeepEval)
6. **Context Reconstruction Innovation** - Solved DeepEval's Hallucination metric context problem
7. **Production-Ready** - Type hints, Pydantic validation, error handling, logging
8. **Framework-Agnostic** - Business logic independent of AI framework
9. **Complete Tool Coverage** - All 11 tools fully tested

---

## 📚 Additional Resources

- [AgentOS Documentation](https://docs.agno.com)
- [DeepEval Documentation](https://docs.confident-ai.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)

---

## 📄 License

MIT License

---

## 🤝 Contributing

This is a portfolio project demonstrating production-ready AI agent development. For contributions:

1. Fork the repository
2. Create a feature branch
3. Add unit tests for business logic changes
4. Add DeepEval tests for agent changes
5. Submit a pull request

---

**Built with ❤️ using AgentOS 2.0, OpenAI GPT-4, DeepEval, MongoDB, and modern Python practices**

*Demonstrating production-level AI agent development with comprehensive testing and evaluation*
