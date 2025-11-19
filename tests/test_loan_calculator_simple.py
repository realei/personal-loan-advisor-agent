"""
简单的LoanCalculatorTool单元测试
展示基本的测试场景和边界情况
"""

import pytest
from src.tools.loan_calculator import LoanCalculatorTool, LoanRequest


class TestLoanCalculatorBasics:
    """基础贷款计算测试"""

    @pytest.fixture
    def calculator(self):
        """创建计算器实例"""
        return LoanCalculatorTool(max_dti_ratio=0.43)

    def test_basic_monthly_payment_calculation(self, calculator):
        """测试基本月供计算 - 最常见场景"""
        # Given: 5万贷款，5%年利率，3年期
        loan_request = LoanRequest(
            loan_amount=50000,
            annual_interest_rate=0.05,
            loan_term_months=36
        )

        # When: 计算月供
        result = calculator.calculate_monthly_payment(loan_request)

        # Then: 验证结果
        assert result.monthly_payment > 0
        assert result.total_payment > result.total_principal
        assert result.total_interest > 0
        assert result.total_principal == 50000
        assert result.loan_term_months == 36

        # 验证数学正确性：总支付 = 本金 + 利息
        assert abs(result.total_payment - (result.total_principal + result.total_interest)) < 0.01

    def test_zero_interest_rate(self, calculator):
        """测试零利率贷款 - 边界情况"""
        # Given: 无息贷款
        loan_request = LoanRequest(
            loan_amount=12000,
            annual_interest_rate=0.0,
            loan_term_months=12
        )

        result = calculator.calculate_monthly_payment(loan_request)

        # Then: 月供应该等于本金除以月数
        expected_payment = 12000 / 12
        assert abs(result.monthly_payment - expected_payment) < 0.01
        assert result.total_interest == 0
        assert result.total_payment == result.total_principal

    def test_higher_interest_means_higher_payment(self, calculator):
        """测试利率越高，月供越高 - 业务逻辑验证"""
        # Given: 相同本金和期限，不同利率
        low_rate = LoanRequest(
            loan_amount=50000,
            annual_interest_rate=0.03,
            loan_term_months=36
        )

        high_rate = LoanRequest(
            loan_amount=50000,
            annual_interest_rate=0.10,
            loan_term_months=36
        )

        low_result = calculator.calculate_monthly_payment(low_rate)
        high_result = calculator.calculate_monthly_payment(high_rate)

        # Then: 高利率的月供应该更高
        assert high_result.monthly_payment > low_result.monthly_payment
        assert high_result.total_interest > low_result.total_interest

    def test_longer_term_means_lower_monthly_payment(self, calculator):
        """测试期限越长，月供越低 - 业务逻辑验证"""
        # Given: 相同本金和利率，不同期限
        short_term = LoanRequest(
            loan_amount=50000,
            annual_interest_rate=0.05,
            loan_term_months=24
        )

        long_term = LoanRequest(
            loan_amount=50000,
            annual_interest_rate=0.05,
            loan_term_months=60
        )

        short_result = calculator.calculate_monthly_payment(short_term)
        long_result = calculator.calculate_monthly_payment(long_term)

        # Then: 长期限的月供应该更低（但总利息更高）
        assert long_result.monthly_payment < short_result.monthly_payment
        assert long_result.total_interest > short_result.total_interest


class TestLoanCalculatorEdgeCases:
    """边界情况和错误处理测试"""

    @pytest.fixture
    def calculator(self):
        return LoanCalculatorTool(max_dti_ratio=0.43)

    def test_very_small_loan_amount(self, calculator):
        """测试极小贷款金额"""
        loan_request = LoanRequest(
            loan_amount=100,
            annual_interest_rate=0.05,
            loan_term_months=12
        )

        result = calculator.calculate_monthly_payment(loan_request)

        assert result.monthly_payment > 0
        assert result.monthly_payment < 10  # 应该很小

    def test_very_large_loan_amount(self, calculator):
        """测试大额贷款"""
        loan_request = LoanRequest(
            loan_amount=1000000,
            annual_interest_rate=0.04,
            loan_term_months=360  # 30年
        )

        result = calculator.calculate_monthly_payment(loan_request)

        assert result.monthly_payment > 0
        assert result.total_payment > result.total_principal

    def test_invalid_negative_amount(self):
        """测试负数贷款金额 - 应该失败"""
        with pytest.raises(Exception):  # Pydantic会抛出ValidationError
            LoanRequest(
                loan_amount=-50000,
                annual_interest_rate=0.05,
                loan_term_months=36
            )

    def test_invalid_negative_rate(self):
        """测试负利率 - 应该失败"""
        with pytest.raises(Exception):
            LoanRequest(
                loan_amount=50000,
                annual_interest_rate=-0.05,
                loan_term_months=36
            )

    def test_invalid_zero_term(self):
        """测试零期限 - 应该失败"""
        with pytest.raises(Exception):
            LoanRequest(
                loan_amount=50000,
                annual_interest_rate=0.05,
                loan_term_months=0
            )


