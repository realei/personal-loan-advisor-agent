# Test Documentation

## 📋 Test File Organization

```
tests/
├── README_TESTS.md                              # This file
│
├── Business Logic Unit Tests (for interview demo)
│   ├── test_loan_calculator_simple.py           # ⭐ Loan calculator tests
│   └── test_loan_eligibility_simple.py          # ⭐ Eligibility checker tests
│
└── Evaluation System Tests (core highlight)
    ├── deepeval_config.py                       # Evaluation configuration
    ├── test_mongodb_deepeval.py                 # DeepEval integration
    ├── test_mongodb_deepeval_with_storage.py    # Evaluation with storage
    └── test_agent_evaluation.py                 # Agent evaluation
```

---

## 🚀 Quick Test Execution

### Run All Tests
```bash
uv run pytest tests/ -v
```

### Run Business Logic Tests (for interview demo)
```bash
# Loan calculator tests
uv run pytest tests/test_loan_calculator_simple.py -v

# Eligibility checker tests
uv run pytest tests/test_loan_eligibility_simple.py -v

# Run both together
uv run pytest tests/test_loan_calculator_simple.py tests/test_loan_eligibility_simple.py -v
```

### Run Evaluation System Tests
```bash
# DeepEval integration tests
uv run pytest tests/test_mongodb_deepeval_with_storage.py -v

# Performance benchmark tests
uv run pytest tests/test_mongodb_deepeval_with_storage.py::TestWithStorage::test_performance_benchmark_with_storage -v
```

---

## 📊 Test Coverage Scenarios

### `test_loan_calculator_simple.py` (Loan Calculator)

#### ✅ Basic Functionality Tests
- **Basic monthly payment calculation** - Most common loan calculation scenario
- **Zero interest rate loan** - Edge case
- **Interest rate impact** - Verify higher rate = higher payment
- **Term impact** - Verify longer term = lower payment but higher total interest

#### ✅ Edge Case Tests
- Very small loan amount ($100)
- Large loan amount ($1,000,000)
- Negative input validation (should fail)
- Zero term validation (should fail)

#### ✅ Business Logic Tests
- **Affordability check** - DTI ratio calculation
- **Payment schedule** - Verify balance decreases, principal portion increases
- **Total amount matching** - Verify mathematical correctness

#### ✅ Performance Tests (optional)
- Calculation speed benchmark
- Large payment schedule generation (360 months)

### `test_loan_eligibility_simple.py` (Eligibility Check)

#### ✅ Perfect vs Unqualified Scenarios
- **Perfect applicant** - All conditions met
- **Age disqualified** - Too young/too old
- **Income disqualified** - Income too low
- **Credit score disqualified** - Credit score too low

#### ✅ DTI Ratio Tests
- Acceptable DTI (< 50%)
- Excessive DTI (> 50%)

#### ✅ Employment Status Tests
- Full-time employment (best)
- Unemployed (affects eligibility)
- Employment duration too short

#### ✅ History Record Tests
- Has default record
- Has existing loans

#### ✅ Boundary Condition Tests
- Minimum age (18)
- Maximum age (65)
- Minimum income ($5,000)
- Minimum credit score (600)

#### ✅ Parameterized Tests
- Multiple age range tests
- Different credit score impacts

---

## 💡 Test Design Highlights (for interview discussion)

### 1. Test Pyramid
```
        /\
       /Eval\       ← Evaluation system tests (integration tests)
      /------\
     /Unit Test\    ← Business logic tests (these two files)
    /--------\
```

### 2. Clear Test Naming
```python
def test_basic_monthly_payment_calculation(self, calculator):
    """Test basic monthly payment calculation - most common scenario"""
    # Given-When-Then pattern
```

### 3. Given-When-Then Pattern
```python
# Given: Setup test data
result = calculator.calculate_monthly_payment(
    loan_amount=50000,
    annual_interest_rate=0.05,
    loan_term_months=36
)

# Then: Verify results
assert result.monthly_payment > 0
assert result.total_interest > 0
```

### 4. Boundary Value Testing
```python
@pytest.mark.parametrize("age,expected_eligible", [
    (17, False),  # Outside boundary
    (18, True),   # Boundary value ✅
    (35, True),   # Normal value
    (65, True),   # Boundary value ✅
    (66, False),  # Outside boundary
])
```

### 5. Business Logic Validation
```python
def test_higher_interest_means_higher_payment(self, calculator):
    """Verify business rule: higher interest rate = higher payment"""
    low_rate_result = calculator.calculate_monthly_payment(...)
    high_rate_result = calculator.calculate_monthly_payment(...)

    assert high_rate_result.monthly_payment > low_rate_result.monthly_payment
```

