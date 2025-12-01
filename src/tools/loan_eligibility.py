"""Loan Eligibility Tool - Rule-based eligibility checks for personal loans.

This tool implements banking-grade eligibility criteria including:
- Age verification
- Income requirements
- Credit score thresholds
- Debt-to-Income (DTI) ratio validation
- Employment status checks

Refactored to use FinancialEngine for DTI calculations,
ensuring consistency with LoanCalculatorTool.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .financial import engine


class EmploymentStatus(str, Enum):
    """Employment status categories."""

    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    SELF_EMPLOYED = "self_employed"
    UNEMPLOYED = "unemployed"
    RETIRED = "retired"


class EligibilityStatus(str, Enum):
    """Loan eligibility status."""

    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    CONDITIONAL = "conditional"  # Eligible with conditions


@dataclass
class EligibilityResult:
    """Result of loan eligibility check."""

    status: EligibilityStatus
    eligible: bool
    reasons: list[str]
    score: float  # 0-100, overall eligibility score
    recommendations: list[str]


class ApplicantInfo(BaseModel):
    """Applicant information for eligibility check."""

    age: int = Field(..., ge=18, le=100, description="Applicant age")
    monthly_income: float = Field(..., gt=0, description="Monthly income in local currency")
    credit_score: int = Field(..., ge=300, le=850, description="Credit score (FICO scale)")
    employment_status: EmploymentStatus = Field(..., description="Current employment status")
    employment_length_years: float = Field(
        ..., ge=0, description="Years at current employment"
    )
    monthly_debt_obligations: float = Field(
        default=0.0, ge=0, description="Total monthly debt payments"
    )
    requested_loan_amount: float = Field(..., gt=0, description="Requested loan amount")
    loan_term_months: int = Field(..., gt=0, le=60, description="Requested loan term in months")
    has_existing_loans: bool = Field(default=False, description="Has other active loans")
    previous_defaults: bool = Field(default=False, description="Previous loan defaults on record")


class LoanEligibilityTool:
    """Tool for checking loan eligibility based on banking criteria."""

    def __init__(
        self,
        min_age: int = 18,
        max_age: int = 65,
        min_monthly_income: float = 5000.0,
        min_credit_score: int = 600,
        max_dti_ratio: float = 0.5,
        min_employment_length: float = 1.0,
        max_loan_amount: float = 1000000.0,
    ):
        """Initialize eligibility tool with configurable thresholds.

        Args:
            min_age: Minimum age for loan eligibility
            max_age: Maximum age at loan maturity
            min_monthly_income: Minimum monthly income required
            min_credit_score: Minimum credit score required
            max_dti_ratio: Maximum debt-to-income ratio allowed (0.5 = 50%)
            min_employment_length: Minimum employment length in years
            max_loan_amount: Maximum loan amount allowed
        """
        self.min_age = min_age
        self.max_age = max_age
        self.min_monthly_income = min_monthly_income
        self.min_credit_score = min_credit_score
        self.max_dti_ratio = max_dti_ratio
        self.min_employment_length = min_employment_length
        self.max_loan_amount = max_loan_amount

    def check_eligibility(self, applicant: ApplicantInfo) -> EligibilityResult:
        """Check if applicant is eligible for the loan.

        Args:
            applicant: Applicant information

        Returns:
            EligibilityResult with status, reasons, and recommendations
        """
        reasons = []
        recommendations = []
        eligibility_scores = []

        # Check age
        age_check = self._check_age(applicant, reasons, recommendations, eligibility_scores)

        # Check income
        income_check = self._check_income(applicant, reasons, recommendations, eligibility_scores)

        # Check credit score
        credit_check = self._check_credit_score(
            applicant, reasons, recommendations, eligibility_scores
        )

        # Check employment
        employment_check = self._check_employment(
            applicant, reasons, recommendations, eligibility_scores
        )

        # Check DTI ratio
        dti_check = self._check_dti(applicant, reasons, recommendations, eligibility_scores)

        # Check loan amount
        amount_check = self._check_loan_amount(
            applicant, reasons, recommendations, eligibility_scores
        )

        # Check previous defaults
        default_check = self._check_defaults(applicant, reasons, recommendations, eligibility_scores)

        # Calculate overall eligibility score (weighted average)
        overall_score = sum(eligibility_scores) / len(eligibility_scores) if eligibility_scores else 0

        # Determine final status
        all_passed = all([age_check, income_check, credit_check, employment_check,
                         dti_check, amount_check, default_check])

        if all_passed:
            status = EligibilityStatus.ELIGIBLE
            eligible = True
            if not reasons:  # All checks passed without warnings
                reasons.append("All eligibility criteria met successfully")
        else:
            # Check if any critical failures
            critical_failures = [
                not age_check,
                not income_check,
                not credit_check,
                not employment_check,  # Unemployment is critical
                not dti_check,
                applicant.previous_defaults
            ]

            if any(critical_failures):
                status = EligibilityStatus.NOT_ELIGIBLE
                eligible = False
            else:
                status = EligibilityStatus.CONDITIONAL
                eligible = False
                recommendations.append(
                    "Consider improving employment stability or reducing requested loan amount"
                )

        return EligibilityResult(
            status=status,
            eligible=eligible,
            reasons=reasons,
            score=overall_score,
            recommendations=recommendations,
        )

    def _check_age(
        self,
        applicant: ApplicantInfo,
        reasons: list[str],
        recommendations: list[str],
        scores: list[float],
    ) -> bool:
        """Check age requirements."""
        loan_maturity_age = applicant.age + (applicant.loan_term_months / 12)

        if applicant.age < self.min_age:
            reasons.append(f"Age {applicant.age} is below minimum requirement of {self.min_age}")
            recommendations.append("Must be at least 18 years old to apply")
            scores.append(0.0)
            return False

        if loan_maturity_age > self.max_age:
            reasons.append(
                f"Loan maturity age {loan_maturity_age:.0f} exceeds maximum of {self.max_age}"
            )
            recommendations.append("Consider shorter loan term or apply at younger age")
            scores.append(30.0)
            return False

        scores.append(100.0)
        return True

    def _check_income(
        self,
        applicant: ApplicantInfo,
        reasons: list[str],
        recommendations: list[str],
        scores: list[float],
    ) -> bool:
        """Check income requirements."""
        if applicant.monthly_income < self.min_monthly_income:
            reasons.append(
                f"Monthly income {applicant.monthly_income:.2f} below minimum "
                f"requirement of {self.min_monthly_income:.2f}"
            )
            recommendations.append(
                f"Minimum monthly income required: {self.min_monthly_income:.2f}"
            )
            scores.append(0.0)
            return False

        # Score based on income multiples
        income_ratio = applicant.monthly_income / self.min_monthly_income
        if income_ratio >= 3:
            scores.append(100.0)
        elif income_ratio >= 2:
            scores.append(85.0)
        elif income_ratio >= 1.5:
            scores.append(70.0)
        else:
            scores.append(55.0)

        return True

    def _check_credit_score(
        self,
        applicant: ApplicantInfo,
        reasons: list[str],
        recommendations: list[str],
        scores: list[float],
    ) -> bool:
        """Check credit score requirements."""
        if applicant.credit_score < self.min_credit_score:
            reasons.append(
                f"Credit score {applicant.credit_score} below minimum of {self.min_credit_score}"
            )
            recommendations.append(
                "Improve credit score by paying bills on time and reducing credit utilization"
            )
            scores.append(0.0)
            return False

        # Score based on credit score tiers
        if applicant.credit_score >= 750:  # Excellent
            scores.append(100.0)
        elif applicant.credit_score >= 700:  # Good
            scores.append(85.0)
        elif applicant.credit_score >= 650:  # Fair
            scores.append(70.0)
        else:  # Below fair
            scores.append(55.0)

        return True

    def _check_employment(
        self,
        applicant: ApplicantInfo,
        reasons: list[str],
        recommendations: list[str],
        scores: list[float],
    ) -> bool:
        """Check employment requirements."""
        if applicant.employment_status == EmploymentStatus.UNEMPLOYED:
            reasons.append("Unemployed applicants are not eligible")
            recommendations.append("Secure employment before applying for a loan")
            scores.append(0.0)
            return False

        if applicant.employment_status == EmploymentStatus.RETIRED:
            if applicant.age < 60:
                reasons.append("Early retirement requires additional verification")
                scores.append(60.0)
            else:
                scores.append(80.0)
            return True

        if applicant.employment_length_years < self.min_employment_length:
            reasons.append(
                f"Employment length {applicant.employment_length_years:.1f} years "
                f"below minimum of {self.min_employment_length:.1f} years"
            )
            recommendations.append("Build employment history for better loan terms")
            scores.append(40.0)
            return False

        # Score based on employment stability
        if applicant.employment_length_years >= 5:
            scores.append(100.0)
        elif applicant.employment_length_years >= 3:
            scores.append(85.0)
        elif applicant.employment_length_years >= 2:
            scores.append(70.0)
        else:
            scores.append(55.0)

        return True

    def _check_dti(
        self,
        applicant: ApplicantInfo,
        reasons: list[str],
        recommendations: list[str],
        scores: list[float],
    ) -> bool:
        """Check Debt-to-Income ratio."""
        # Use FinancialEngine for consistent calculation with LoanCalculatorTool
        estimated_payment = engine.payment(
            principal=applicant.requested_loan_amount,
            rate=0.05,  # Assume 5% annual rate for eligibility check
            periods=applicant.loan_term_months
        )

        total_monthly_debt = applicant.monthly_debt_obligations + estimated_payment
        dti_ratio = total_monthly_debt / applicant.monthly_income

        if dti_ratio > self.max_dti_ratio:
            reasons.append(
                f"Debt-to-Income ratio {dti_ratio:.1%} exceeds maximum of {self.max_dti_ratio:.1%}"
            )
            recommendations.append(
                "Reduce existing debt or request smaller loan amount to improve DTI ratio"
            )
            scores.append(0.0)
            return False

        # Score based on DTI ratio
        if dti_ratio <= 0.30:
            scores.append(100.0)
        elif dti_ratio <= 0.36:
            scores.append(85.0)
        elif dti_ratio <= 0.43:
            scores.append(70.0)
        else:
            scores.append(55.0)

        return True

    def _check_loan_amount(
        self,
        applicant: ApplicantInfo,
        reasons: list[str],
        recommendations: list[str],
        scores: list[float],
    ) -> bool:
        """Check loan amount requirements."""
        if applicant.requested_loan_amount > self.max_loan_amount:
            reasons.append(
                f"Requested amount {applicant.requested_loan_amount:.2f} "
                f"exceeds maximum of {self.max_loan_amount:.2f}"
            )
            recommendations.append(f"Maximum loan amount allowed: {self.max_loan_amount:.2f}")
            scores.append(0.0)
            return False

        # Check loan-to-income ratio
        annual_income = applicant.monthly_income * 12
        loan_to_income = applicant.requested_loan_amount / annual_income

        if loan_to_income > 3:
            reasons.append(
                f"Loan amount is {loan_to_income:.1f}x annual income (very high risk)"
            )
            recommendations.append("Consider requesting smaller loan amount relative to income")
            scores.append(30.0)
            return False

        # Score based on loan-to-income ratio
        if loan_to_income <= 1:
            scores.append(100.0)
        elif loan_to_income <= 1.5:
            scores.append(85.0)
        elif loan_to_income <= 2:
            scores.append(70.0)
        else:
            scores.append(55.0)

        return True

    def _check_defaults(
        self,
        applicant: ApplicantInfo,
        reasons: list[str],
        recommendations: list[str],
        scores: list[float],
    ) -> bool:
        """Check for previous loan defaults."""
        if applicant.previous_defaults:
            reasons.append("Previous loan defaults on record - high risk")
            recommendations.append(
                "Resolve previous defaults and rebuild credit history before reapplying"
            )
            scores.append(0.0)
            return False

        scores.append(100.0)
        return True
