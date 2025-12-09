# numpy-financial 学习路径与银行业知识拓展

> 基于 personal-loan-advisor-agent 项目定制的学习计划

---

## 第一阶段：numpy-financial 核心函数 (1-2周)

### 1.1 项目函数映射表

| 你的项目函数 | numpy-financial 对应 | Excel 等价 |
|-------------|---------------------|-----------|
| `calculate_monthly_payment()` | `npf.pmt()` | PMT() |
| 利息部分计算 | `npf.ipmt()` | IPMT() |
| 本金部分计算 | `npf.ppmt()` | PPMT() |
| `calculate_max_loan_amount()` | `npf.pv()` | PV() |
| 未来值计算 | `npf.fv()` | FV() |
| 期数计算 | `npf.nper()` | NPER() |
| 利率计算 | `npf.rate()` | RATE() |
| 净现值 | `npf.npv()` | NPV() |
| 内部收益率 | `npf.irr()` | IRR() |

### 1.2 核心学习内容

```python
import numpy_financial as npf
import pandas as pd

# ============================================
# 练习1: 月供计算 (对应你的 calculate_monthly_payment)
# ============================================
principal = 50000      # 贷款本金
annual_rate = 0.05     # 年利率 5%
months = 36            # 36期

# npf.pmt 参数: rate(月利率), nper(期数), pv(现值/本金，取负)
monthly_payment = npf.pmt(rate=annual_rate/12, nper=months, pv=-principal)
print(f"月供: ${monthly_payment:.2f}")  # 应该 ≈ $1,498.88

# ============================================
# 练习2: 摊销表生成 (对应你的 generate_amortization_schedule)
# ============================================
def generate_amortization_npf(principal, annual_rate, months):
    """使用 numpy-financial 生成摊销表"""
    monthly_rate = annual_rate / 12
    payment = npf.pmt(monthly_rate, months, -principal)

    schedule = []
    for period in range(1, months + 1):
        interest = npf.ipmt(monthly_rate, period, months, -principal)
        principal_paid = npf.ppmt(monthly_rate, period, months, -principal)
        balance = npf.fv(monthly_rate, period, payment, -principal)

        schedule.append({
            'month': period,
            'payment': payment,
            'principal': principal_paid,
            'interest': interest,
            'balance': max(0, balance)  # 防止浮点误差
        })

    return pd.DataFrame(schedule)

# 测试
df = generate_amortization_npf(50000, 0.05, 36)
print(df.head(10))

# ============================================
# 练习3: 最大贷款额计算 (对应你的 calculate_max_loan_amount)
# ============================================
max_monthly_payment = 2000  # 最大可承受月供
annual_rate = 0.05
months = 36

# npf.pv 计算现值（即最大本金）
max_principal = npf.pv(rate=annual_rate/12, nper=months, pmt=-max_monthly_payment)
print(f"最大可贷款额: ${max_principal:.2f}")

# ============================================
# 练习4: 贷款期限计算
# ============================================
# 问题：$50,000贷款，5%年利率，月供$1,000，需要多少期？
nper = npf.nper(rate=0.05/12, pmt=-1000, pv=50000)
print(f"还款期数: {nper:.1f} 个月")

# ============================================
# 练习5: 反推利率
# ============================================
# 问题：$50,000贷款，36期，月供$1,498.88，利率是多少？
rate = npf.rate(nper=36, pmt=-1498.88, pv=50000)
print(f"月利率: {rate:.4%}, 年利率: {rate*12:.2%}")
```

### 1.3 验证练习

用 numpy-financial 重写你项目中的函数，对比结果是否一致：

```python
# 验证脚本
from src.tools.loan_calculator import LoanCalculatorTool, LoanRequest
import numpy_financial as npf

# 创建相同参数
loan = LoanRequest(loan_amount=50000, annual_interest_rate=0.05, loan_term_months=36)

# 你的实现
calculator = LoanCalculatorTool()
your_result = calculator.calculate_monthly_payment(loan)

# numpy-financial 实现
npf_result = npf.pmt(0.05/12, 36, -50000)

# 对比
print(f"你的结果: ${your_result.monthly_payment:.6f}")
print(f"npf结果:  ${npf_result:.6f}")
print(f"差异: ${abs(your_result.monthly_payment - npf_result):.10f}")
```

---

## 第二阶段：高级金融计算 (2-3周)

### 2.1 净现值 (NPV) 与内部收益率 (IRR)

```python
# NPV - 净现值
# 场景：评估一笔贷款投资是否值得

initial_investment = -100000  # 初始投资（负数）
cash_flows = [25000, 30000, 35000, 40000, 45000]  # 5年现金流
discount_rate = 0.08  # 折现率 8%

npv = npf.npv(discount_rate, [initial_investment] + cash_flows)
print(f"净现值: ${npv:.2f}")  # 正数表示值得投资

# IRR - 内部收益率
# 场景：计算贷款产品的实际收益率

irr = npf.irr([initial_investment] + cash_flows)
print(f"内部收益率: {irr:.2%}")
```

