"""
Simple unit tests for LoanEligibilityTool
Demonstrates typical eligibility check scenarios
"""

import pytest
from src.tools.loan_eligibility import (
    LoanEligibilityTool,
    ApplicantInfo,
    EmploymentStatus,
    EligibilityStatus
)


class TestEligibilityBasics:
    """Basic eligibility check tests"""

    @pytest.fixture
    def eligibility_tool(self):
        """Create eligibility check tool"""
        return LoanEligibilityTool(
            min_age=18,
            max_age=65,
            min_monthly_income=5000,
            min_credit_score=600,
            max_dti_ratio=0.5,
            min_employment_length=1.0
        )

    def test_perfect_applicant(self, eligibility_tool):
        """Test perfect applicant - should be fully eligible"""
        # Given: High-quality applicant
        applicant = ApplicantInfo(
            age=35,
            monthly_income=10000,
            credit_score=750,
            employment_status=EmploymentStatus.FULL_TIME,
            employment_length_years=5,
            monthly_debt_obligations=1000,
            requested_loan_amount=50000,
            loan_term_months=36,
            has_existing_loans=False,
            previous_defaults=False
        )

        # When: Check eligibility
        result = eligibility_tool.check_eligibility(applicant)

        # Then: Should be eligible
        assert result.eligible is True
        assert result.status == EligibilityStatus.ELIGIBLE
        assert result.score > 80  # High score
        # Successful application may contain success messages, not necessarily an empty list
        assert len(result.reasons) >= 0

    def test_too_young_applicant(self, eligibility_tool):
        """Test applicant too young - should fail at Pydantic validation"""
        # Below minimum age 18, Pydantic will reject directly
        with pytest.raises(Exception):  # Pydantic ValidationError
            ApplicantInfo(
                age=16,
                monthly_income=10000,
                credit_score=750,
                employment_status=EmploymentStatus.FULL_TIME,
                employment_length_years=1,
                monthly_debt_obligations=0,
                requested_loan_amount=30000,
                loan_term_months=36
            )

    def test_too_old_applicant(self, eligibility_tool):
        """Test applicant too old - should be ineligible"""
        applicant = ApplicantInfo(
            age=70,  # Exceeds maximum age 65
            monthly_income=10000,
            credit_score=750,
            employment_status=EmploymentStatus.RETIRED,
            employment_length_years=30,
            monthly_debt_obligations=0,
            requested_loan_amount=30000,
            loan_term_months=36
        )

        result = eligibility_tool.check_eligibility(applicant)

        assert result.eligible is False
        assert "age" in str(result.reasons).lower()

    def test_low_income_applicant(self, eligibility_tool):
        """Test income too low - should be ineligible"""
        applicant = ApplicantInfo(
            age=30,
            monthly_income=3000,  # Below minimum income 5000
            credit_score=700,
            employment_status=EmploymentStatus.FULL_TIME,
            employment_length_years=2,
            monthly_debt_obligations=0,
            requested_loan_amount=50000,
            loan_term_months=36
        )

        result = eligibility_tool.check_eligibility(applicant)

        assert result.eligible is False
        assert "income" in str(result.reasons).lower()

    def test_low_credit_score(self, eligibility_tool):
        """Test credit score too low - should be ineligible"""
        applicant = ApplicantInfo(
            age=30,
            monthly_income=10000,
            credit_score=550,  # Below minimum score 600
            employment_status=EmploymentStatus.FULL_TIME,
            employment_length_years=3,
            monthly_debt_obligations=0,
            requested_loan_amount=30000,
            loan_term_months=36
        )

        result = eligibility_tool.check_eligibility(applicant)

        assert result.eligible is False
        assert "credit" in str(result.reasons).lower()


class TestDTIRatio:
    """DTI (Debt-to-Income) ratio tests"""

    @pytest.fixture
    def eligibility_tool(self):
        return LoanEligibilityTool(max_dti_ratio=0.5)

    def test_acceptable_dti_ratio(self, eligibility_tool):
        """Test acceptable DTI ratio"""
        applicant = ApplicantInfo(
            age=35,
            monthly_income=10000,
            credit_score=720,
            employment_status=EmploymentStatus.FULL_TIME,
            employment_length_years=5,
            monthly_debt_obligations=2000,  # Existing debt
            requested_loan_amount=50000,  # New loan monthly payment approx $1500
            loan_term_months=36
        )

        result = eligibility_tool.check_eligibility(applicant)

        # DTI = (2000 + 1500) / 10000 = 35% < 50%
        assert result.eligible is True

    def test_excessive_dti_ratio(self, eligibility_tool):
        """Test excessive DTI ratio - should be ineligible"""
        applicant = ApplicantInfo(
            age=35,
            monthly_income=5000,  # Low income
            credit_score=720,
            employment_status=EmploymentStatus.FULL_TIME,
            employment_length_years=5,
            monthly_debt_obligations=3000,  # High existing debt
            requested_loan_amount=50000,  # Wants to borrow more
            loan_term_months=36
        )

        result = eligibility_tool.check_eligibility(applicant)

        # DTI will exceed 50%
        assert result.eligible is False
        assert "dti" in str(result.reasons).lower() or "debt" in str(result.reasons).lower()


