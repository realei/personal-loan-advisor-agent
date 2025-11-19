# 测试说明

## 📋 测试文件组织

```
tests/
├── README_TESTS.md                              # 本文件
│
├── 业务逻辑单元测试 (给面试官演示)
│   ├── test_loan_calculator_simple.py           # ⭐ 贷款计算器测试
│   └── test_loan_eligibility_simple.py          # ⭐ 资格检查测试
│
└── 评估系统测试 (核心亮点)
    ├── deepeval_config.py                       # 评估配置
    ├── test_mongodb_deepeval.py                 # DeepEval集成
    ├── test_mongodb_deepeval_with_storage.py    # 带存储的评估
    └── test_agent_evaluation.py                 # Agent评估
```

---

## 🚀 快速运行测试

### 运行所有测试
```bash
uv run pytest tests/ -v
```

### 运行业务逻辑测试（给面试官看）
```bash
# 贷款计算器测试
uv run pytest tests/test_loan_calculator_simple.py -v

# 资格检查测试
uv run pytest tests/test_loan_eligibility_simple.py -v

# 两个一起运行
uv run pytest tests/test_loan_calculator_simple.py tests/test_loan_eligibility_simple.py -v
```

### 运行评估系统测试
```bash
# DeepEval集成测试
uv run pytest tests/test_mongodb_deepeval_with_storage.py -v

# 性能基准测试
uv run pytest tests/test_mongodb_deepeval_with_storage.py::TestWithStorage::test_performance_benchmark_with_storage -v
```

---

## 📊 测试覆盖的场景

### `test_loan_calculator_simple.py` (贷款计算器)

#### ✅ 基础功能测试
- **基本月供计算** - 最常见的贷款计算场景
- **零利率贷款** - 边界情况
- **利率影响** - 验证利率越高，月供越高
- **期限影响** - 验证期限越长，月供越低但总利息更高

#### ✅ 边界情况测试
- 极小贷款金额（$100）
- 大额贷款（$1,000,000）
- 负数输入验证（应该失败）
- 零期限验证（应该失败）

#### ✅ 业务逻辑测试
- **可负担性检查** - DTI比率计算
- **还款计划** - 验证余额递减、本金占比增加
- **总额匹配** - 验证数学正确性

#### ✅ 性能测试（可选）
- 计算速度基准
- 大型还款计划生成（360期）

### `test_loan_eligibility_simple.py` (资格检查)

#### ✅ 完美vs不合格场景
- **完美申请人** - 所有条件都满足
- **年龄不合格** - 太年轻/太老
- **收入不合格** - 收入太低
- **信用分不合格** - 信用分太低

#### ✅ DTI比率测试
- 可接受的DTI（< 50%）
- 过高的DTI（> 50%）

#### ✅ 就业状态测试
- 全职就业（最佳）
- 失业（影响资格）
- 就业时间太短

#### ✅ 历史记录测试
- 有违约记录
- 有现有贷款

#### ✅ 边界条件测试
- 最小年龄（18岁）
- 最大年龄（65岁）
- 最低收入（$5,000）
- 最低信用分（600）

#### ✅ 参数化测试
- 多个年龄范围测试
- 不同信用分数的影响

---

## 💡 测试设计亮点（给面试官讲）

### 1. 测试金字塔
```
        /\
       /评估\       ← 评估系统测试（集成测试）
      /------\
     /单元测试\     ← 业务逻辑测试（这两个文件）
    /--------\
```

### 2. 测试命名清晰
```python
def test_basic_monthly_payment_calculation(self, calculator):
    """测试基本月供计算 - 最常见场景"""
    # Given-When-Then模式
```

### 3. Given-When-Then模式
```python
# Given: 设置测试数据
result = calculator.calculate_monthly_payment(
    loan_amount=50000,
    annual_interest_rate=0.05,
    loan_term_months=36
)

# Then: 验证结果
assert result.monthly_payment > 0
assert result.total_interest > 0
```

### 4. 边界值测试
```python
@pytest.mark.parametrize("age,expected_eligible", [
    (17, False),  # 边界外
    (18, True),   # 边界值 ✅
    (35, True),   # 正常值
    (65, True),   # 边界值 ✅
    (66, False),  # 边界外
])
```

