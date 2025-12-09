# 重构计划：SOLID 原则 + numpy-financial

## 1. 重构的好处

### 1.1 使用 numpy-financial 的好处

| 方面 | 当前实现 | 重构后 |
|------|---------|--------|
| **可信度** | 自定义公式，需要验证 | 银行标准库，Excel兼容 |
| **维护性** | 需要自己维护公式 | 社区维护，减少bug风险 |
| **性能** | 循环计算摊销表 | 向量化操作，性能提升10x+ |
| **审计** | 需要解释公式推导 | 行业认可，审计友好 |

### 1.2 SOLID 原则的好处

| 原则 | 当前问题 | 重构后收益 |
|------|---------|-----------|
| **S** 单一职责 | Calculator 混合了计算和格式化 | 清晰分离，易于测试 |
| **O** 开闭原则 | 添加房贷需要修改现有类 | 扩展新贷款类型无需改动 |
| **L** 里氏替换 | 没有抽象基类 | 子类可安全替换父类 |
| **I** 接口隔离 | 单一大接口 | 小而专注的接口 |
| **D** 依赖反转 | 直接依赖具体实现 | 依赖抽象，易于mock测试 |

---

## 2. 新架构设计

### 2.1 整体架构图

```
                    ┌─────────────────────────────────────┐
                    │         LoanAdvisorAgent            │
                    │    (使用 agent/loan_advisor_tools)  │
                    └─────────────────┬───────────────────┘
                                      │
                    ┌─────────────────▼───────────────────┐
                    │           Facade Layer              │
                    │   LoanCalculatorTool (保持接口)     │
                    │   LoanEligibilityTool (保持接口)    │
                    └─────────────────┬───────────────────┘
                                      │
       ┌──────────────────────────────┼──────────────────────────────┐
       │                              │                              │
       ▼                              ▼                              ▼
┌──────────────┐           ┌──────────────────┐           ┌──────────────────┐
│CalculationEngine│        │ EligibilityEngine │           │  AmortizationEngine│
│  (核心计算)      │        │   (资格审查)      │           │    (摊销生成)      │
└──────┬───────┘           └────────┬─────────┘           └────────┬─────────┘
       │                            │                              │
       ▼                            ▼                              ▼
┌──────────────┐           ┌──────────────────┐           ┌──────────────────┐
│  ILoanProduct │           │ IEligibilityRule │           │IAmortizationStrategy│
│   (抽象接口)   │           │   (规则接口)     │           │   (策略接口)       │
└──────┬───────┘           └────────┬─────────┘           └────────┬─────────┘
       │                            │                              │
       ├────────────┐               ├────────────┐                 ├────────────┐
       ▼            ▼               ▼            ▼                 ▼            ▼
┌──────────┐ ┌──────────┐  ┌──────────┐ ┌──────────┐       ┌──────────┐ ┌──────────┐
│PersonalLoan│ │Mortgage │  │ AgeRule  │ │ DTIRule  │       │FixedRate │ │Adjustable│
│  (个人贷款) │ │ (房贷)   │  │(年龄规则) │ │(DTI规则) │       │(固定利率) │ │ (浮动利率)│
└──────────┘ └──────────┘  └──────────┘ └──────────┘       └──────────┘ └──────────┘
```

### 2.2 目录结构