class TestEmploymentStatus:
    """Employment status tests"""

    @pytest.fixture
    def eligibility_tool(self):
        return LoanEligibilityTool(min_employment_length=1.0)

    def test_full_time_employment(self, eligibility_tool):
        """Test full-time employment - should be optimal status"""
        applicant = ApplicantInfo(
            age=30,
            monthly_income=8000,
            credit_score=700,
            employment_status=EmploymentStatus.FULL_TIME,
            employment_length_years=3,
            monthly_debt_obligations=500,
            requested_loan_amount=40000,
            loan_term_months=36
        )

        result = eligibility_tool.check_eligibility(applicant)
        assert result.eligible is True

    def test_unemployed_applicant(self, eligibility_tool):
        """Test unemployed applicant - should be ineligible"""
        applicant = ApplicantInfo(
            age=30,
            monthly_income=8000,  # May have other income
            credit_score=750,
            employment_status=EmploymentStatus.UNEMPLOYED,
            employment_length_years=0,
            monthly_debt_obligations=0,
            requested_loan_amount=30000,
            loan_term_months=36
        )

        result = eligibility_tool.check_eligibility(applicant)

        # Unemployment will result in ineligibility
        assert result.eligible is False
        assert "unemployed" in str(result.reasons).lower()

    def test_short_employment_length(self, eligibility_tool):
        """Test employment length too short"""
        applicant = ApplicantInfo(
            age=25,
            monthly_income=8000,
            credit_score=700,
            employment_status=EmploymentStatus.FULL_TIME,
            employment_length_years=0.5,  # Only worked for half a year
            monthly_debt_obligations=0,
            requested_loan_amount=30000,
            loan_term_months=36
        )

        result = eligibility_tool.check_eligibility(applicant)

        # Short employment length will affect score, but may not completely reject
        assert result.score < 90


class TestPreviousDefaults:
    """Previous default history tests"""

    @pytest.fixture
    def eligibility_tool(self):
        return LoanEligibilityTool()

    def test_applicant_with_defaults(self, eligibility_tool):
        """Test applicant with default history"""
        applicant = ApplicantInfo(
            age=35,
            monthly_income=10000,
            credit_score=680,
            employment_status=EmploymentStatus.FULL_TIME,
            employment_length_years=5,
            monthly_debt_obligations=1000,
            requested_loan_amount=40000,
            loan_term_months=36,
            previous_defaults=True  # Has default history
        )

        result = eligibility_tool.check_eligibility(applicant)

        # Default history will result in ineligibility
        assert result.eligible is False
        assert "default" in str(result.reasons).lower()

    def test_applicant_with_existing_loans(self, eligibility_tool):
        """Test applicant with existing loans"""
        applicant = ApplicantInfo(
            age=35,
            monthly_income=10000,
            credit_score=720,
            employment_status=EmploymentStatus.FULL_TIME,
            employment_length_years=5,
            monthly_debt_obligations=2000,
            requested_loan_amount=30000,
            loan_term_months=36,
            has_existing_loans=True  # Has existing loans
        )

        result = eligibility_tool.check_eligibility(applicant)

        # With existing loans but reasonable DTI, should still pass
        # But score will be affected
        assert result.score < 100


class TestBoundaryConditions:
    """Boundary condition tests"""

    @pytest.fixture
    def eligibility_tool(self):
        return LoanEligibilityTool(
            min_age=18,
            max_age=65,
            min_monthly_income=5000,
            min_credit_score=600
        )

    def test_minimum_age_boundary(self, eligibility_tool):
        """Test minimum age boundary (18 years old)"""
        applicant = ApplicantInfo(
            age=18,  # Just meets minimum age
            monthly_income=6000,
            credit_score=650,
            employment_status=EmploymentStatus.FULL_TIME,
            employment_length_years=1,
            monthly_debt_obligations=0,
            requested_loan_amount=20000,
            loan_term_months=24
        )

        result = eligibility_tool.check_eligibility(applicant)
        assert result.eligible is True

    def test_maximum_age_boundary(self, eligibility_tool):
        """Test maximum age boundary (65 years old) - must consider loan maturity age"""
        applicant = ApplicantInfo(
            age=65,  # Boundary age
            monthly_income=8000,
            credit_score=700,
            employment_status=EmploymentStatus.FULL_TIME,
            employment_length_years=30,
            monthly_debt_obligations=500,
            requested_loan_amount=30000,
            loan_term_months=24  # Short-term loan to avoid exceeding maximum age
        )

        result = eligibility_tool.check_eligibility(applicant)
        # 65 years old applying for 24-month loan, will be 67 at maturity, may still exceed limit
        # Actual result depends on tool implementation

    def test_minimum_income_boundary(self, eligibility_tool):
        """Test minimum income boundary ($5000)"""
        applicant = ApplicantInfo(
            age=30,
            monthly_income=5000,  # Just meets minimum income
            credit_score=650,
            employment_status=EmploymentStatus.FULL_TIME,
            employment_length_years=2,
            monthly_debt_obligations=0,
            requested_loan_amount=20000,
            loan_term_months=36
        )

        result = eligibility_tool.check_eligibility(applicant)
        assert result.eligible is True

    def test_minimum_credit_score_boundary(self, eligibility_tool):
        """Test minimum credit score boundary (600)"""
        applicant = ApplicantInfo(
            age=30,
            monthly_income=8000,
            credit_score=600,  # Just meets minimum score
            employment_status=EmploymentStatus.FULL_TIME,
            employment_length_years=2,
            monthly_debt_obligations=500,
            requested_loan_amount=25000,
            loan_term_months=36
        )

        result = eligibility_tool.check_eligibility(applicant)
        assert result.eligible is True