### 5. 业务逻辑验证
```python
def test_higher_interest_means_higher_payment(self, calculator):
    """验证业务规则：利率越高，月供越高"""
    low_rate_result = calculator.calculate_monthly_payment(...)
    high_rate_result = calculator.calculate_monthly_payment(...)

    assert high_rate_result.monthly_payment > low_rate_result.monthly_payment
```

---

## 🎯 面试演示流程

### 第1步：展示测试结构
```bash
# 显示测试文件
ls -lh tests/test_loan_*_simple.py
```

### 第2步：运行业务逻辑测试
```bash
# 运行并展示输出
uv run pytest tests/test_loan_calculator_simple.py -v --tb=short

# 输出示例：
# test_loan_calculator_simple.py::TestLoanCalculatorBasics::test_basic_monthly_payment_calculation PASSED
# test_loan_calculator_simple.py::TestLoanCalculatorBasics::test_zero_interest_rate PASSED
# test_loan_calculator_simple.py::TestLoanCalculatorEdgeCases::test_invalid_negative_amount PASSED
# ...
```

### 第3步：展示代码质量
```bash
# 显示测试覆盖率
uv run pytest tests/test_loan_calculator_simple.py tests/test_loan_eligibility_simple.py \
    --cov=src/tools --cov-report=term-missing
```

### 第4步：讲解测试设计
打开测试文件，展示：
1. **清晰的测试组织** - 用class分组
2. **Given-When-Then模式** - 可读性强
3. **边界值测试** - 完整性
4. **参数化测试** - pytest高级用法
5. **fixture复用** - DRY原则

### 第5步：运行评估系统（亮点）
```bash
# 展示评估系统
uv run python scripts/run_evaluation.py --mode recent --hours 24 --limit 3 --with-tools
```

---

## 📈 测试统计

### 业务逻辑测试
- **test_loan_calculator_simple.py**: 16个测试 ✅
- **test_loan_eligibility_simple.py**: 26个测试 ✅
- **总计**: 42个测试用例

### 测试类型分布
```
基础功能测试:     40%  ████████
边界情况测试:     30%  ██████
业务逻辑验证:     20%  ████
性能/集成测试:    10%  ██
```

### 预期结果
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

## 🔧 pytest配置

项目根目录的 `pytest.ini`:
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

## 💼 面试问答准备

### Q: "你如何组织测试？"
**A**: "我采用了测试金字塔原则：
- **底层**: 大量单元测试（test_loan_calculator_simple.py等）- 快速、独立
- **中层**: 集成测试（test_mongodb_deepeval.py）- 验证组件协作
- **顶层**: 评估系统测试 - 端到端质量保证

每个测试文件都按功能分类（class），使用Given-When-Then模式提高可读性。"

### Q: "你如何保证测试质量？"
**A**: "我关注几个方面：
1. **边界值测试** - 测试临界条件（18岁、65岁等）
2. **负面测试** - 验证错误处理（负数、零值）
3. **业务逻辑验证** - 不只是技术正确，还要业务正确（利率高→月供高）
4. **参数化测试** - 用相同逻辑测试多个场景
5. **fixture复用** - DRY原则，减少重复代码"

### Q: "你的测试覆盖率如何？"
**A**: "业务逻辑层（src/tools）的覆盖率>90%。更重要的是，我不只追求行覆盖率，还关注：
- **分支覆盖** - 所有if/else都测试到
- **边界覆盖** - 边界值都测试到
- **业务场景覆盖** - 真实用户场景都覆盖"

### Q: "为什么创建_simple.py测试文件？"
**A**: "这些是专门为演示设计的简洁测试，展示：
- 清晰的测试结构
- 完整的场景覆盖
- 最佳实践（Given-When-Then、参数化）
- 业务逻辑验证

生产环境可能还有更详细的测试，但这些文件最适合给人看。"

---

## 🚀 快速开始

```bash
# 1. 安装依赖
uv sync

# 2. 运行业务逻辑测试
uv run pytest tests/test_loan_*_simple.py -v

# 3. 查看覆盖率
uv run pytest tests/test_loan_*_simple.py --cov=src/tools --cov-report=html

# 4. 打开覆盖率报告
open htmlcov/index.html
```

---

**测试是代码质量的保证，更是工程师专业性的体现！** ✨