### 2.2 银行定价模型基础

```python
# 贷款定价：基准利率 + 风险溢价
def calculate_loan_rate(base_rate, credit_score, ltv_ratio):
    """
    银行贷款利率定价模型

    Args:
        base_rate: 基准利率 (如 LPR)
        credit_score: 信用评分 (300-850)
        ltv_ratio: 贷款价值比 (Loan-to-Value)
    """
    # 信用风险溢价
    if credit_score >= 750:
        credit_premium = 0.00
    elif credit_score >= 700:
        credit_premium = 0.005
    elif credit_score >= 650:
        credit_premium = 0.015
    else:
        credit_premium = 0.03

    # LTV 风险溢价
    if ltv_ratio <= 0.6:
        ltv_premium = 0.00
    elif ltv_ratio <= 0.8:
        ltv_premium = 0.005
    else:
        ltv_premium = 0.015

    return base_rate + credit_premium + ltv_premium

# 示例
rate = calculate_loan_rate(base_rate=0.0385, credit_score=720, ltv_ratio=0.75)
print(f"贷款利率: {rate:.2%}")
```

---

## 第三阶段：银行业核心概念 (3-4周)

### 3.1 风险管理核心指标

| 指标 | 英文 | 计算方式 | 用途 |
|------|------|---------|------|
| **DTI** | Debt-to-Income | 月债务/月收入 | 个人贷款审批 |
| **LTV** | Loan-to-Value | 贷款额/抵押物价值 | 房贷风险评估 |
| **PD** | Probability of Default | 违约概率模型 | 信用风险 |
| **LGD** | Loss Given Default | 违约损失率 | 风险准备金 |
| **EAD** | Exposure at Default | 违约时敞口 | 资本计算 |
| **EL** | Expected Loss | PD × LGD × EAD | 预期损失 |

### 3.2 信用评分模型 (扩展学习)

```python
import numpy as np
from sklearn.linear_model import LogisticRegression

# 简化版信用评分卡模型 (实际银行会更复杂)
def build_simple_scorecard():
    """
    信用评分卡构建示例
    实际银行使用: FICO, VantageScore, 或自研模型
    """
    # 特征权重示例
    weights = {
        'payment_history': 0.35,      # 还款历史 (最重要)
        'credit_utilization': 0.30,   # 信用使用率
        'credit_history_length': 0.15, # 信用历史长度
        'credit_mix': 0.10,           # 信用类型多样性
        'new_credit': 0.10            # 新开信用账户
    }

    return weights

# FICO 评分区间
FICO_RANGES = {
    'Exceptional': (800, 850),
    'Very Good': (740, 799),
    'Good': (670, 739),
    'Fair': (580, 669),
    'Poor': (300, 579)
}
```

### 3.3 巴塞尔协议基础 (Basel III/IV)

```python
# 银行资本充足率计算简化示例
def calculate_capital_ratio(tier1_capital, tier2_capital, risk_weighted_assets):
    """
    资本充足率 = (一级资本 + 二级资本) / 风险加权资产

    巴塞尔III要求:
    - 核心一级资本 (CET1) >= 4.5%
    - 一级资本 >= 6%
    - 总资本 >= 8%
    - 加上缓冲要求，通常需要 10.5%+
    """
    total_capital = tier1_capital + tier2_capital
    capital_ratio = total_capital / risk_weighted_assets

    return {
        'total_capital': total_capital,
        'risk_weighted_assets': risk_weighted_assets,
        'capital_ratio': capital_ratio,
        'meets_minimum': capital_ratio >= 0.08,
        'meets_buffer': capital_ratio >= 0.105
    }
```

---

## 第四阶段：职业发展路径 (长期)

### 4.1 认证路径选择

| 认证 | 适合方向 | Python相关性 | 难度 |
|------|---------|-------------|------|
| **CFA** | 投资分析、资产管理 | Level I 有 Python PSM | ⭐⭐⭐⭐⭐ |
| **FRM** | 风险管理 | 需要量化建模 | ⭐⭐⭐⭐ |
| **CQF** | 量化金融 | 核心技能 | ⭐⭐⭐⭐ |
| **PRM** | 风险管理 | 辅助技能 | ⭐⭐⭐ |

### 4.2 技能树

```
金融 Python 技能树
├── 基础层 (你已完成 ✅)
│   ├── Python 基础
│   ├── Pandas/NumPy
│   └── numpy-financial (学习中)
│
├── 中级层 (下一步)
│   ├── 统计建模 (statsmodels)
│   ├── 机器学习 (scikit-learn)
│   ├── 数据可视化 (matplotlib, plotly)
│   └── 时间序列分析
│
├── 高级层 (银行业深入)
│   ├── 信用风险模型
│   ├── 市场风险 (VaR)
│   ├── QuantLib (衍生品定价)
│   └── 蒙特卡洛模拟
│
└── 专家层
    ├── 高频交易系统
    ├── 另类数据分析
    └── AI/ML 在金融中的应用
```

### 4.3 推荐学习资源