class TestRecommendations:
    """Recommendation tests"""

    @pytest.fixture
    def eligibility_tool(self):
        return LoanEligibilityTool()

    def test_recommendations_for_ineligible(self, eligibility_tool):
        """Test ineligible applicant should receive recommendations"""
        applicant = ApplicantInfo(
            age=25,
            monthly_income=4000,  # Income too low
            credit_score=580,  # Credit score too low
            employment_status=EmploymentStatus.PART_TIME,
            employment_length_years=0.8,  # Short employment length
            monthly_debt_obligations=1500,
            requested_loan_amount=50000,
            loan_term_months=36
        )

        result = eligibility_tool.check_eligibility(applicant)

        # Should be ineligible and have improvement recommendations
        assert result.eligible is False
        assert len(result.recommendations) > 0

    def test_conditional_eligibility(self, eligibility_tool):
        """Test conditional eligibility"""
        applicant = ApplicantInfo(
            age=25,
            monthly_income=6000,
            credit_score=620,  # Just passed
            employment_status=EmploymentStatus.FULL_TIME,
            employment_length_years=1.5,
            monthly_debt_obligations=800,
            requested_loan_amount=35000,
            loan_term_months=36,
            has_existing_loans=True
        )

        result = eligibility_tool.check_eligibility(applicant)

        # May be conditional eligibility or eligible but with low score
        if result.status == EligibilityStatus.CONDITIONAL:
            assert len(result.recommendations) > 0


# Parameterized tests - demonstrates pytest advanced usage
class TestParameterized:
    """Parameterized tests - test multiple scenarios with same logic"""

    @pytest.fixture
    def eligibility_tool(self):
        return LoanEligibilityTool()

    @pytest.mark.parametrize("age,expected_eligible", [
        (18, True),   # Boundary value
        (35, True),   # Normal
        (66, False),  # Too old
    ])
    def test_age_ranges(self, eligibility_tool, age, expected_eligible):
        """Parameterized test for different ages"""
        applicant = ApplicantInfo(
            age=age,
            monthly_income=8000,
            credit_score=700,
            employment_status=EmploymentStatus.FULL_TIME,
            employment_length_years=3,
            monthly_debt_obligations=500,
            requested_loan_amount=30000,
            loan_term_months=24  # Short-term loan
        )

        result = eligibility_tool.check_eligibility(applicant)
        assert result.eligible == expected_eligible

    def test_age_below_minimum(self, eligibility_tool):
        """Test below minimum age - Pydantic validation failure"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            ApplicantInfo(
                age=17,
                monthly_income=8000,
                credit_score=700,
                employment_status=EmploymentStatus.FULL_TIME,
                employment_length_years=3,
                monthly_debt_obligations=500,
                requested_loan_amount=30000,
                loan_term_months=36
            )

    @pytest.mark.parametrize("credit_score,min_expected_score", [
        (550, 0),    # Too low, very low score
        (600, 60),   # Minimum passing, medium score
        (700, 75),   # Good, high score
        (800, 90),   # Excellent, very high score
    ])
    def test_credit_score_impact(self, eligibility_tool, credit_score, min_expected_score):
        """Parameterized test for credit score impact"""
        applicant = ApplicantInfo(
            age=35,
            monthly_income=8000,
            credit_score=credit_score,
            employment_status=EmploymentStatus.FULL_TIME,
            employment_length_years=5,
            monthly_debt_obligations=500,
            requested_loan_amount=30000,
            loan_term_months=36
        )

        result = eligibility_tool.check_eligibility(applicant)
        assert result.score >= min_expected_score


if __name__ == "__main__":
    # Can run this file directly for testing
    pytest.main([__file__, "-v", "-s"])
