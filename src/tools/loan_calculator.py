"""Loan Calculator Tool - Financial calculations for personal loans.

This tool provides:
- Monthly EMI (Equated Monthly Installment) calculation
- Total interest calculation
- Loan amortization schedule
- Affordability assessment

Refactored to use numpy-financial via FinancialEngine for:
- Industry-standard calculations (Excel-compatible)
- Better performance (vectorized operations)
- Easier maintenance and auditing
"""

from dataclasses import dataclass
from typing import Optional

import pandas as pd
from pydantic import BaseModel, Field

from .financial import engine


@dataclass
class LoanCalculation:
    """Result of loan calculation."""

    monthly_payment: float
    total_payment: float
    total_interest: float
    total_principal: float
    loan_term_months: int
    annual_interest_rate: float
    effective_monthly_rate: float


@dataclass
class AmortizationSchedule:
    """Loan amortization schedule."""

    schedule: pd.DataFrame  # Columns: month, payment, principal, interest, balance
    summary: LoanCalculation


class LoanRequest(BaseModel):
    """Loan calculation request parameters."""

    loan_amount: float = Field(..., gt=0, description="Principal loan amount")
    annual_interest_rate: float = Field(
        ..., ge=0, le=1, description="Annual interest rate (e.g., 0.0499 for 4.99%)"
    )
    loan_term_months: int = Field(..., gt=0, le=360, description="Loan term in months")
    monthly_income: Optional[float] = Field(
        None, gt=0, description="Monthly income for affordability check"
    )