```
src/
├── tools/
│   ├── __init__.py
│   ├── loan_calculator.py      # Facade - 保持原有接口 (向后兼容)
│   ├── loan_eligibility.py     # Facade - 保持原有接口
│   │
│   ├── core/                   # 核心抽象层 (NEW)
│   │   ├── __init__.py
│   │   ├── interfaces.py       # 所有抽象接口/协议
│   │   ├── models.py           # 共享数据模型
│   │   └── exceptions.py       # 自定义异常
│   │
│   ├── calculation/            # 计算引擎 (NEW)
│   │   ├── __init__.py
│   │   ├── engine.py           # CalculationEngine (使用npf)
│   │   └── strategies.py       # 摊销策略
│   │
│   ├── eligibility/            # 资格审查引擎 (NEW)
│   │   ├── __init__.py
│   │   ├── engine.py           # EligibilityEngine
│   │   └── rules.py            # 各种规则实现
│   │
│   └── products/               # 贷款产品 (NEW - 扩展性)
│       ├── __init__.py
│       ├── base.py             # BaseLoanProduct
│       ├── personal.py         # PersonalLoan
│       ├── mortgage.py         # MortgageLoan (未来)
│       └── auto.py             # AutoLoan (未来)
```

---

## 3. 核心接口设计 (Interface Segregation)

### 3.1 core/interfaces.py

```python
from abc import ABC, abstractmethod
from typing import Protocol
from dataclasses import dataclass
import pandas as pd

# =============================================
# 协议定义 (Protocol - Python 3.8+)
# =============================================

class IPaymentCalculator(Protocol):
    """月供计算接口 - 单一职责"""
    def calculate_payment(
        self,
        principal: float,
        annual_rate: float,
        term_months: int
    ) -> float:
        """计算月供"""
        ...

class IInterestCalculator(Protocol):
    """利息计算接口"""
    def calculate_interest(
        self,
        balance: float,
        monthly_rate: float
    ) -> float:
        """计算当期利息"""
        ...

class IAmortizationGenerator(Protocol):
    """摊销表生成接口"""
    def generate(
        self,
        principal: float,
        annual_rate: float,
        term_months: int
    ) -> pd.DataFrame:
        """生成摊销表"""
        ...

# =============================================
# 抽象基类 (Abstract Base Class)
# =============================================

class BaseLoanProduct(ABC):
    """贷款产品抽象基类 - Liskov Substitution"""

    @property
    @abstractmethod
    def product_type(self) -> str:
        """产品类型标识"""
        pass

    @property
    @abstractmethod
    def min_term_months(self) -> int:
        """最小期限"""
        pass

    @property
    @abstractmethod
    def max_term_months(self) -> int:
        """最大期限"""
        pass

    @abstractmethod
    def get_base_rate(self) -> float:
        """获取基准利率"""
        pass

    @abstractmethod
    def calculate_risk_premium(self, credit_score: int) -> float:
        """计算风险溢价"""
        pass

class BaseEligibilityRule(ABC):
    """资格规则抽象基类"""

    @property
    @abstractmethod
    def rule_name(self) -> str:
        """规则名称"""
        pass

    @property
    @abstractmethod
    def weight(self) -> float:
        """规则权重 (0-1)"""
        pass

    @abstractmethod
    def check(self, applicant: 'ApplicantInfo') -> 'RuleResult':
        """执行规则检查"""
        pass
```

### 3.2 core/models.py

```python
from dataclasses import dataclass
from typing import Optional
from enum import Enum
import pandas as pd

class LoanProductType(str, Enum):
    """贷款产品类型"""
    PERSONAL = "personal"
    MORTGAGE = "mortgage"
    AUTO = "auto"
    STUDENT = "student"

@dataclass(frozen=True)
class LoanCalculation:
    """贷款计算结果 - Immutable Value Object"""
    monthly_payment: float
    total_payment: float
    total_interest: float
    total_principal: float
    loan_term_months: int
    annual_interest_rate: float
    effective_monthly_rate: float

    def __post_init__(self):
        # 验证不变量
        assert self.monthly_payment > 0
        assert self.total_payment >= self.total_principal

@dataclass
class RuleResult:
    """规则检查结果"""
    passed: bool
    score: float  # 0-100
    reason: Optional[str] = None
    recommendation: Optional[str] = None
```

---

## 4. 计算引擎实现 (使用 numpy-financial)

### 4.1 calculation/engine.py