---

## 🎯 Interview Demo Process

### Step 1: Show Test Structure
```bash
# Display test files
ls -lh tests/test_loan_*_simple.py
```

### Step 2: Run Business Logic Tests
```bash
# Run and show output
uv run pytest tests/test_loan_calculator_simple.py -v --tb=short

# Example output:
# test_loan_calculator_simple.py::TestLoanCalculatorBasics::test_basic_monthly_payment_calculation PASSED
# test_loan_calculator_simple.py::TestLoanCalculatorBasics::test_zero_interest_rate PASSED
# test_loan_calculator_simple.py::TestLoanCalculatorEdgeCases::test_invalid_negative_amount PASSED
# ...
```

### Step 3: Show Code Quality
```bash
# Show test coverage
uv run pytest tests/test_loan_calculator_simple.py tests/test_loan_eligibility_simple.py \
    --cov=src/tools --cov-report=term-missing
```

### Step 4: Explain Test Design
Open test files to show:
1. **Clear test organization** - Grouped by class
2. **Given-When-Then pattern** - High readability
3. **Boundary value testing** - Completeness
4. **Parameterized testing** - Advanced pytest usage
5. **Fixture reuse** - DRY principle

### Step 5: Run Evaluation System (highlight)
```bash
# Show evaluation system
uv run python scripts/run_evaluation.py --mode recent --hours 24 --limit 3 --with-tools
```

---

## 📈 Test Statistics

### Business Logic Tests
- **test_loan_calculator_simple.py**: 16 tests ✅
- **test_loan_eligibility_simple.py**: 26 tests ✅
- **Total**: 42 test cases

### Test Type Distribution
```
Basic functionality tests:  40%  ████████
Edge case tests:            30%  ██████
Business logic validation:  20%  ████
Performance/integration:    10%  ██
```

### Expected Results
```bash
$ uv run pytest tests/test_loan_*_simple.py -v

=================== test session starts ===================
collected 42 items

test_loan_calculator_simple.py::... PASSED        [ 10%]
test_loan_calculator_simple.py::... PASSED        [ 20%]
...
test_loan_eligibility_simple.py::... PASSED       [ 90%]
test_loan_eligibility_simple.py::... PASSED       [100%]

=================== 42 passed in 0.34s ====================
```

---

## 🔧 pytest Configuration

Project root `pytest.ini`:
```ini
[pytest]
markers =
    benchmark: Performance benchmark tests
    integration: Integration tests
    unit: Unit tests

testpaths = tests
python_files = test_*.py
python_functions = test_*

addopts =
    -v
    --tb=short
    --strict-markers
```

---

## 💼 Interview Q&A Preparation

### Q: "How do you organize tests?"
**A**: "I adopted the test pyramid principle:
- **Bottom layer**: Numerous unit tests (test_loan_calculator_simple.py, etc.) - fast and independent
- **Middle layer**: Integration tests (test_mongodb_deepeval.py) - verify component collaboration
- **Top layer**: Evaluation system tests - end-to-end quality assurance

Each test file is organized by functionality (class), using Given-When-Then pattern for improved readability."

### Q: "How do you ensure test quality?"
**A**: "I focus on several aspects:
1. **Boundary value testing** - Test critical conditions (18, 65 years, etc.)
2. **Negative testing** - Verify error handling (negative numbers, zero values)
3. **Business logic validation** - Not just technically correct, but business correct (high rate → high payment)
4. **Parameterized testing** - Test multiple scenarios with same logic
5. **Fixture reuse** - DRY principle, reduce code duplication"

### Q: "What's your test coverage?"
**A**: "Business logic layer (src/tools) coverage >90%. More importantly, I don't just pursue line coverage, but also:
- **Branch coverage** - All if/else tested
- **Boundary coverage** - All boundary values tested
- **Business scenario coverage** - All real user scenarios covered"

### Q: "Why create _simple.py test files?"
**A**: "These are concise tests designed specifically for demos, showcasing:
- Clear test structure
- Complete scenario coverage
- Best practices (Given-When-Then, parameterization)
- Business logic validation

Production environments might have more detailed tests, but these files are best for presentation."

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Run business logic tests
uv run pytest tests/test_loan_*_simple.py -v

# 3. View coverage
uv run pytest tests/test_loan_*_simple.py --cov=src/tools --cov-report=html

# 4. Open coverage report
open htmlcov/index.html
```

---

**Testing is the guarantee of code quality and a demonstration of engineering professionalism!** ✨