**在线课程:**
- [CFA Python Programming Fundamentals](https://www.cfainstitute.org/programs/cfa-program/candidate-resources/practical-skills-modules/python-programming-fundamentals) - CFA 官方
- Coursera: Python and Statistics for Financial Analysis
- DataCamp: Finance Fundamentals in Python

**书籍:**
- "Python for Finance" by Yves Hilpisch
- "Advances in Financial Machine Learning" by Marcos López de Prado
- "Options, Futures, and Other Derivatives" by John Hull

**实践项目建议:**
1. 用 numpy-financial 重构你的 LoanCalculatorTool
2. 添加 Monte Carlo 压力测试功能
3. 构建简单的信用评分卡模型
4. 实现 VaR (Value at Risk) 计算

---

## 第五阶段：项目重构建议

### 5.1 建议的代码重构

```python
# src/tools/loan_calculator_v2.py
"""
使用 numpy-financial 重构的贷款计算器
"""
import numpy_financial as npf
import pandas as pd
from dataclasses import dataclass
from typing import Optional

@dataclass
class LoanCalculation:
    monthly_payment: float
    total_payment: float
    total_interest: float
    total_principal: float
    loan_term_months: int
    annual_interest_rate: float
    effective_monthly_rate: float

class LoanCalculatorV2:
    """使用 numpy-financial 的贷款计算器 (银行标准)"""

    def __init__(self, max_dti_ratio: float = 0.5):
        self.max_dti_ratio = max_dti_ratio

    def calculate_monthly_payment(
        self,
        principal: float,
        annual_rate: float,
        months: int
    ) -> LoanCalculation:
        """使用 numpy-financial 计算月供"""
        monthly_rate = annual_rate / 12

        # 使用银行标准公式
        monthly_payment = npf.pmt(monthly_rate, months, -principal)
        total_payment = monthly_payment * months
        total_interest = total_payment - principal

        return LoanCalculation(
            monthly_payment=monthly_payment,
            total_payment=total_payment,
            total_interest=total_interest,
            total_principal=principal,
            loan_term_months=months,
            annual_interest_rate=annual_rate,
            effective_monthly_rate=monthly_rate
        )

    def generate_amortization(
        self,
        principal: float,
        annual_rate: float,
        months: int
    ) -> pd.DataFrame:
        """使用向量化操作生成摊销表 (更高效)"""
        monthly_rate = annual_rate / 12
        payment = npf.pmt(monthly_rate, months, -principal)

        periods = np.arange(1, months + 1)

        # 向量化计算 - 比循环快得多
        interest = npf.ipmt(monthly_rate, periods, months, -principal)
        principal_paid = npf.ppmt(monthly_rate, periods, months, -principal)
        balance = npf.fv(monthly_rate, periods, payment, -principal)

        return pd.DataFrame({
            'month': periods,
            'payment': payment,
            'principal': principal_paid,
            'interest': interest,
            'balance': np.maximum(0, balance)
        })

    def calculate_max_loan(
        self,
        monthly_income: float,
        annual_rate: float,
        months: int,
        existing_debt: float = 0
    ) -> float:
        """计算最大可贷款额"""
        max_payment = monthly_income * self.max_dti_ratio - existing_debt

        if max_payment <= 0:
            return 0

        # npf.pv 直接计算现值（最大本金）
        return npf.pv(annual_rate / 12, months, -max_payment)
```

---

## 学习检查清单

### Phase 1: numpy-financial 基础
- [ ] 安装 numpy-financial: `pip install numpy-financial`
- [ ] 掌握 `pmt()` 月供计算
- [ ] 掌握 `ipmt()` / `ppmt()` 利息/本金分解
- [ ] 掌握 `pv()` / `fv()` 现值/终值计算
- [ ] 掌握 `nper()` / `rate()` 期数/利率反算
- [ ] 对比你的代码与 npf 结果一致性

### Phase 2: 高级金融计算
- [ ] 理解 NPV 净现值
- [ ] 理解 IRR 内部收益率
- [ ] 实现贷款定价模型
- [ ] 了解 MIRR 修正内部收益率

### Phase 3: 银行业概念
- [ ] 掌握 DTI, LTV 比率
- [ ] 了解 PD, LGD, EAD 风险指标
- [ ] 了解巴塞尔协议基础
- [ ] 理解信用评分卡原理

### Phase 4: 职业发展
- [ ] 评估 CFA vs FRM 路径
- [ ] 完成 CFA Python PSM 模块
- [ ] 学习 scikit-learn 信用建模
- [ ] 探索 QuantLib 基础

---

## 参考资源

- [numpy-financial 官方文档](https://numpy.org/numpy-financial/)
- [CFA Python Programming Fundamentals](https://www.cfainstitute.org/programs/cfa-program/candidate-resources/practical-skills-modules/python-programming-fundamentals)
- [Building a Financial Model with Pandas](https://pbpython.com/amortization-model.html)
- [GARP FRM Certification](https://www.garp.org/frm)

---

*Created: 2025-12-01*
*Project: personal-loan-advisor-agent*