class LoanCalculatorTool:
    """Tool for calculating loan payments and schedules.

    Uses FinancialEngine internally for numpy-financial based calculations.
    Public interface remains unchanged for backward compatibility.
    """

    def __init__(self, max_dti_ratio: float = 0.5):
        """Initialize loan calculator.

        Args:
            max_dti_ratio: Maximum recommended debt-to-income ratio (default 50%)
        """
        self.max_dti_ratio = max_dti_ratio

    def calculate_monthly_payment(self, loan_request: LoanRequest) -> LoanCalculation:
        """Calculate monthly EMI payment using numpy-financial.

        Formula: EMI = P × r × (1 + r)^n / ((1 + r)^n - 1)
        Where:
            P = Principal loan amount
            r = Monthly interest rate
            n = Number of months

        Args:
            loan_request: Loan parameters

        Returns:
            LoanCalculation with monthly payment and totals
        """
        P = loan_request.loan_amount
        annual_rate = loan_request.annual_interest_rate
        n = loan_request.loan_term_months

        # Use FinancialEngine for calculation
        monthly_payment = engine.payment(
            principal=P,
            rate=annual_rate,
            periods=n
        )

        # Calculate totals
        total_payment = monthly_payment * n
        total_interest = total_payment - P

        return LoanCalculation(
            monthly_payment=monthly_payment,
            total_payment=total_payment,
            total_interest=total_interest,
            total_principal=P,
            loan_term_months=n,
            annual_interest_rate=annual_rate,
            effective_monthly_rate=annual_rate / 12,
        )

    def generate_amortization_schedule(
        self, loan_request: LoanRequest
    ) -> AmortizationSchedule:
        """Generate detailed month-by-month amortization schedule.

        Uses vectorized numpy-financial operations for better performance.

        Args:
            loan_request: Loan parameters

        Returns:
            AmortizationSchedule with full payment breakdown
        """
        calculation = self.calculate_monthly_payment(loan_request)

        # Use FinancialEngine for vectorized amortization table
        schedule_df = engine.amortization_table(
            principal=loan_request.loan_amount,
            rate=loan_request.annual_interest_rate,
            periods=loan_request.loan_term_months
        )

        return AmortizationSchedule(schedule=schedule_df, summary=calculation)

    def check_affordability(
        self, loan_request: LoanRequest, existing_monthly_debt: float = 0.0
    ) -> dict:
        """Check if loan is affordable based on income.

        Args:
            loan_request: Loan parameters (must include monthly_income)
            existing_monthly_debt: Existing monthly debt obligations

        Returns:
            Dictionary with affordability assessment
        """
        if loan_request.monthly_income is None:
            return {
                "affordable": None,
                "message": "Monthly income required for affordability check",
            }

        calculation = self.calculate_monthly_payment(loan_request)
        total_monthly_debt = calculation.monthly_payment + existing_monthly_debt
        dti_ratio = total_monthly_debt / loan_request.monthly_income

        affordable = dti_ratio <= self.max_dti_ratio

        return {
            "affordable": affordable,
            "monthly_payment": calculation.monthly_payment,
            "monthly_income": loan_request.monthly_income,
            "existing_debt": existing_monthly_debt,
            "total_monthly_debt": total_monthly_debt,
            "dti_ratio": dti_ratio,
            "max_recommended_dti": self.max_dti_ratio,
            "message": self._generate_affordability_message(dti_ratio, affordable),
        }

    def _generate_affordability_message(self, dti_ratio: float, affordable: bool) -> str:
        """Generate human-readable affordability message."""
        if affordable:
            if dti_ratio <= 0.30:
                return (
                    f"Excellent affordability! DTI ratio of {dti_ratio:.1%} is very healthy."
                )
            elif dti_ratio <= 0.36:
                return f"Good affordability. DTI ratio of {dti_ratio:.1%} is within comfort zone."
            else:
                return f"Acceptable affordability. DTI ratio of {dti_ratio:.1%} is manageable but getting high."
        else:
            return (
                f"Warning: DTI ratio of {dti_ratio:.1%} exceeds recommended maximum of "
                f"{self.max_dti_ratio:.1%}. Consider reducing loan amount or term."
            )

    def compare_loan_options(
        self, loan_amount: float, annual_rate: float, terms: list[int]
    ) -> pd.DataFrame:
        """Compare different loan term options.

        Args:
            loan_amount: Principal amount
            annual_rate: Annual interest rate
            terms: List of loan terms in months to compare

        Returns:
            DataFrame comparing different loan terms
        """
        comparisons = []

        for term in terms:
            loan_request = LoanRequest(
                loan_amount=loan_amount, annual_interest_rate=annual_rate, loan_term_months=term
            )
            calc = self.calculate_monthly_payment(loan_request)

            comparisons.append(
                {
                    "term_months": term,
                    "term_years": term / 12,
                    "monthly_payment": calc.monthly_payment,
                    "total_payment": calc.total_payment,
                    "total_interest": calc.total_interest,
                    "interest_percentage": (calc.total_interest / loan_amount) * 100,
                }
            )

        return pd.DataFrame(comparisons)

    def calculate_max_loan_amount(
        self,
        monthly_income: float,
        annual_interest_rate: float,
        loan_term_months: int,
        existing_monthly_debt: float = 0.0,
    ) -> dict:
        """Calculate maximum affordable loan amount.

        Uses numpy-financial's PV function for reverse EMI calculation.

        Args:
            monthly_income: Monthly income
            annual_interest_rate: Annual interest rate
            loan_term_months: Desired loan term
            existing_monthly_debt: Existing monthly debt obligations

        Returns:
            Dictionary with maximum loan amount and details
        """
        # Maximum affordable monthly payment
        max_monthly_payment = (monthly_income * self.max_dti_ratio) - existing_monthly_debt

        if max_monthly_payment <= 0:
            return {
                "max_loan_amount": 0,
                "max_monthly_payment": max_monthly_payment,
                "message": "Existing debt already exceeds recommended DTI ratio",
            }

        # Use FinancialEngine for reverse calculation
        max_principal = engine.max_principal(
            payment=max_monthly_payment,
            rate=annual_interest_rate,
            periods=loan_term_months
        )

        return {
            "max_loan_amount": max_principal,
            "max_monthly_payment": max_monthly_payment,
            "monthly_income": monthly_income,
            "existing_debt": existing_monthly_debt,
            "dti_ratio": self.max_dti_ratio,
            "term_months": loan_term_months,
            "annual_interest_rate": annual_interest_rate,
            "message": f"Based on {self.max_dti_ratio:.0%} DTI ratio, you can afford up to ${max_principal:,.2f}",
        }
