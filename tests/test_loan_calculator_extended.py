"""Unit tests for extended loan calculator functions.

Tests mortgage, auto loan, and early payoff calculator functions.
These tests complement test_loan_calculator_simple.py which tests
the basic LoanCalculatorTool class.

Follows pytest best practices:
- Parametrized tests for rule-based scenarios
- Fixtures for reusable test data
- Clear separation of concerns
"""

import pytest
import pandas as pd
from src.tools.loan_calculator import (
    calculate_home_affordability,
    calculate_mortgage_payment,
    calculate_car_loan,
    compare_car_loan_terms,
    calculate_early_payoff,
    get_calculator,
    LoanCalculatorTool,
)
from src.tools.loan_types import LoanType


# =============================================================================
# TEST CONSTANTS
# =============================================================================

STANDARD_INCOME = 20_000
STANDARD_HOME_PRICE = 2_000_000
STANDARD_CAR_PRICE = 150_000


# =============================================================================
# HOME AFFORDABILITY TESTS
# =============================================================================

class TestHomeAffordability:
    """Tests for calculate_home_affordability function."""

    def test_basic_calculation_returns_expected_fields(self):
        """Basic calculation should return all expected fields."""
        result = calculate_home_affordability(monthly_income=STANDARD_INCOME)

        expected_fields = [
            "affordable",
            "max_home_price",
            "max_loan_amount",
            "required_down_payment",
            "down_payment_percentage",
            "monthly_payment",
            "ltv_ratio",
            "dti_ratio",
            "residency",
            "property_type",
            "message",
        ]
        for field in expected_fields:
            assert field in result, f"Missing field: {field}"

    def test_basic_calculation_is_affordable(self):
        """Standard income should result in affordable calculation."""
        result = calculate_home_affordability(monthly_income=STANDARD_INCOME)

        assert result["affordable"] is True
        assert result["max_home_price"] > 0
        assert result["max_loan_amount"] > 0

    @pytest.mark.parametrize("residency,property_type,expected_ltv", [
        pytest.param("citizen", "first", 0.85, id="citizen-first-85pct"),
        pytest.param("expat", "first", 0.80, id="expat-first-80pct"),
        pytest.param("expat", "second", 0.65, id="expat-second-65pct"),
        pytest.param("non_resident", "first", 0.50, id="non-resident-50pct"),
    ])
    def test_ltv_varies_by_residency_and_property_type(
        self, residency, property_type, expected_ltv
    ):
        """LTV ratio should correctly vary by residency and property type."""
        result = calculate_home_affordability(
            monthly_income=STANDARD_INCOME,
            residency=residency,
            property_type=property_type,
        )

        assert result["ltv_ratio"] == expected_ltv

    def test_down_payment_percentage_consistent_with_ltv(self):
        """Down payment percentage should equal 1 - LTV."""
        result = calculate_home_affordability(
            monthly_income=STANDARD_INCOME,
            residency="expat",
            property_type="first",
        )

        expected_down_pct = 1.0 - result["ltv_ratio"]
        assert abs(result["down_payment_percentage"] - expected_down_pct) < 0.01

    def test_high_existing_debt_returns_unaffordable(self):
        """High existing debt should result in unaffordable status."""
        result = calculate_home_affordability(
            monthly_income=STANDARD_INCOME,
            existing_debt_payment=15_000,  # 75% of income
        )

        assert result["affordable"] is False
        assert result["max_home_price"] == 0

    def test_residency_and_property_type_in_result(self):
        """Result should include residency and property type used."""
        result = calculate_home_affordability(
            monthly_income=STANDARD_INCOME,
            residency="citizen",
            property_type="second",
        )

        assert result["residency"] == "citizen"
        assert result["property_type"] == "second"

    def test_higher_income_means_higher_affordability(self):
        """Higher income should result in higher max home price."""
        low_income = calculate_home_affordability(monthly_income=10_000)
        high_income = calculate_home_affordability(monthly_income=30_000)

        assert high_income["max_home_price"] > low_income["max_home_price"]


# =============================================================================
# MORTGAGE PAYMENT TESTS
# =============================================================================