```python
import numpy_financial as npf
import numpy as np
import pandas as pd
from typing import Optional

from ..core.interfaces import IPaymentCalculator, IAmortizationGenerator
from ..core.models import LoanCalculation

class CalculationEngine(IPaymentCalculator, IAmortizationGenerator):
    """
    核心计算引擎 - 使用 numpy-financial

    Single Responsibility: 只负责数学计算
    Open/Closed: 通过策略模式扩展不同计算方法
    """

    def calculate_payment(
        self,
        principal: float,
        annual_rate: float,
        term_months: int
    ) -> float:
        """使用 npf.pmt 计算月供"""
        if annual_rate == 0:
            return principal / term_months

        monthly_rate = annual_rate / 12
        # npf.pmt 返回负数（表示支出），取正
        return -npf.pmt(monthly_rate, term_months, principal)

    def calculate_full(
        self,
        principal: float,
        annual_rate: float,
        term_months: int
    ) -> LoanCalculation:
        """完整计算"""
        monthly_payment = self.calculate_payment(principal, annual_rate, term_months)
        total_payment = monthly_payment * term_months
        total_interest = total_payment - principal

        return LoanCalculation(
            monthly_payment=monthly_payment,
            total_payment=total_payment,
            total_interest=total_interest,
            total_principal=principal,
            loan_term_months=term_months,
            annual_interest_rate=annual_rate,
            effective_monthly_rate=annual_rate / 12
        )

    def generate(
        self,
        principal: float,
        annual_rate: float,
        term_months: int
    ) -> pd.DataFrame:
        """
        向量化生成摊销表 - 性能优化

        使用 npf.ipmt 和 npf.ppmt 一次性计算所有期的利息和本金
        """
        if annual_rate == 0:
            return self._generate_zero_interest(principal, term_months)

        monthly_rate = annual_rate / 12
        payment = -npf.pmt(monthly_rate, term_months, principal)

        # 向量化计算 - 比循环快10x+
        periods = np.arange(1, term_months + 1)

        interest = -npf.ipmt(monthly_rate, periods, term_months, principal)
        principal_paid = -npf.ppmt(monthly_rate, periods, term_months, principal)
        balance = -npf.fv(monthly_rate, periods, payment, principal)

        # 修正浮点误差
        balance = np.maximum(0, balance)
        balance[-1] = 0  # 确保最后一期余额为0

        return pd.DataFrame({
            'month': periods,
            'payment': payment,
            'principal': principal_paid,
            'interest': interest,
            'balance': balance
        })

    def _generate_zero_interest(
        self,
        principal: float,
        term_months: int
    ) -> pd.DataFrame:
        """零利率特殊处理"""
        payment = principal / term_months
        periods = np.arange(1, term_months + 1)
        balance = principal - (payment * periods)
        balance = np.maximum(0, balance)

        return pd.DataFrame({
            'month': periods,
            'payment': payment,
            'principal': payment,
            'interest': 0.0,
            'balance': balance
        })

    def calculate_max_principal(
        self,
        max_payment: float,
        annual_rate: float,
        term_months: int
    ) -> float:
        """反向计算最大本金 - 使用 npf.pv"""
        if annual_rate == 0:
            return max_payment * term_months

        monthly_rate = annual_rate / 12
        # npf.pv 计算现值（本金）
        return -npf.pv(monthly_rate, term_months, max_payment)
```

---

## 5. 资格审查引擎 (规则模式)

### 5.1 eligibility/rules.py

