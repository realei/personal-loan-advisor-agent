"""Tools for the Personal Loan Advisor Agent."""

from .loan_eligibility import (
    LoanEligibilityTool,
    ApplicantInfo,
    EmploymentStatus,
    EligibilityStatus,
    EligibilityResult,
)
from .loan_calculator import (
    LoanCalculatorTool,
    LoanRequest,
    LoanCalculation,
    AmortizationSchedule,
)

__all__ = [
    "LoanEligibilityTool",
    "ApplicantInfo",
    "EmploymentStatus",
    "EligibilityStatus",
    "EligibilityResult",
    "LoanCalculatorTool",
    "LoanRequest",
    "LoanCalculation",
    "AmortizationSchedule",
]