class TestMortgagePayment:
    """Tests for calculate_mortgage_payment function."""

    def test_valid_calculation_returns_expected_fields(self):
        """Valid calculation should return all expected fields."""
        result = calculate_mortgage_payment(
            home_price=STANDARD_HOME_PRICE,
            residency="expat",
            property_type="first",
        )

        expected_fields = [
            "valid",
            "home_price",
            "down_payment",
            "loan_amount",
            "ltv_ratio",
            "monthly_payment",
            "total_payment",
            "total_interest",
        ]
        for field in expected_fields:
            assert field in result, f"Missing field: {field}"

    def test_valid_calculation_with_minimum_down_payment(self):
        """Calculation with minimum down payment should be valid."""
        result = calculate_mortgage_payment(
            home_price=STANDARD_HOME_PRICE,
            residency="expat",
            property_type="first",
        )

        assert result["valid"] is True
        assert result["home_price"] == STANDARD_HOME_PRICE
        assert result["monthly_payment"] > 0

    def test_insufficient_down_payment_returns_invalid(self):
        """Insufficient down payment should return invalid result."""
        # Expat needs 20% down, try with only 10%
        result = calculate_mortgage_payment(
            home_price=STANDARD_HOME_PRICE,
            down_payment=STANDARD_HOME_PRICE * 0.10,
            residency="expat",
            property_type="first",
        )

        assert result["valid"] is False
        assert "LTV" in result["message"]

    @pytest.mark.parametrize("residency,property_type,min_down_pct", [
        pytest.param("citizen", "first", 0.15, id="citizen-15pct"),
        pytest.param("expat", "first", 0.20, id="expat-20pct"),
        pytest.param("expat", "second", 0.35, id="expat-second-35pct"),
        pytest.param("non_resident", "first", 0.50, id="non-resident-50pct"),
    ])
    def test_minimum_down_payment_accepted(
        self, residency, property_type, min_down_pct
    ):
        """Minimum down payment for each status should be accepted."""
        result = calculate_mortgage_payment(
            home_price=STANDARD_HOME_PRICE,
            down_payment=STANDARD_HOME_PRICE * min_down_pct,
            residency=residency,
            property_type=property_type,
        )

        assert result["valid"] is True

    def test_ltv_ratio_calculated_correctly(self):
        """LTV ratio should be (home_price - down_payment) / home_price."""
        down_payment = 500_000  # 25% down on 2M
        result = calculate_mortgage_payment(
            home_price=STANDARD_HOME_PRICE,
            down_payment=down_payment,
            residency="expat",
            property_type="first",
        )

        expected_ltv = (STANDARD_HOME_PRICE - down_payment) / STANDARD_HOME_PRICE
        assert abs(result["ltv_ratio"] - expected_ltv) < 0.001

    def test_larger_down_payment_reduces_monthly_payment(self):
        """Larger down payment should reduce monthly payment."""
        min_down = calculate_mortgage_payment(
            home_price=STANDARD_HOME_PRICE,
            down_payment=STANDARD_HOME_PRICE * 0.20,
            residency="expat",
        )
        large_down = calculate_mortgage_payment(
            home_price=STANDARD_HOME_PRICE,
            down_payment=STANDARD_HOME_PRICE * 0.40,
            residency="expat",
        )

        assert large_down["monthly_payment"] < min_down["monthly_payment"]

    def test_total_interest_calculated(self):
        """Total interest should be total_payment - loan_amount."""
        result = calculate_mortgage_payment(
            home_price=STANDARD_HOME_PRICE,
            residency="expat",
        )

        expected_interest = result["total_payment"] - result["loan_amount"]
        assert abs(result["total_interest"] - expected_interest) < 1.0


# =============================================================================
# CAR LOAN TESTS
# =============================================================================

