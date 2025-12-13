"""Unit tests for structured response models.

Tests the Pydantic response models used for deterministic agent output.
Validates that models correctly validate and serialize data.

Follows pytest best practices:
- Parametrized tests for validation rules
- Fixtures for reusable test data
- Clear separation of concerns
"""

import pytest
from pydantic import ValidationError
from src.agent.response_models import (
    LoanAdvisorResponse,
    SimpleLoanResponse,
    EligibilityResult,
    PaymentResult,
    AffordabilityResult,
    TermComparisonItem,
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
def valid_eligibility_result():
    """Valid eligibility result data."""
    return {
        "eligible": True,
        "status": "approved",
        "score": 85.0,
        "reasons": ["Good credit score", "Stable employment"],
        "recommendations": ["Consider shorter term for lower interest"],
    }


@pytest.fixture
def valid_payment_result():
    """Valid payment result data."""
    return {
        "loan_amount": 50000.0,
        "annual_interest_rate": 0.05,
        "loan_term_months": 36,
        "monthly_payment": 1498.88,
        "total_payment": 53959.68,
        "total_interest": 3959.68,
        "interest_percentage": 7.92,
    }


@pytest.fixture
def valid_affordability_result():
    """Valid affordability result data."""
    return {
        "affordable": True,
        "monthly_income": 10000.0,
        "existing_debt": 500.0,
        "monthly_payment": 1498.88,
        "total_monthly_debt": 1998.88,
        "dti_ratio": 0.20,
        "max_recommended_dti": 0.43,
        "message": "Loan is affordable with DTI of 20%",
    }


@pytest.fixture
def valid_loan_advisor_response(valid_payment_result):
    """Valid full loan advisor response."""
    return {
        "action": "payment_calculation",
        "tool_called": "calculate_loan_payment",
        "payment": valid_payment_result,
        "summary": "Monthly payment of $1,498.88 for $50,000 loan",
        "details": "## Payment Details\n\nYour monthly payment is $1,498.88",
        "recommendations": ["Consider automatic payments for discount"],
        "warnings": [],
        "follow_up_questions": ["Would you like to see the amortization schedule?"],
    }


# =============================================================================
# ELIGIBILITY RESULT TESTS
# =============================================================================

class TestEligibilityResult:
    """Tests for EligibilityResult model."""

    def test_valid_eligibility_result(self, valid_eligibility_result):
        """Valid data should create model successfully."""
        result = EligibilityResult(**valid_eligibility_result)

        assert result.eligible is True
        assert result.status == "approved"
        assert result.score == 85.0

    @pytest.mark.parametrize("status", ["approved", "conditional", "denied"])
    def test_valid_status_values(self, status):
        """All valid status values should be accepted."""
        result = EligibilityResult(
            eligible=True,
            status=status,
            score=75.0,
        )
        assert result.status == status

    def test_invalid_status_rejected(self):
        """Invalid status should raise ValidationError."""
        with pytest.raises(ValidationError):
            EligibilityResult(
                eligible=True,
                status="pending",  # Invalid
                score=75.0,
            )

    @pytest.mark.parametrize("score", [-1, 101, 150])
    def test_invalid_score_rejected(self, score):
        """Score outside 0-100 range should be rejected."""
        with pytest.raises(ValidationError):
            EligibilityResult(
                eligible=True,
                status="approved",
                score=score,
            )

    @pytest.mark.parametrize("score", [0, 50, 100])
    def test_valid_score_boundary(self, score):
        """Score at boundaries should be accepted."""
        result = EligibilityResult(
            eligible=True,
            status="approved",
            score=score,
        )
        assert result.score == score


# =============================================================================
# PAYMENT RESULT TESTS
# =============================================================================

class TestPaymentResult:
    """Tests for PaymentResult model."""

    def test_valid_payment_result(self, valid_payment_result):
        """Valid data should create model successfully."""
        result = PaymentResult(**valid_payment_result)

        assert result.loan_amount == 50000.0
        assert result.monthly_payment == 1498.88

    def test_zero_interest_rate_allowed(self):
        """Zero interest rate should be allowed."""
        result = PaymentResult(
            loan_amount=10000.0,
            annual_interest_rate=0.0,
            loan_term_months=12,
            monthly_payment=833.33,
            total_payment=10000.0,
            total_interest=0.0,
            interest_percentage=0.0,
        )
        assert result.annual_interest_rate == 0.0
        assert result.total_interest == 0.0

    def test_negative_loan_amount_rejected(self):
        """Negative loan amount should be rejected."""
        with pytest.raises(ValidationError):
            PaymentResult(
                loan_amount=-10000.0,
                annual_interest_rate=0.05,
                loan_term_months=36,
                monthly_payment=300.0,
                total_payment=10800.0,
                total_interest=800.0,
                interest_percentage=8.0,
            )

    def test_zero_loan_term_rejected(self):
        """Zero loan term should be rejected."""
        with pytest.raises(ValidationError):
            PaymentResult(
                loan_amount=10000.0,
                annual_interest_rate=0.05,
                loan_term_months=0,
                monthly_payment=300.0,
                total_payment=10800.0,
                total_interest=800.0,
                interest_percentage=8.0,
            )


# =============================================================================
# AFFORDABILITY RESULT TESTS
# =============================================================================

class TestAffordabilityResult:
    """Tests for AffordabilityResult model."""

    def test_valid_affordability_result(self, valid_affordability_result):
        """Valid data should create model successfully."""
        result = AffordabilityResult(**valid_affordability_result)

        assert result.affordable is True
        assert result.dti_ratio == 0.20

    @pytest.mark.parametrize("dti", [0.0, 0.5, 1.0])
    def test_valid_dti_ratio_boundary(self, dti):
        """DTI ratio at boundaries should be accepted."""
        result = AffordabilityResult(
            affordable=True,
            monthly_income=10000.0,
            existing_debt=0.0,
            monthly_payment=1000.0,
            total_monthly_debt=1000.0,
            dti_ratio=dti,
            max_recommended_dti=0.43,
            message="Test",
        )
        assert result.dti_ratio == dti

    def test_dti_ratio_over_one_rejected(self):
        """DTI ratio over 1.0 should be rejected."""
        with pytest.raises(ValidationError):
            AffordabilityResult(
                affordable=False,
                monthly_income=10000.0,
                existing_debt=0.0,
                monthly_payment=1000.0,
                total_monthly_debt=1000.0,
                dti_ratio=1.5,  # Invalid
                max_recommended_dti=0.43,
                message="Test",
            )


# =============================================================================
# TERM COMPARISON TESTS
# =============================================================================

class TestTermComparisonResult:
    """Tests for TermComparisonResult model."""

    def test_valid_term_comparison(self):
        """Valid term comparison should create model successfully."""
        options = [
            TermComparisonItem(
                term_months=36,
                term_years=3.0,
                monthly_payment=1500.0,
                total_payment=54000.0,
                total_interest=4000.0,
                interest_percentage=8.0,
            ),
            TermComparisonItem(
                term_months=60,
                term_years=5.0,
                monthly_payment=950.0,
                total_payment=57000.0,
                total_interest=7000.0,
                interest_percentage=14.0,
            ),
        ]

        result = TermComparisonResult(
            loan_amount=50000.0,
            annual_interest_rate=0.05,
            options=options,
            recommendation="Choose 36 months for less interest",
        )

        assert len(result.options) == 2
        assert result.options[0].term_months == 36
        assert result.options[1].term_months == 60


# =============================================================================
# MORTGAGE RESULT TESTS
# =============================================================================

class TestMortgagePaymentResult:
    """Tests for MortgagePaymentResult model."""

    def test_valid_mortgage_result(self):
        """Valid mortgage result should create model successfully."""
        result = MortgagePaymentResult(
            valid=True,
            home_price=500000.0,
            down_payment=100000.0,
            down_payment_percentage=0.20,
            loan_amount=400000.0,
            ltv_ratio=0.80,
            max_ltv_allowed=0.80,
            monthly_payment=2108.02,
            total_payment=758886.72,
            total_interest=358886.72,
            annual_interest_rate=0.045,
            loan_term_years=30,
        )

        assert result.valid is True
        assert result.home_price == 500000.0
        assert result.ltv_ratio == 0.80

    def test_invalid_ltv_rejected(self):
        """LTV ratio over 1.0 should be rejected."""
        with pytest.raises(ValidationError):
            MortgagePaymentResult(
                valid=True,
                home_price=500000.0,
                down_payment=100000.0,
                down_payment_percentage=0.20,
                loan_amount=400000.0,
                ltv_ratio=1.5,  # Invalid
                max_ltv_allowed=0.80,
                monthly_payment=2108.02,
                total_payment=758886.72,
                total_interest=358886.72,
                annual_interest_rate=0.045,
                loan_term_years=30,
            )


# =============================================================================
# CAR LOAN RESULT TESTS
# =============================================================================

class TestCarLoanResult:
    """Tests for CarLoanResult model."""

    def test_valid_car_loan_result(self):
        """Valid car loan result should create model successfully."""
        result = CarLoanResult(
            valid=True,
            car_price=30000.0,
            down_payment=3000.0,
            down_payment_percentage=0.10,
            loan_amount=27000.0,
            ltv_ratio=0.90,
            monthly_payment=509.32,
            total_payment=30559.20,
            total_interest=3559.20,
            annual_interest_rate=0.055,
            loan_term_months=60,
        )

        assert result.valid is True
        assert result.car_price == 30000.0


# =============================================================================
# EARLY PAYOFF RESULT TESTS
# =============================================================================

class TestEarlyPayoffResult:
    """Tests for EarlyPayoffResult model."""

    def test_valid_early_payoff_result(self):
        """Valid early payoff result should create model successfully."""
        result = EarlyPayoffResult(
            original_term_months=360,
            new_term_months=280,
            months_saved=80,
            years_saved=6.7,
            original_monthly_payment=1000.0,
            new_monthly_payment=1200.0,
            extra_monthly_payment=200.0,
            original_total_interest=160000.0,
            new_total_interest=100000.0,
            interest_saved=60000.0,
            message="You'll save $60,000 in interest",
        )

        assert result.months_saved == 80
        assert result.interest_saved == 60000.0


# =============================================================================
# MAIN RESPONSE MODEL TESTS
# =============================================================================

class TestLoanAdvisorResponse:
    """Tests for main LoanAdvisorResponse model."""

    def test_valid_full_response(self, valid_loan_advisor_response):
        """Valid full response should create model successfully."""
        response = LoanAdvisorResponse(**valid_loan_advisor_response)

        assert response.action == "payment_calculation"
        assert response.tool_called == "calculate_loan_payment"
        assert response.payment is not None
        assert response.summary == "Monthly payment of $1,498.88 for $50,000 loan"

    @pytest.mark.parametrize("action", [
        "eligibility_check",
        "payment_calculation",
        "payment_schedule",
        "affordability_check",
        "term_comparison",
        "max_loan_calculation",
        "home_affordability",
        "mortgage_payment",
        "car_loan",
        "car_loan_comparison",
        "early_payoff",
        "general_response",
    ])
    def test_all_action_types_valid(self, action):
        """All action types should be accepted."""
        response = LoanAdvisorResponse(
            action=action,
            summary="Test summary",
            details="Test details",
        )
        assert response.action == action

    def test_invalid_action_rejected(self):
        """Invalid action type should be rejected."""
        with pytest.raises(ValidationError):
            LoanAdvisorResponse(
                action="invalid_action",
                summary="Test",
                details="Test",
            )

    def test_general_response_no_tool_called(self):
        """General response should work without tool_called."""
        response = LoanAdvisorResponse(
            action="general_response",
            tool_called=None,
            summary="I can help with loan calculations",
            details="Please provide your loan details",
        )

        assert response.action == "general_response"
        assert response.tool_called is None

    def test_response_with_warnings(self, valid_payment_result):
        """Response with warnings should be created successfully."""
        response = LoanAdvisorResponse(
            action="payment_calculation",
            tool_called="calculate_loan_payment",
            payment=PaymentResult(**valid_payment_result),
            summary="Monthly payment calculated",
            details="Details here",
            warnings=["High DTI ratio detected", "Consider lower loan amount"],
        )

        assert len(response.warnings) == 2
        assert "High DTI ratio detected" in response.warnings

    def test_response_serialization(self, valid_loan_advisor_response):
        """Response should serialize to dict correctly."""
        response = LoanAdvisorResponse(**valid_loan_advisor_response)
        data = response.model_dump()

        assert isinstance(data, dict)
        assert data["action"] == "payment_calculation"
        assert data["payment"]["loan_amount"] == 50000.0

    def test_response_json_serialization(self, valid_loan_advisor_response):
        """Response should serialize to JSON correctly."""
        response = LoanAdvisorResponse(**valid_loan_advisor_response)
        json_str = response.model_dump_json()

        assert isinstance(json_str, str)
        assert "payment_calculation" in json_str
        assert "50000" in json_str


# =============================================================================
# SIMPLE RESPONSE MODEL TESTS
# =============================================================================

class TestSimpleLoanResponse:
    """Tests for SimpleLoanResponse model."""

    def test_valid_simple_response(self):
        """Valid simple response should create model successfully."""
        response = SimpleLoanResponse(
            success=True,
            action="payment_calculation",
            data={"monthly_payment": 1498.88, "total_interest": 3959.68},
            summary="Monthly payment is $1,498.88",
        )

        assert response.success is True
        assert response.data["monthly_payment"] == 1498.88

    def test_simple_response_with_recommendations(self):
        """Simple response with recommendations should work."""
        response = SimpleLoanResponse(
            success=True,
            action="eligibility_check",
            data={"eligible": True, "score": 85},
            summary="You are eligible",
            recommendations=["Consider shorter term", "Shop around for rates"],
        )

        assert len(response.recommendations) == 2


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Edge case tests for response models."""

    def test_empty_lists_default(self):
        """Empty lists should be default for list fields."""
        response = LoanAdvisorResponse(
            action="general_response",
            summary="Test",
            details="Test details",
        )

        assert response.recommendations == []
        assert response.warnings == []
        assert response.follow_up_questions == []

    def test_none_optional_fields(self):
        """Optional fields should default to None."""
        response = LoanAdvisorResponse(
            action="general_response",
            summary="Test",
            details="Test details",
        )

        assert response.tool_called is None
        assert response.eligibility is None
        assert response.payment is None

    def test_large_numbers_handled(self):
        """Large loan amounts should be handled correctly."""
        result = PaymentResult(
            loan_amount=10_000_000.0,
            annual_interest_rate=0.035,
            loan_term_months=360,
            monthly_payment=44941.21,
            total_payment=16178835.60,
            total_interest=6178835.60,
            interest_percentage=61.79,
        )

        assert result.loan_amount == 10_000_000.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
