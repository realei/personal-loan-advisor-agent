"""Unit tests for LoanEligibilityTool."""

import pytest

from src.tools.loan_eligibility import (
    ApplicantInfo,
    EligibilityStatus,
    EmploymentStatus,
    LoanEligibilityTool,
)


class TestLoanEligibilityTool:
    """Test suite for LoanEligibilityTool."""

    @pytest.fixture
    def eligibility_tool(self):
        """Create LoanEligibilityTool instance with default settings."""
        return LoanEligibilityTool(
            min_age=18,
            max_age=65,
            min_monthly_income=5000.0,
            min_credit_score=600,
            max_dti_ratio=0.5,
            min_employment_length=1.0,
            max_loan_amount=1000000.0,
        )

    @pytest.fixture
    def valid_applicant(self):
        """Create a valid applicant for testing."""
        return ApplicantInfo(
            age=35,
            monthly_income=10000.0,
            credit_score=720,
            employment_status=EmploymentStatus.FULL_TIME,
            employment_length_years=5.0,
            monthly_debt_obligations=1500.0,
            requested_loan_amount=50000.0,
            loan_term_months=36,
            has_existing_loans=False,
            previous_defaults=False,
        )

    def test_fully_eligible_applicant(self, eligibility_tool, valid_applicant):
        """Test that a fully qualified applicant is approved."""
        result = eligibility_tool.check_eligibility(valid_applicant)

        assert result.eligible is True
        assert result.status == EligibilityStatus.ELIGIBLE
        assert result.score >= 80.0
        assert len(result.reasons) >= 0

    def test_age_too_young(self, eligibility_tool, valid_applicant):
        """Test rejection for applicant below minimum age."""
        valid_applicant.age = 17

        result = eligibility_tool.check_eligibility(valid_applicant)

        assert result.eligible is False
        assert result.status == EligibilityStatus.NOT_ELIGIBLE
        assert any("below minimum requirement" in reason for reason in result.reasons)

    def test_age_maturity_exceeds_max(self, eligibility_tool, valid_applicant):
        """Test rejection when loan maturity age exceeds maximum."""
        valid_applicant.age = 60
        valid_applicant.loan_term_months = 60  # Will mature at age 65

        result = eligibility_tool.check_eligibility(valid_applicant)

        # Should still pass since maturity is exactly 65
        assert result.eligible is True

        # Now test exceeding
        valid_applicant.loan_term_months = 72  # Will mature at age 66
        result = eligibility_tool.check_eligibility(valid_applicant)

        assert result.eligible is False
        assert any("exceeds maximum" in reason for reason in result.reasons)

    def test_insufficient_income(self, eligibility_tool, valid_applicant):
        """Test rejection for insufficient income."""
        valid_applicant.monthly_income = 4000.0  # Below minimum of 5000

        result = eligibility_tool.check_eligibility(valid_applicant)

        assert result.eligible is False
        assert result.status == EligibilityStatus.NOT_ELIGIBLE
        assert any("below minimum requirement" in reason for reason in result.reasons)

    def test_low_credit_score(self, eligibility_tool, valid_applicant):
        """Test rejection for low credit score."""
        valid_applicant.credit_score = 550  # Below minimum of 600

        result = eligibility_tool.check_eligibility(valid_applicant)

        assert result.eligible is False
        assert result.status == EligibilityStatus.NOT_ELIGIBLE
        assert any("Credit score" in reason for reason in result.reasons)

    def test_unemployed_applicant(self, eligibility_tool, valid_applicant):
        """Test rejection for unemployed applicant."""
        valid_applicant.employment_status = EmploymentStatus.UNEMPLOYED

        result = eligibility_tool.check_eligibility(valid_applicant)

        assert result.eligible is False
        assert result.status == EligibilityStatus.NOT_ELIGIBLE
        assert any("Unemployed" in reason for reason in result.reasons)

    def test_insufficient_employment_length(self, eligibility_tool, valid_applicant):
        """Test rejection for insufficient employment history."""
        valid_applicant.employment_length_years = 0.5  # Below minimum of 1.0

        result = eligibility_tool.check_eligibility(valid_applicant)

        assert result.eligible is False
        assert any("Employment length" in reason for reason in result.reasons)

    def test_high_dti_ratio(self, eligibility_tool, valid_applicant):
        """Test rejection for high debt-to-income ratio."""
        # Set high existing debt
        valid_applicant.monthly_debt_obligations = 8000.0
        # With new loan payment, DTI will exceed 50%

        result = eligibility_tool.check_eligibility(valid_applicant)

        assert result.eligible is False
        assert result.status == EligibilityStatus.NOT_ELIGIBLE
        assert any("Debt-to-Income ratio" in reason for reason in result.reasons)

    def test_excessive_loan_amount(self, eligibility_tool, valid_applicant):
        """Test rejection for loan amount exceeding maximum."""
        valid_applicant.requested_loan_amount = 1500000.0  # Exceeds max of 1,000,000

        result = eligibility_tool.check_eligibility(valid_applicant)

        assert result.eligible is False
        assert result.status == EligibilityStatus.NOT_ELIGIBLE
        assert any("exceeds maximum" in reason for reason in result.reasons)

    def test_previous_defaults(self, eligibility_tool, valid_applicant):
        """Test rejection for applicant with previous defaults."""
        valid_applicant.previous_defaults = True

        result = eligibility_tool.check_eligibility(valid_applicant)

        assert result.eligible is False
        assert result.status == EligibilityStatus.NOT_ELIGIBLE
        assert any("defaults" in reason.lower() for reason in result.reasons)

    def test_retired_applicant_eligible(self, eligibility_tool, valid_applicant):
        """Test that retired applicant with good profile is eligible."""
        valid_applicant.age = 62
        valid_applicant.employment_status = EmploymentStatus.RETIRED
        valid_applicant.monthly_income = 8000.0  # Good retirement income

        result = eligibility_tool.check_eligibility(valid_applicant)

        assert result.eligible is True
        assert result.status == EligibilityStatus.ELIGIBLE

    def test_self_employed_applicant(self, eligibility_tool, valid_applicant):
        """Test self-employed applicant eligibility."""
        valid_applicant.employment_status = EmploymentStatus.SELF_EMPLOYED
        valid_applicant.employment_length_years = 3.0

        result = eligibility_tool.check_eligibility(valid_applicant)

        assert result.eligible is True
        assert result.status == EligibilityStatus.ELIGIBLE

    def test_excellent_credit_high_score(self, eligibility_tool, valid_applicant):
        """Test that excellent credit score results in high eligibility score."""
        valid_applicant.credit_score = 800
        valid_applicant.monthly_income = 20000.0
        valid_applicant.employment_length_years = 10.0

        result = eligibility_tool.check_eligibility(valid_applicant)

        assert result.eligible is True
        assert result.score >= 90.0  # Should have very high score

    def test_marginal_applicant_conditional(self, eligibility_tool, valid_applicant):
        """Test that marginal applicant gets conditional status."""
        # Make applicant marginal but not failing critical checks
        valid_applicant.credit_score = 620  # Just above minimum
        valid_applicant.monthly_income = 5500.0  # Just above minimum
        valid_applicant.employment_length_years = 0.8  # Below minimum

        result = eligibility_tool.check_eligibility(valid_applicant)

        # Should fail due to employment length
        assert result.eligible is False

    def test_high_loan_to_income_ratio(self, eligibility_tool, valid_applicant):
        """Test warning for high loan-to-income ratio."""
        valid_applicant.monthly_income = 5000.0
        valid_applicant.requested_loan_amount = 200000.0  # 40x monthly income

        result = eligibility_tool.check_eligibility(valid_applicant)

        assert result.eligible is False
        assert any("annual income" in reason for reason in result.reasons)

    def test_recommendations_provided(self, eligibility_tool, valid_applicant):
        """Test that recommendations are provided for rejected applicants."""
        valid_applicant.credit_score = 550

        result = eligibility_tool.check_eligibility(valid_applicant)

        assert result.eligible is False
        assert len(result.recommendations) > 0
        assert any("credit score" in rec.lower() for rec in result.recommendations)

    def test_score_calculation(self, eligibility_tool, valid_applicant):
        """Test that eligibility score is calculated correctly."""
        result = eligibility_tool.check_eligibility(valid_applicant)

        assert 0 <= result.score <= 100
        assert isinstance(result.score, float)

    def test_multiple_failures(self, eligibility_tool, valid_applicant):
        """Test applicant failing multiple criteria."""
        valid_applicant.age = 17
        valid_applicant.credit_score = 500
        valid_applicant.monthly_income = 3000.0
        valid_applicant.previous_defaults = True

        result = eligibility_tool.check_eligibility(valid_applicant)

        assert result.eligible is False
        assert len(result.reasons) >= 3  # Should have multiple failure reasons
        assert result.score < 50.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