class TestCarLoan:
    """Tests for calculate_car_loan function."""

    def test_valid_calculation_returns_expected_fields(self):
        """Valid calculation should return all expected fields."""
        result = calculate_car_loan(car_price=STANDARD_CAR_PRICE)

        expected_fields = [
            "valid",
            "car_price",
            "down_payment",
            "loan_amount",
            "ltv_ratio",
            "monthly_payment",
            "total_payment",
            "total_interest",
        ]
        for field in expected_fields:
            assert field in result, f"Missing field: {field}"

    def test_valid_calculation_with_default_down_payment(self):
        """Calculation with default down payment should be valid."""
        result = calculate_car_loan(car_price=STANDARD_CAR_PRICE)

        assert result["valid"] is True
        assert result["car_price"] == STANDARD_CAR_PRICE
        assert result["monthly_payment"] > 0

    def test_insufficient_down_payment_returns_invalid(self):
        """Insufficient down payment should return invalid result."""
        result = calculate_car_loan(
            car_price=STANDARD_CAR_PRICE,
            down_payment=1_000,  # Way too low
        )

        assert result["valid"] is False
        assert "LTV" in result["message"]

    def test_custom_down_payment_accepted(self):
        """Custom down payment above minimum should be accepted."""
        result = calculate_car_loan(
            car_price=STANDARD_CAR_PRICE,
            down_payment=50_000,
        )

        assert result["valid"] is True
        assert result["down_payment"] == 50_000

    def test_loan_amount_equals_price_minus_down_payment(self):
        """Loan amount should equal car price minus down payment."""
        down_payment = 30_000
        result = calculate_car_loan(
            car_price=STANDARD_CAR_PRICE,
            down_payment=down_payment,
        )

        assert result["loan_amount"] == STANDARD_CAR_PRICE - down_payment


class TestCompareCarLoanTerms:
    """Tests for compare_car_loan_terms function."""

    def test_returns_dataframe(self):
        """Comparison should return a pandas DataFrame."""
        result = compare_car_loan_terms(car_price=100_000)

        assert isinstance(result, pd.DataFrame)

    def test_default_terms_36_48_60_72(self):
        """Default terms should be 36, 48, 60, 72 months."""
        result = compare_car_loan_terms(car_price=100_000)

        assert list(result["term_months"]) == [36, 48, 60, 72]

    def test_custom_terms_used(self):
        """Custom terms should be used when provided."""
        custom_terms = [24, 36, 48]
        result = compare_car_loan_terms(car_price=100_000, terms=custom_terms)

        assert list(result["term_months"]) == custom_terms

    def test_dataframe_has_expected_columns(self):
        """DataFrame should have expected columns."""
        result = compare_car_loan_terms(car_price=100_000)

        expected_columns = [
            "term_months",
            "term_years",
            "monthly_payment",
            "total_payment",
            "total_interest",
            "interest_percentage",
        ]
        for col in expected_columns:
            assert col in result.columns, f"Missing column: {col}"

    def test_shorter_term_higher_payment_less_interest(self):
        """Shorter term should mean higher monthly payment but less total interest."""
        result = compare_car_loan_terms(car_price=100_000)

        short_term = result[result["term_months"] == 36].iloc[0]
        long_term = result[result["term_months"] == 72].iloc[0]

        assert short_term["monthly_payment"] > long_term["monthly_payment"]
        assert short_term["total_interest"] < long_term["total_interest"]


# =============================================================================
# EARLY PAYOFF TESTS
# =============================================================================

