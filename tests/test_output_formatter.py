"""Unit tests for output formatter module.

Tests the configurable output formatting system that supports
both markdown (streaming) and structured (Pydantic) output.

Follows pytest best practices:
- Parametrized tests for both formatters
- Fixtures for reusable test data
- Clear separation of concerns
"""

import pytest
import pandas as pd
from src.agent.output_formatter import (
    OutputMode,
    OutputFormatter,
    MarkdownFormatter,
    StructuredFormatter,
    get_formatter,
)
from src.agent.response_models import (
    EligibilityResult,
    PaymentResult,
    AffordabilityResult,
    TermComparisonResult,
    MaxLoanResult,
    HomeAffordabilityResult,
    MortgagePaymentResult,
    CarLoanResult,
    EarlyPayoffResult,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def eligibility_data():
    """Sample eligibility check data."""
    return {
        "eligible": True,
        "status": "approved",
        "score": 85.0,
        "reasons": ["Good credit score", "Stable employment"],
        "recommendations": ["Consider shorter term"],
    }


@pytest.fixture
def payment_data():
    """Sample payment calculation data."""
    return {
        "loan_amount": 50000.0,
        "annual_interest_rate": 0.05,
        "loan_term_months": 36,
        "monthly_payment": 1498.88,
        "total_payment": 53959.68,
        "total_interest": 3959.68,
    }


@pytest.fixture
def affordability_data():
    """Sample affordability check data."""
    return {
        "affordable": True,
        "monthly_income": 10000.0,
        "existing_debt": 500.0,
        "monthly_payment": 1498.88,
        "total_monthly_debt": 1998.88,
        "dti_ratio": 0.20,
        "max_recommended_dti": 0.43,
        "message": "Loan is affordable with 20% DTI",
    }


@pytest.fixture
def term_comparison_df():
    """Sample term comparison DataFrame."""
    return pd.DataFrame([
        {"term_months": 36, "term_years": 3.0, "monthly_payment": 1500.0,
         "total_payment": 54000.0, "total_interest": 4000.0, "interest_percentage": 8.0},
        {"term_months": 60, "term_years": 5.0, "monthly_payment": 950.0,
         "total_payment": 57000.0, "total_interest": 7000.0, "interest_percentage": 14.0},
    ])


@pytest.fixture
def schedule_df():
    """Sample amortization schedule DataFrame."""
    return pd.DataFrame([
        {"month": 1, "payment": 1500.0, "principal": 1200.0, "interest": 300.0, "balance": 48800.0},
        {"month": 2, "payment": 1500.0, "principal": 1210.0, "interest": 290.0, "balance": 47590.0},
        {"month": 3, "payment": 1500.0, "principal": 1220.0, "interest": 280.0, "balance": 46370.0},
    ])


@pytest.fixture
def max_loan_data():
    """Sample max loan calculation data."""
    return {
        "max_loan_amount": 75000.0,
        "monthly_income": 10000.0,
        "existing_debt": 500.0,
        "max_monthly_payment": 2500.0,
        "term_months": 36,
        "annual_interest_rate": 0.05,
        "message": "Based on 30% DTI limit",
    }


@pytest.fixture
def home_affordability_data():
    """Sample home affordability data."""
    return {
        "affordable": True,
        "max_home_price": 500000.0,
        "max_loan_amount": 400000.0,
        "required_down_payment": 100000.0,
        "down_payment_percentage": 0.20,
        "monthly_payment": 2100.0,
        "ltv_ratio": 0.80,
        "dti_ratio": 0.35,
        "residency": "expat",
        "property_type": "first",
        "message": "You can afford up to $500,000 home",
    }


@pytest.fixture
def mortgage_data():
    """Sample mortgage payment data."""
    return {
        "valid": True,
        "home_price": 500000.0,
        "down_payment": 100000.0,
        "down_payment_percentage": 0.20,
        "loan_amount": 400000.0,
        "ltv_ratio": 0.80,
        "max_ltv_allowed": 0.80,
        "monthly_payment": 2108.02,
        "total_payment": 758886.72,
        "total_interest": 358886.72,
        "annual_interest_rate": 0.045,
        "loan_term_years": 30,
    }


@pytest.fixture
def car_loan_data():
    """Sample car loan data."""
    return {
        "valid": True,
        "car_price": 30000.0,
        "down_payment": 3000.0,
        "down_payment_percentage": 0.10,
        "loan_amount": 27000.0,
        "ltv_ratio": 0.90,
        "monthly_payment": 509.32,
        "total_payment": 30559.20,
        "total_interest": 3559.20,
        "annual_interest_rate": 0.055,
        "loan_term_months": 60,
    }


@pytest.fixture
def early_payoff_data():
    """Sample early payoff data."""
    return {
        "original_term_months": 360,
        "new_term_months": 280,
        "months_saved": 80,
        "years_saved": 6.7,
        "original_monthly_payment": 1000.0,
        "new_monthly_payment": 1200.0,
        "extra_monthly_payment": 200.0,
        "original_total_interest": 160000.0,
        "new_total_interest": 100000.0,
        "interest_saved": 60000.0,
        "message": "You'll save $60,000 in interest",
    }


# =============================================================================
# OUTPUT MODE TESTS
# =============================================================================

class TestOutputMode:
    """Tests for OutputMode enum."""

    def test_markdown_mode(self):
        """Markdown mode should be available."""
        assert OutputMode.MARKDOWN == "markdown"

    def test_structured_mode(self):
        """Structured mode should be available."""
        assert OutputMode.STRUCTURED == "structured"

    def test_from_env_default_markdown(self, monkeypatch):
        """Default mode should be markdown."""
        monkeypatch.delenv("OUTPUT_MODE", raising=False)
        mode = OutputMode.from_env()
        assert mode == OutputMode.MARKDOWN

    def test_from_env_structured(self, monkeypatch):
        """Should detect structured mode from env."""
        monkeypatch.setenv("OUTPUT_MODE", "structured")
        mode = OutputMode.from_env()
        assert mode == OutputMode.STRUCTURED

    @pytest.mark.parametrize("env_value", ["json", "pydantic", "structured"])
    def test_from_env_structured_aliases(self, monkeypatch, env_value):
        """Should accept various structured mode aliases."""
        monkeypatch.setenv("OUTPUT_MODE", env_value)
        mode = OutputMode.from_env()
        assert mode == OutputMode.STRUCTURED


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================

class TestGetFormatter:
    """Tests for get_formatter factory function."""

    def test_get_markdown_formatter(self):
        """Should return MarkdownFormatter for markdown mode."""
        formatter = get_formatter("markdown")
        assert isinstance(formatter, MarkdownFormatter)

    def test_get_structured_formatter(self):
        """Should return StructuredFormatter for structured mode."""
        formatter = get_formatter("structured")
        assert isinstance(formatter, StructuredFormatter)

    def test_get_formatter_with_enum(self):
        """Should accept OutputMode enum."""
        formatter = get_formatter(OutputMode.MARKDOWN)
        assert isinstance(formatter, MarkdownFormatter)

    def test_get_formatter_auto_detect(self, monkeypatch):
        """Should auto-detect mode from env when None."""
        monkeypatch.setenv("OUTPUT_MODE", "structured")
        formatter = get_formatter(None)
        assert isinstance(formatter, StructuredFormatter)

    def test_formatter_implements_protocol(self):
        """Both formatters should implement OutputFormatter protocol."""
        markdown = get_formatter("markdown")
        structured = get_formatter("structured")

        assert isinstance(markdown, OutputFormatter)
        assert isinstance(structured, OutputFormatter)


# =============================================================================
# MARKDOWN FORMATTER TESTS
# =============================================================================

class TestMarkdownFormatter:
    """Tests for MarkdownFormatter."""

    @pytest.fixture
    def formatter(self):
        return MarkdownFormatter()

    def test_format_eligibility_returns_string(self, formatter, eligibility_data):
        """Eligibility output should be string."""
        result = formatter.format_eligibility(eligibility_data)
        assert isinstance(result, str)

    def test_format_eligibility_contains_status(self, formatter, eligibility_data):
        """Output should contain status."""
        result = formatter.format_eligibility(eligibility_data)
        assert "APPROVED" in result
        assert "✅" in result

    def test_format_eligibility_contains_score(self, formatter, eligibility_data):
        """Output should contain score."""
        result = formatter.format_eligibility(eligibility_data)
        assert "85.0" in result

    def test_format_payment_returns_string(self, formatter, payment_data):
        """Payment output should be string."""
        result = formatter.format_payment(payment_data)
        assert isinstance(result, str)

    def test_format_payment_contains_amounts(self, formatter, payment_data):
        """Output should contain payment amounts."""
        result = formatter.format_payment(payment_data)
        assert "$50,000" in result
        assert "$1,498.88" in result

    def test_format_affordability_affordable(self, formatter, affordability_data):
        """Affordable loan should show positive indicator."""
        result = formatter.format_affordability(affordability_data)
        assert "✅" in result
        assert "AFFORDABLE" in result

    def test_format_affordability_unaffordable(self, formatter):
        """Unaffordable loan should show warning."""
        data = {"affordable": False, "dti_ratio": 0.6, "message": "Too high DTI"}
        result = formatter.format_affordability(data)
        assert "⚠️" in result
        assert "UNAFFORDABLE" in result

    def test_format_schedule_returns_table(self, formatter, schedule_df):
        """Schedule output should contain table."""
        data = {"show_first_n_months": 3, "loan_term_months": 36}
        result = formatter.format_schedule(data, schedule_df)
        assert "| Month |" in result
        assert "| 1 |" in result

    def test_format_term_comparison_returns_table(self, formatter, term_comparison_df):
        """Term comparison should return table."""
        data = {"loan_amount": 50000, "annual_interest_rate": 0.05}
        result = formatter.format_term_comparison(data, term_comparison_df)
        assert "| Term |" in result
        assert "36 mo" in result

    def test_format_max_loan_positive(self, formatter, max_loan_data):
        """Max loan output should show amount."""
        result = formatter.format_max_loan(max_loan_data)
        assert "$75,000" in result
        assert "✅" in result

    def test_format_max_loan_zero(self, formatter):
        """Zero max loan should show cannot afford."""
        data = {"max_loan_amount": 0, "message": "Debt too high"}
        result = formatter.format_max_loan(data)
        assert "❌" in result
        assert "Cannot afford" in result

    def test_format_home_affordability(self, formatter, home_affordability_data):
        """Home affordability should show details."""
        result = formatter.format_home_affordability(home_affordability_data)
        assert "$500,000" in result
        assert "Expat" in result

    def test_format_mortgage(self, formatter, mortgage_data):
        """Mortgage output should show payment."""
        result = formatter.format_mortgage(mortgage_data)
        assert "$2,108.02" in result
        assert "80%" in result

    def test_format_car_loan(self, formatter, car_loan_data):
        """Car loan output should show payment."""
        result = formatter.format_car_loan(car_loan_data)
        assert "$509.32" in result
        assert "$30,000" in result

    def test_format_early_payoff(self, formatter, early_payoff_data):
        """Early payoff output should show savings."""
        result = formatter.format_early_payoff(early_payoff_data)
        assert "$60,000" in result
        assert "80 months" in result


# =============================================================================
# STRUCTURED FORMATTER TESTS
# =============================================================================

class TestStructuredFormatter:
    """Tests for StructuredFormatter."""

    @pytest.fixture
    def formatter(self):
        return StructuredFormatter()

    def test_format_eligibility_returns_model(self, formatter, eligibility_data):
        """Eligibility output should be Pydantic model."""
        result = formatter.format_eligibility(eligibility_data)
        assert isinstance(result, EligibilityResult)

    def test_format_eligibility_model_values(self, formatter, eligibility_data):
        """Model should have correct values."""
        result = formatter.format_eligibility(eligibility_data)
        assert result.eligible is True
        assert result.status == "approved"
        assert result.score == 85.0

    def test_format_payment_returns_model(self, formatter, payment_data):
        """Payment output should be Pydantic model."""
        result = formatter.format_payment(payment_data)
        assert isinstance(result, PaymentResult)

    def test_format_payment_model_values(self, formatter, payment_data):
        """Model should have correct values."""
        result = formatter.format_payment(payment_data)
        assert result.loan_amount == 50000.0
        assert result.monthly_payment == 1498.88

    def test_format_affordability_returns_model(self, formatter, affordability_data):
        """Affordability output should be Pydantic model."""
        result = formatter.format_affordability(affordability_data)
        assert isinstance(result, AffordabilityResult)

    def test_format_term_comparison_returns_model(self, formatter, term_comparison_df):
        """Term comparison should return Pydantic model."""
        data = {"loan_amount": 50000, "annual_interest_rate": 0.05}
        result = formatter.format_term_comparison(data, term_comparison_df)
        assert isinstance(result, TermComparisonResult)
        assert len(result.options) == 2

    def test_format_max_loan_returns_model(self, formatter, max_loan_data):
        """Max loan output should be Pydantic model."""
        result = formatter.format_max_loan(max_loan_data)
        assert isinstance(result, MaxLoanResult)
        assert result.max_loan_amount == 75000.0

    def test_format_home_affordability_returns_model(self, formatter, home_affordability_data):
        """Home affordability should return Pydantic model."""
        result = formatter.format_home_affordability(home_affordability_data)
        assert isinstance(result, HomeAffordabilityResult)

    def test_format_mortgage_returns_model(self, formatter, mortgage_data):
        """Mortgage output should be Pydantic model."""
        result = formatter.format_mortgage(mortgage_data)
        assert isinstance(result, MortgagePaymentResult)
        assert result.monthly_payment == 2108.02

    def test_format_car_loan_returns_model(self, formatter, car_loan_data):
        """Car loan output should be Pydantic model."""
        result = formatter.format_car_loan(car_loan_data)
        assert isinstance(result, CarLoanResult)
        assert result.monthly_payment == 509.32

    def test_format_early_payoff_returns_model(self, formatter, early_payoff_data):
        """Early payoff output should be Pydantic model."""
        result = formatter.format_early_payoff(early_payoff_data)
        assert isinstance(result, EarlyPayoffResult)
        assert result.interest_saved == 60000.0


# =============================================================================
# FORMATTER INTERCHANGEABILITY TESTS (Liskov Substitution)
# =============================================================================

class TestFormatterInterchangeability:
    """Tests that formatters are interchangeable (Liskov Substitution Principle)."""

    @pytest.fixture(params=["markdown", "structured"])
    def formatter(self, request):
        """Parametrized fixture for both formatters."""
        return get_formatter(request.param)

    def test_all_formatters_have_eligibility_method(self, formatter):
        """All formatters should have format_eligibility method."""
        assert hasattr(formatter, "format_eligibility")
        assert callable(formatter.format_eligibility)

    def test_all_formatters_have_payment_method(self, formatter):
        """All formatters should have format_payment method."""
        assert hasattr(formatter, "format_payment")
        assert callable(formatter.format_payment)

    def test_all_formatters_have_affordability_method(self, formatter):
        """All formatters should have format_affordability method."""
        assert hasattr(formatter, "format_affordability")
        assert callable(formatter.format_affordability)

    def test_all_methods_work_with_data(self, formatter, eligibility_data, payment_data):
        """All formatters should process data without errors."""
        # Should not raise
        formatter.format_eligibility(eligibility_data)
        formatter.format_payment(payment_data)


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Edge case tests for formatters."""

    def test_markdown_handles_missing_fields(self):
        """Markdown formatter should handle missing fields gracefully."""
        formatter = MarkdownFormatter()
        data = {}  # Empty data
        result = formatter.format_payment(data)
        assert isinstance(result, str)
        assert "$0.00" in result

    def test_structured_handles_missing_fields(self):
        """Structured formatter should use defaults for missing fields."""
        formatter = StructuredFormatter()
        data = {"eligible": True, "status": "approved", "score": 50}
        result = formatter.format_eligibility(data)
        assert result.reasons == []
        assert result.recommendations == []

    def test_markdown_handles_zero_loan_amount(self):
        """Should handle zero loan amount without division error."""
        formatter = MarkdownFormatter()
        data = {"loan_amount": 0, "total_interest": 0}
        result = formatter.format_payment(data)
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