```python
from abc import ABC
from dataclasses import dataclass
from typing import List

from ..core.interfaces import BaseEligibilityRule
from ..core.models import RuleResult

class AgeRule(BaseEligibilityRule):
    """年龄规则"""

    def __init__(self, min_age: int = 18, max_age: int = 65):
        self.min_age = min_age
        self.max_age = max_age

    @property
    def rule_name(self) -> str:
        return "age_check"

    @property
    def weight(self) -> float:
        return 1.0

    def check(self, applicant) -> RuleResult:
        maturity_age = applicant.age + (applicant.loan_term_months / 12)

        if applicant.age < self.min_age:
            return RuleResult(
                passed=False,
                score=0,
                reason=f"Age {applicant.age} below minimum {self.min_age}",
                recommendation="Must be at least 18 years old"
            )

        if maturity_age > self.max_age:
            return RuleResult(
                passed=False,
                score=30,
                reason=f"Maturity age {maturity_age:.0f} exceeds {self.max_age}",
                recommendation="Consider shorter loan term"
            )

        return RuleResult(passed=True, score=100)

class DTIRule(BaseEligibilityRule):
    """DTI 规则 - 依赖注入计算器"""

    def __init__(self, max_dti: float = 0.5, calculator=None):
        self.max_dti = max_dti
        self.calculator = calculator  # 依赖反转

    @property
    def rule_name(self) -> str:
        return "dti_check"

    @property
    def weight(self) -> float:
        return 1.5  # DTI 权重更高

    def check(self, applicant) -> RuleResult:
        # 使用注入的计算器
        if self.calculator:
            payment = self.calculator.calculate_payment(
                applicant.requested_loan_amount,
                0.05,  # 假设利率
                applicant.loan_term_months
            )
        else:
            # 降级到简单计算
            payment = self._simple_payment_estimate(applicant)

        total_debt = applicant.monthly_debt_obligations + payment
        dti = total_debt / applicant.monthly_income

        if dti > self.max_dti:
            return RuleResult(
                passed=False,
                score=0,
                reason=f"DTI {dti:.1%} exceeds max {self.max_dti:.1%}",
                recommendation="Reduce debt or request smaller loan"
            )

        # DTI 评分
        score = self._calculate_dti_score(dti)
        return RuleResult(passed=True, score=score)

    def _calculate_dti_score(self, dti: float) -> float:
        if dti <= 0.30:
            return 100
        elif dti <= 0.36:
            return 85
        elif dti <= 0.43:
            return 70
        return 55
```

### 5.2 eligibility/engine.py

```python
from typing import List
from ..core.interfaces import BaseEligibilityRule
from ..core.models import RuleResult

class EligibilityEngine:
    """
    资格审查引擎

    Open/Closed: 通过添加规则扩展，无需修改引擎
    Dependency Inversion: 依赖抽象规则接口
    """

    def __init__(self, rules: List[BaseEligibilityRule] = None):
        self.rules = rules or []

    def add_rule(self, rule: BaseEligibilityRule) -> 'EligibilityEngine':
        """Builder 模式 - 链式添加规则"""
        self.rules.append(rule)
        return self

    def evaluate(self, applicant) -> dict:
        """执行所有规则"""
        results = {}
        total_score = 0
        total_weight = 0
        all_passed = True
        reasons = []
        recommendations = []

        for rule in self.rules:
            result = rule.check(applicant)
            results[rule.rule_name] = result

            total_score += result.score * rule.weight
            total_weight += rule.weight

            if not result.passed:
                all_passed = False
                if result.reason:
                    reasons.append(result.reason)
                if result.recommendation:
                    recommendations.append(result.recommendation)

        final_score = total_score / total_weight if total_weight > 0 else 0

        return {
            'eligible': all_passed,
            'score': final_score,
            'reasons': reasons,
            'recommendations': recommendations,
            'details': results
        }
```

---

## 6. 贷款产品扩展 (Open/Closed)

### 6.1 products/personal.py

```python
from ..core.interfaces import BaseLoanProduct

class PersonalLoan(BaseLoanProduct):
    """个人贷款产品"""

    @property
    def product_type(self) -> str:
        return "personal"

    @property
    def min_term_months(self) -> int:
        return 12

    @property
    def max_term_months(self) -> int:
        return 60

    def get_base_rate(self) -> float:
        return 0.0499  # 4.99%

    def calculate_risk_premium(self, credit_score: int) -> float:
        if credit_score >= 750:
            return 0.0
        elif credit_score >= 700:
            return 0.005
        elif credit_score >= 650:
            return 0.015
        return 0.03
```