class TestAffordabilityCheck:
    """贷款可负担性检查测试"""

    @pytest.fixture
    def calculator(self):
        return LoanCalculatorTool(max_dti_ratio=0.43)

    def test_affordable_loan(self, calculator):
        """测试可负担的贷款 - 通过DTI检查"""
        loan_request = LoanRequest(
            loan_amount=50000,
            annual_interest_rate=0.05,
            loan_term_months=36,
            monthly_income=10000
        )

        result = calculator.check_affordability(
            loan_request,
            existing_monthly_debt=1000
        )

        # 月供约$1,498，加上已有债务$1,000 = $2,498
        # DTI = 2498 / 10000 = 24.98% < 43%
        assert result["affordable"] is True
        assert result["dti_ratio"] < 0.43

    def test_unaffordable_loan(self, calculator):
        """测试不可负担的贷款 - DTI过高"""
        loan_request = LoanRequest(
            loan_amount=100000,
            annual_interest_rate=0.08,
            loan_term_months=36,
            monthly_income=5000
        )

        result = calculator.check_affordability(
            loan_request,
            existing_monthly_debt=1000
        )

        # 高额贷款 + 低收入 = DTI过高
        assert result["affordable"] is False
        assert result["dti_ratio"] > 0.43

    def test_zero_existing_debt(self, calculator):
        """测试无现有债务的情况"""
        loan_request = LoanRequest(
            loan_amount=30000,
            annual_interest_rate=0.05,
            loan_term_months=36,
            monthly_income=8000
        )

        result = calculator.check_affordability(loan_request, existing_monthly_debt=0)

        # 只考虑新贷款的月供
        assert result["affordable"] is True
        assert result["existing_debt"] == 0


class TestAmortizationSchedule:
    """还款计划测试"""

    @pytest.fixture
    def calculator(self):
        return LoanCalculatorTool(max_dti_ratio=0.43)

    def test_schedule_length(self, calculator):
        """测试还款计划的长度正确"""
        loan_request = LoanRequest(
            loan_amount=50000,
            annual_interest_rate=0.05,
            loan_term_months=36
        )

        schedule = calculator.generate_amortization_schedule(loan_request)

        # 应该有36期还款
        assert len(schedule.schedule) == 36

    def test_schedule_balance_decreases(self, calculator):
        """测试每期余额递减"""
        loan_request = LoanRequest(
            loan_amount=50000,
            annual_interest_rate=0.05,
            loan_term_months=36
        )

        schedule = calculator.generate_amortization_schedule(loan_request)
        df = schedule.schedule

        # 第一期余额应该接近本金
        assert df.iloc[0]["balance"] < 50000

        # 最后一期余额应该接近0
        assert df.iloc[-1]["balance"] < 1.0

        # 余额应该逐期递减
        for i in range(len(df) - 1):
            assert df.iloc[i]["balance"] > df.iloc[i + 1]["balance"]

    def test_schedule_principal_increases(self, calculator):
        """测试本金占比逐期增加"""
        loan_request = LoanRequest(
            loan_amount=50000,
            annual_interest_rate=0.05,
            loan_term_months=36
        )

        schedule = calculator.generate_amortization_schedule(loan_request)
        df = schedule.schedule

        # 前期利息占比高，后期本金占比高
        first_month_principal = df.iloc[0]["principal"]
        last_month_principal = df.iloc[-1]["principal"]

        assert last_month_principal > first_month_principal

    def test_total_payments_match(self, calculator):
        """测试所有月供总和等于总支付额"""
        loan_request = LoanRequest(
            loan_amount=50000,
            annual_interest_rate=0.05,
            loan_term_months=36
        )

        schedule = calculator.generate_amortization_schedule(loan_request)
        df = schedule.schedule
        total_from_schedule = df["payment"].sum()

        # 应该等于summary中的总支付额
        assert abs(total_from_schedule - schedule.summary.total_payment) < 1.0


if __name__ == "__main__":
    # 可以直接运行此文件进行测试
    pytest.main([__file__, "-v", "-s"])
