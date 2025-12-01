"""Tools for the Personal Loan Advisor Agent."""

from .financial import FinancialEngine, engine
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
    # Financial engine
    "FinancialEngine",
    "engine",
    # Eligibility
    "LoanEligibilityTool",
    "ApplicantInfo",
    "EmploymentStatus",
    "EligibilityStatus",
    "EligibilityResult",
    # Calculator
    "LoanCalculatorTool",
    "LoanRequest",
    "LoanCalculation",
    "AmortizationSchedule",
]