### 6.2 products/mortgage.py (未来扩展示例)

```python
from ..core.interfaces import BaseLoanProduct

class MortgageLoan(BaseLoanProduct):
    """房贷产品 - 未来扩展"""

    @property
    def product_type(self) -> str:
        return "mortgage"

    @property
    def min_term_months(self) -> int:
        return 60  # 5年

    @property
    def max_term_months(self) -> int:
        return 360  # 30年

    def get_base_rate(self) -> float:
        return 0.0385  # 3.85% (房贷利率更低)

    def calculate_risk_premium(self, credit_score: int) -> float:
        # 房贷有抵押，风险溢价更低
        if credit_score >= 750:
            return 0.0
        elif credit_score >= 700:
            return 0.0025
        return 0.005
```

---

## 7. Facade 层 (向后兼容)

### 7.1 保持原有接口

```python
# loan_calculator.py - 重构后的 Facade

from .calculation.engine import CalculationEngine
from .core.models import LoanCalculation

class LoanCalculatorTool:
    """
    Facade 模式 - 保持原有接口，内部使用新引擎

    所有现有测试应该无需修改即可通过
    """

    def __init__(self, max_dti_ratio: float = 0.5):
        self.max_dti_ratio = max_dti_ratio
        self._engine = CalculationEngine()  # 组合新引擎

    def calculate_monthly_payment(self, loan_request: LoanRequest) -> LoanCalculation:
        """保持原有签名"""
        return self._engine.calculate_full(
            principal=loan_request.loan_amount,
            annual_rate=loan_request.annual_interest_rate,
            term_months=loan_request.loan_term_months
        )

    def generate_amortization_schedule(self, loan_request: LoanRequest) -> AmortizationSchedule:
        """保持原有签名"""
        calculation = self.calculate_monthly_payment(loan_request)
        schedule_df = self._engine.generate(
            principal=loan_request.loan_amount,
            annual_rate=loan_request.annual_interest_rate,
            term_months=loan_request.loan_term_months
        )
        return AmortizationSchedule(schedule=schedule_df, summary=calculation)

    # ... 其他方法保持原有签名
```

---

## 8. 实施步骤

### Phase 1: 核心基础设施
1. 创建 `core/` 目录和接口定义
2. 创建 `calculation/engine.py` 使用 npf
3. 运行测试确保 npf 计算结果一致

### Phase 2: Facade 重构
1. 修改 `loan_calculator.py` 使用新引擎
2. 运行所有 16 个 Calculator 测试
3. 验证向后兼容性

### Phase 3: 规则引擎
1. 创建 `eligibility/rules.py`
2. 创建 `eligibility/engine.py`
3. 修改 `loan_eligibility.py` 使用新引擎
4. 运行所有 26 个 Eligibility 测试

### Phase 4: 产品扩展层
1. 创建 `products/` 目录
2. 实现 `PersonalLoan` 产品
3. 添加扩展测试

### Phase 5: 验收
1. 运行全部 42 个测试
2. 性能对比测试
3. 更新文档

---

## 9. 设计模式总结

| 模式 | 应用位置 | 解决的问题 |
|------|---------|-----------|
| **Strategy** | AmortizationGenerator | 不同摊销算法(等额本息/等额本金) |
| **Factory** | LoanProductFactory | 创建不同贷款产品 |
| **Facade** | LoanCalculatorTool | 简化接口，向后兼容 |
| **Builder** | EligibilityEngine | 链式配置规则 |
| **Template Method** | BaseEligibilityRule | 规则检查框架 |
| **Composite** | EligibilityEngine | 组合多个规则 |

---

*Created: 2025-12-01*
