"""
Simple unit tests for LoanCalculatorTool
Demonstrates basic test scenarios and edge cases
"""

import pytest
from src.tools.loan_calculator import LoanCalculatorTool, LoanRequest


class TestLoanCalculatorBasics:
    """Basic loan calculation tests"""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance"""
        return LoanCalculatorTool(max_dti_ratio=0.43)

    def test_basic_monthly_payment_calculation(self, calculator):
        """Test basic monthly payment calculation - most common scenario"""
        # Given: $50,000 loan, 5% annual interest rate, 3 year term
        loan_request = LoanRequest(
            loan_amount=50000,
            annual_interest_rate=0.05,
            loan_term_months=36
        )

        # When: Calculate monthly payment
        result = calculator.calculate_monthly_payment(loan_request)

        # Then: Verify results
        assert result.monthly_payment > 0
        assert result.total_payment > result.total_principal
        assert result.total_interest > 0
        assert result.total_principal == 50000
        assert result.loan_term_months == 36

        # Verify mathematical correctness: total payment = principal + interest
        assert abs(result.total_payment - (result.total_principal + result.total_interest)) < 0.01

    def test_zero_interest_rate(self, calculator):
        """Test zero interest rate loan - edge case"""
        # Given: Interest-free loan
        loan_request = LoanRequest(
            loan_amount=12000,
            annual_interest_rate=0.0,
            loan_term_months=12
        )

        result = calculator.calculate_monthly_payment(loan_request)

        # Then: Monthly payment should equal principal divided by number of months
        expected_payment = 12000 / 12
        assert abs(result.monthly_payment - expected_payment) < 0.01
        assert result.total_interest == 0
        assert result.total_payment == result.total_principal

    def test_higher_interest_means_higher_payment(self, calculator):
        """Test higher interest rate means higher payment - business logic verification"""
        # Given: Same principal and term, different interest rates
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

        # Then: Higher interest rate should result in higher monthly payment
        assert high_result.monthly_payment > low_result.monthly_payment
        assert high_result.total_interest > low_result.total_interest

    def test_longer_term_means_lower_monthly_payment(self, calculator):
        """Test longer term means lower monthly payment - business logic verification"""
        # Given: Same principal and interest rate, different terms
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

        # Then: Longer term should result in lower monthly payment (but higher total interest)
        assert long_result.monthly_payment < short_result.monthly_payment
        assert long_result.total_interest > short_result.total_interest


class TestLoanCalculatorEdgeCases:
    """Edge cases and error handling tests"""

    @pytest.fixture
    def calculator(self):
        return LoanCalculatorTool(max_dti_ratio=0.43)

    def test_very_small_loan_amount(self, calculator):
        """Test very small loan amount"""
        loan_request = LoanRequest(
            loan_amount=100,
            annual_interest_rate=0.05,
            loan_term_months=12
        )

        result = calculator.calculate_monthly_payment(loan_request)

        assert result.monthly_payment > 0
        assert result.monthly_payment < 10  # Should be very small

    def test_very_large_loan_amount(self, calculator):
        """Test large loan amount"""
        loan_request = LoanRequest(
            loan_amount=1000000,
            annual_interest_rate=0.04,
            loan_term_months=360  # 30 years
        )

        result = calculator.calculate_monthly_payment(loan_request)

        assert result.monthly_payment > 0
        assert result.total_payment > result.total_principal

    def test_invalid_negative_amount(self):
        """Test negative loan amount - should fail"""
        with pytest.raises(Exception):  # Pydantic will raise ValidationError
            LoanRequest(
                loan_amount=-50000,
                annual_interest_rate=0.05,
                loan_term_months=36
            )

    def test_invalid_negative_rate(self):
        """Test negative interest rate - should fail"""
        with pytest.raises(Exception):
            LoanRequest(
                loan_amount=50000,
                annual_interest_rate=-0.05,
                loan_term_months=36
            )

    def test_invalid_zero_term(self):
        """Test zero term - should fail"""
        with pytest.raises(Exception):
            LoanRequest(
                loan_amount=50000,
                annual_interest_rate=0.05,
                loan_term_months=0
            )


class TestAffordabilityCheck:
    """Loan affordability check tests"""

    @pytest.fixture
    def calculator(self):
        return LoanCalculatorTool(max_dti_ratio=0.43)

    def test_affordable_loan(self, calculator):
        """Test affordable loan - passes DTI check"""
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

        # Monthly payment approx $1,498, plus existing debt $1,000 = $2,498
        # DTI = 2498 / 10000 = 24.98% < 43%
        assert result["affordable"] is True
        assert result["dti_ratio"] < 0.43

    def test_unaffordable_loan(self, calculator):
        """Test unaffordable loan - DTI too high"""
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

        # High loan amount + low income = DTI too high
        assert result["affordable"] is False
        assert result["dti_ratio"] > 0.43

    def test_zero_existing_debt(self, calculator):
        """Test case with no existing debt"""
        loan_request = LoanRequest(
            loan_amount=30000,
            annual_interest_rate=0.05,
            loan_term_months=36,
            monthly_income=8000
        )

        result = calculator.check_affordability(loan_request, existing_monthly_debt=0)

        # Only consider monthly payment for new loan
        assert result["affordable"] is True
        assert result["existing_debt"] == 0


class TestAmortizationSchedule:
    """Payment schedule tests"""

    @pytest.fixture
    def calculator(self):
        return LoanCalculatorTool(max_dti_ratio=0.43)

    def test_schedule_length(self, calculator):
        """Test payment schedule has correct length"""
        loan_request = LoanRequest(
            loan_amount=50000,
            annual_interest_rate=0.05,
            loan_term_months=36
        )

        schedule = calculator.generate_amortization_schedule(loan_request)

        # Should have 36 payments
        assert len(schedule.schedule) == 36

    def test_schedule_balance_decreases(self, calculator):
        """Test balance decreases each period"""
        loan_request = LoanRequest(
            loan_amount=50000,
            annual_interest_rate=0.05,
            loan_term_months=36
        )

        schedule = calculator.generate_amortization_schedule(loan_request)
        df = schedule.schedule

        # First period balance should be close to principal
        assert df.iloc[0]["balance"] < 50000

        # Last period balance should be close to 0
        assert df.iloc[-1]["balance"] < 1.0

        # Balance should decrease each period
        for i in range(len(df) - 1):
            assert df.iloc[i]["balance"] > df.iloc[i + 1]["balance"]

    def test_schedule_principal_increases(self, calculator):
        """Test principal portion increases each period"""
        loan_request = LoanRequest(
            loan_amount=50000,
            annual_interest_rate=0.05,
            loan_term_months=36
        )

        schedule = calculator.generate_amortization_schedule(loan_request)
        df = schedule.schedule

        # Early periods have higher interest, later periods have higher principal
        first_month_principal = df.iloc[0]["principal"]
        last_month_principal = df.iloc[-1]["principal"]

        assert last_month_principal > first_month_principal

    def test_total_payments_match(self, calculator):
        """Test sum of all monthly payments equals total payment amount"""
        loan_request = LoanRequest(
            loan_amount=50000,
            annual_interest_rate=0.05,
            loan_term_months=36
        )

        schedule = calculator.generate_amortization_schedule(loan_request)
        df = schedule.schedule
        total_from_schedule = df["payment"].sum()

        # Should equal total payment in summary
        assert abs(total_from_schedule - schedule.summary.total_payment) < 1.0


if __name__ == "__main__":
    # Can run this file directly for testing
    pytest.main([__file__, "-v", "-s"])
