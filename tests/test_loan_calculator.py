"""Unit tests for LoanCalculatorTool."""

import pytest
import pandas as pd

from src.tools.loan_calculator import LoanCalculatorTool, LoanRequest


class TestLoanCalculatorTool:
    """Test suite for LoanCalculatorTool."""

    @pytest.fixture
    def calculator(self):
        """Create LoanCalculatorTool instance."""
        return LoanCalculatorTool(max_dti_ratio=0.5)

    @pytest.fixture
    def standard_loan(self):
        """Standard loan request for testing."""
        return LoanRequest(
            loan_amount=50000.0,
            annual_interest_rate=0.05,  # 5% annual
            loan_term_months=36,
            monthly_income=10000.0,
        )

    def test_monthly_payment_calculation(self, calculator, standard_loan):
        """Test EMI calculation accuracy."""
        result = calculator.calculate_monthly_payment(standard_loan)

        # Expected monthly payment for 50k at 5% for 36 months
        # Using online calculator: ~$1498.88
        assert 1498 < result.monthly_payment < 1500
        assert result.loan_term_months == 36
        assert result.annual_interest_rate == 0.05

    def test_total_interest_calculation(self, calculator, standard_loan):
        """Test total interest calculation."""
        result = calculator.calculate_monthly_payment(standard_loan)

        # Total payment should be monthly payment * months
        assert abs(result.total_payment - (result.monthly_payment * 36)) < 0.01

        # Total interest should be total payment - principal
        assert abs(result.total_interest - (result.total_payment - 50000)) < 0.01

        # Total interest should be positive
        assert result.total_interest > 0

    def test_zero_interest_loan(self, calculator):
        """Test calculation with 0% interest."""
        loan = LoanRequest(
            loan_amount=12000.0, annual_interest_rate=0.0, loan_term_months=12
        )

        result = calculator.calculate_monthly_payment(loan)

        # With 0% interest, monthly payment should be exactly principal / months
        assert abs(result.monthly_payment - 1000.0) < 0.01
        assert abs(result.total_interest) < 0.01

    def test_amortization_schedule_length(self, calculator, standard_loan):
        """Test amortization schedule has correct number of rows."""
        schedule = calculator.generate_amortization_schedule(standard_loan)

        assert len(schedule.schedule) == 36
        assert isinstance(schedule.schedule, pd.DataFrame)

    def test_amortization_schedule_columns(self, calculator, standard_loan):
        """Test amortization schedule has required columns."""
        schedule = calculator.generate_amortization_schedule(standard_loan)

        required_cols = ["month", "payment", "principal", "interest", "balance"]
        for col in required_cols:
            assert col in schedule.schedule.columns

    def test_amortization_balance_decreases(self, calculator, standard_loan):
        """Test that balance decreases monotonically."""
        schedule = calculator.generate_amortization_schedule(standard_loan)

        balances = schedule.schedule["balance"].tolist()

        # Balance should decrease each month
        for i in range(len(balances) - 1):
            assert balances[i] >= balances[i + 1]

        # Final balance should be zero (or very close due to rounding)
        assert abs(balances[-1]) < 0.01

    def test_amortization_total_principal(self, calculator, standard_loan):
        """Test that total principal payments equal loan amount."""
        schedule = calculator.generate_amortization_schedule(standard_loan)

        total_principal = schedule.schedule["principal"].sum()

        assert abs(total_principal - standard_loan.loan_amount) < 1.0

    def test_amortization_total_interest(self, calculator, standard_loan):
        """Test that total interest matches calculation."""
        schedule = calculator.generate_amortization_schedule(standard_loan)

        total_interest_schedule = schedule.schedule["interest"].sum()
        total_interest_calc = schedule.summary.total_interest

        assert abs(total_interest_schedule - total_interest_calc) < 1.0

    def test_affordability_check_affordable(self, calculator, standard_loan):
        """Test affordability check for affordable loan."""
        result = calculator.check_affordability(standard_loan, existing_monthly_debt=1000.0)

        assert result["affordable"] is True
        assert result["dti_ratio"] < 0.5
        assert "monthly_payment" in result
        assert "message" in result

    def test_affordability_check_not_affordable(self, calculator):
        """Test affordability check for unaffordable loan."""
        loan = LoanRequest(
            loan_amount=100000.0,
            annual_interest_rate=0.05,
            loan_term_months=24,
            monthly_income=5000.0,
        )

        result = calculator.check_affordability(loan, existing_monthly_debt=1000.0)

        assert result["affordable"] is False
        assert result["dti_ratio"] > 0.5

    def test_affordability_without_income(self, calculator):
        """Test affordability check without income."""
        loan = LoanRequest(
            loan_amount=50000.0,
            annual_interest_rate=0.05,
            loan_term_months=36,
            # monthly_income is None
        )

        result = calculator.check_affordability(loan)

        assert result["affordable"] is None
        assert "income required" in result["message"].lower()

    def test_compare_loan_options(self, calculator):
        """Test comparison of different loan terms."""
        comparison = calculator.compare_loan_options(
            loan_amount=50000.0, annual_rate=0.05, terms=[24, 36, 48, 60]
        )

        assert len(comparison) == 4
        assert "term_months" in comparison.columns
        assert "monthly_payment" in comparison.columns
        assert "total_interest" in comparison.columns

        # Longer terms should have lower monthly payments but higher total interest
        assert comparison.iloc[0]["monthly_payment"] > comparison.iloc[-1]["monthly_payment"]
        assert comparison.iloc[0]["total_interest"] < comparison.iloc[-1]["total_interest"]

    def test_calculate_max_loan_amount(self, calculator):
        """Test maximum affordable loan calculation."""
        result = calculator.calculate_max_loan_amount(
            monthly_income=10000.0,
            annual_interest_rate=0.05,
            loan_term_months=36,
            existing_monthly_debt=1000.0,
        )

        assert result["max_loan_amount"] > 0
        assert result["max_monthly_payment"] > 0
        assert result["dti_ratio"] == 0.5

        # Verify that the calculated amount is actually affordable
        loan_request = LoanRequest(
            loan_amount=result["max_loan_amount"],
            annual_interest_rate=0.05,
            loan_term_months=36,
            monthly_income=10000.0,
        )

        calc = calculator.calculate_monthly_payment(loan_request)
        total_debt = calc.monthly_payment + 1000.0
        dti = total_debt / 10000.0

        assert abs(dti - 0.5) < 0.01  # Should be exactly at max DTI

    def test_calculate_max_loan_with_high_existing_debt(self, calculator):
        """Test max loan calculation with high existing debt."""
        result = calculator.calculate_max_loan_amount(
            monthly_income=5000.0,
            annual_interest_rate=0.05,
            loan_term_months=36,
            existing_monthly_debt=3000.0,  # Already 60% DTI
        )

        assert result["max_loan_amount"] == 0
        assert "exceeds" in result["message"].lower()

    def test_different_interest_rates(self, calculator):
        """Test that higher interest rates result in higher payments."""
        loan_low = LoanRequest(
            loan_amount=50000.0, annual_interest_rate=0.03, loan_term_months=36
        )
        loan_high = LoanRequest(
            loan_amount=50000.0, annual_interest_rate=0.10, loan_term_months=36
        )

        calc_low = calculator.calculate_monthly_payment(loan_low)
        calc_high = calculator.calculate_monthly_payment(loan_high)

        assert calc_high.monthly_payment > calc_low.monthly_payment
        assert calc_high.total_interest > calc_low.total_interest

    def test_different_loan_terms(self, calculator):
        """Test that longer terms result in lower monthly payments."""
        loan_short = LoanRequest(
            loan_amount=50000.0, annual_interest_rate=0.05, loan_term_months=24
        )
        loan_long = LoanRequest(
            loan_amount=50000.0, annual_interest_rate=0.05, loan_term_months=60
        )

        calc_short = calculator.calculate_monthly_payment(loan_short)
        calc_long = calculator.calculate_monthly_payment(loan_long)

        assert calc_short.monthly_payment > calc_long.monthly_payment
        assert calc_short.total_interest < calc_long.total_interest


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