class TestEarlyPayoff:
    """Tests for calculate_early_payoff function."""

    @pytest.fixture
    def standard_loan_params(self):
        """Standard loan parameters for early payoff testing."""
        return {
            "loan_amount": 200_000,
            "annual_interest_rate": 0.05,
            "loan_term_months": 360,  # 30 years
        }

    def test_returns_expected_fields(self, standard_loan_params):
        """Result should contain all expected fields."""
        result = calculate_early_payoff(
            **standard_loan_params,
            extra_monthly_payment=200,
        )

        expected_fields = [
            "original_term_months",
            "new_term_months",
            "months_saved",
            "years_saved",
            "original_monthly_payment",
            "new_monthly_payment",
            "extra_monthly_payment",
            "original_total_interest",
            "new_total_interest",
            "interest_saved",
            "message",
        ]
        for field in expected_fields:
            assert field in result, f"Missing field: {field}"

    def test_extra_payment_saves_interest(self, standard_loan_params):
        """Extra payment should result in interest savings."""
        result = calculate_early_payoff(
            **standard_loan_params,
            extra_monthly_payment=200,
        )

        assert result["interest_saved"] > 0
        assert result["new_total_interest"] < result["original_total_interest"]

    def test_extra_payment_reduces_term(self, standard_loan_params):
        """Extra payment should reduce loan term."""
        result = calculate_early_payoff(
            **standard_loan_params,
            extra_monthly_payment=200,
        )

        assert result["months_saved"] > 0
        assert result["new_term_months"] < result["original_term_months"]

    def test_larger_extra_payment_saves_more(self, standard_loan_params):
        """Larger extra payment should save more interest and time."""
        small_extra = calculate_early_payoff(
            **standard_loan_params,
            extra_monthly_payment=100,
        )
        large_extra = calculate_early_payoff(
            **standard_loan_params,
            extra_monthly_payment=500,
        )

        assert large_extra["interest_saved"] > small_extra["interest_saved"]
        assert large_extra["months_saved"] > small_extra["months_saved"]

    def test_new_monthly_payment_includes_extra(self, standard_loan_params):
        """New monthly payment should equal original + extra."""
        extra = 300
        result = calculate_early_payoff(
            **standard_loan_params,
            extra_monthly_payment=extra,
        )

        expected_new_payment = result["original_monthly_payment"] + extra
        assert abs(result["new_monthly_payment"] - expected_new_payment) < 0.01

    def test_years_saved_is_months_divided_by_12(self, standard_loan_params):
        """Years saved should be months saved divided by 12."""
        result = calculate_early_payoff(
            **standard_loan_params,
            extra_monthly_payment=200,
        )

        expected_years = round(result["months_saved"] / 12, 1)
        assert result["years_saved"] == expected_years


# =============================================================================
# GET_CALCULATOR FACTORY TESTS
# =============================================================================

class TestGetCalculator:
    """Tests for get_calculator factory function."""

    def test_returns_loan_calculator_tool_instance(self):
        """Factory should return LoanCalculatorTool instance."""
        calc = get_calculator(LoanType.PERSONAL)

        assert isinstance(calc, LoanCalculatorTool)

    @pytest.mark.parametrize("loan_type", [
        pytest.param(LoanType.PERSONAL, id="personal"),
        pytest.param(LoanType.MORTGAGE, id="mortgage"),
        pytest.param(LoanType.AUTO, id="auto"),
    ])
    def test_accepts_loan_type_enum(self, loan_type):
        """Factory should accept all LoanType enum values."""
        calc = get_calculator(loan_type)

        assert isinstance(calc, LoanCalculatorTool)

    @pytest.mark.parametrize("loan_type_str", ["personal", "mortgage", "auto"])
    def test_accepts_string_loan_type(self, loan_type_str):
        """Factory should accept string loan type names."""
        calc = get_calculator(loan_type_str)

        assert isinstance(calc, LoanCalculatorTool)

    def test_calculator_has_valid_dti_ratio(self):
        """Returned calculator should have valid DTI ratio."""
        calc = get_calculator(LoanType.MORTGAGE)

        assert 0 < calc.max_dti_ratio <= 1.0

    def test_invalid_string_raises_error(self):
        """Invalid string loan type should raise ValueError."""
        with pytest.raises(ValueError):
            get_calculator("invalid_type")


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestCalculatorIntegration:
    """Integration tests for calculator functions working together."""

    def test_affordability_matches_mortgage_payment(self):
        """Max home price from affordability should be payable with same payment."""
        income = 15_000
        residency = "expat"
        property_type = "first"

        # Get max affordable home
        afford = calculate_home_affordability(
            monthly_income=income,
            residency=residency,
            property_type=property_type,
        )

        # Calculate mortgage for that home
        mortgage = calculate_mortgage_payment(
            home_price=afford["max_home_price"],
            residency=residency,
            property_type=property_type,
        )

        # Monthly payments should be close
        assert mortgage["valid"] is True
        # Allow 1% tolerance due to rounding
        payment_diff = abs(mortgage["monthly_payment"] - afford["monthly_payment"])
        assert payment_diff < afford["monthly_payment"] * 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
