"""Loan Calculator Tool - Financial calculations for multiple loan types.

This tool provides:
- Monthly EMI (Equated Monthly Installment) calculation
- Total interest calculation
- Loan amortization schedule
- Affordability assessment
- Home affordability calculation (with LTV/down payment)
- Car loan comparison
- Early payoff scenarios

Supports loan types: Personal, Mortgage, Auto
All regulations (DTI, LTV, rates) are configurable via .env

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
from .loan_types import LoanType
from .loan_rules import get_mortgage_rule, get_auto_loan_rule
from ..utils.config import config


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


# =============================================================================
# MORTGAGE / HOME LOAN FUNCTIONS
# =============================================================================

def calculate_home_affordability(
    monthly_income: float,
    existing_debt_payment: float = 0.0,
    annual_interest_rate: float | None = None,
    loan_term_months: int = 360,  # 30 years default
    residency: str = "expat",
    property_type: str = "first",
    estimated_price: float = 0,
) -> dict:
    """Calculate maximum home price you can afford.

    Uses rule-based LTV based on residency and property type.

    Args:
        monthly_income: Gross monthly income
        existing_debt_payment: Existing monthly debt payments
        annual_interest_rate: Annual rate (defaults to MORTGAGE_BASE_RATE)
        loan_term_months: Loan term (default 30 years)
        residency: 'citizen', 'expat', or 'non_resident' (default: 'expat')
        property_type: 'first' or 'second' (default: 'first')
        estimated_price: Estimated property price for rule matching

    Returns:
        Dict with max_home_price, max_loan, down_payment, monthly_payment
    """
    cfg = config.mortgage

    if annual_interest_rate is None:
        annual_interest_rate = cfg.base_rate

    # Get applicable rule based on residency and property type
    rule = get_mortgage_rule(residency, property_type, estimated_price)
    max_ltv = rule.max_ltv
    min_down_pct = rule.min_down_payment

    # Calculate max monthly payment based on DTI
    max_dti = cfg.max_dti_ratio
    max_total_debt = monthly_income * max_dti
    max_mortgage_payment = max_total_debt - existing_debt_payment

    if max_mortgage_payment <= 0:
        return {
            "affordable": False,
            "message": "Existing debt exceeds DTI limit for mortgage",
            "max_home_price": 0,
            "max_loan_amount": 0,
            "required_down_payment": 0,
            "monthly_payment": 0,
        }

    # Calculate max loan amount
    max_loan = engine.max_principal(
        payment=max_mortgage_payment,
        rate=annual_interest_rate,
        periods=loan_term_months,
    )

    # Calculate max home price based on LTV
    max_home_price = max_loan / max_ltv
    required_down_payment = max_home_price * min_down_pct

    return {
        "affordable": True,
        "max_home_price": round(max_home_price, 2),
        "max_loan_amount": round(max_loan, 2),
        "required_down_payment": round(required_down_payment, 2),
        "down_payment_percentage": min_down_pct,
        "monthly_payment": round(max_mortgage_payment, 2),
        "dti_ratio": max_dti,
        "ltv_ratio": max_ltv,
        "residency": residency,
        "property_type": property_type,
        "annual_interest_rate": annual_interest_rate,
        "loan_term_months": loan_term_months,
        "loan_term_years": loan_term_months // 12,
        "message": (
            f"As {residency} buying {property_type} home with ${monthly_income:,.0f}/month income, "
            f"you can afford up to ${max_home_price:,.0f} "
            f"(LTV: {max_ltv:.0%}, down payment: ${required_down_payment:,.0f})"
        ),
    }


def calculate_mortgage_payment(
    home_price: float,
    down_payment: float | None = None,
    annual_interest_rate: float | None = None,
    loan_term_months: int = 360,
    residency: str = "expat",
    property_type: str = "first",
) -> dict:
    """Calculate mortgage payment for a specific home price.

    Uses rule-based LTV based on residency and property type.

    Args:
        home_price: Total home price
        down_payment: Down payment amount (defaults to minimum from rule)
        annual_interest_rate: Annual rate (defaults to MORTGAGE_BASE_RATE)
        loan_term_months: Loan term (default 30 years)
        residency: 'citizen', 'expat', or 'non_resident' (default: 'expat')
        property_type: 'first' or 'second' (default: 'first')

    Returns:
        Dict with loan details, monthly payment, LTV ratio
    """
    cfg = config.mortgage

    if annual_interest_rate is None:
        annual_interest_rate = cfg.base_rate

    # Get applicable rule based on residency and property type
    rule = get_mortgage_rule(residency, property_type, home_price)
    max_ltv = rule.max_ltv
    min_down_pct = rule.min_down_payment

    # Calculate down payment
    if down_payment is None:
        down_payment = home_price * min_down_pct

    # Validate LTV
    loan_amount = home_price - down_payment
    ltv_ratio = loan_amount / home_price

    if ltv_ratio > max_ltv:
        min_required_down = home_price * min_down_pct
        return {
            "valid": False,
            "message": (
                f"LTV {ltv_ratio:.1%} exceeds maximum {max_ltv:.0%} for {residency} "
                f"buying {property_type} home. Need at least ${min_required_down:,.0f} "
                f"({min_down_pct:.0%}) down payment."
            ),
        }

    # Calculate payment
    monthly_payment = engine.payment(
        principal=loan_amount,
        rate=annual_interest_rate,
        periods=loan_term_months,
    )

    total_payment = monthly_payment * loan_term_months
    total_interest = total_payment - loan_amount

    return {
        "valid": True,
        "home_price": home_price,
        "down_payment": down_payment,
        "down_payment_percentage": down_payment / home_price,
        "loan_amount": loan_amount,
        "ltv_ratio": ltv_ratio,
        "max_ltv_allowed": max_ltv,
        "residency": residency,
        "property_type": property_type,
        "monthly_payment": round(monthly_payment, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2),
        "annual_interest_rate": annual_interest_rate,
        "loan_term_months": loan_term_months,
        "loan_term_years": loan_term_months // 12,
    }


# =============================================================================
# AUTO / CAR LOAN FUNCTIONS
# =============================================================================

def calculate_car_loan(
    car_price: float,
    down_payment: float | None = None,
    annual_interest_rate: float | None = None,
    loan_term_months: int = 60,
) -> dict:
    """Calculate car loan payment.

    Args:
        car_price: Vehicle price
        down_payment: Down payment (defaults to minimum from config)
        annual_interest_rate: Annual rate (defaults to AUTO_BASE_RATE)
        loan_term_months: Loan term (default 5 years)

    Returns:
        Dict with loan details and monthly payment
    """
    cfg = config.auto_loan

    if annual_interest_rate is None:
        annual_interest_rate = cfg.base_rate

    # Calculate down payment
    if down_payment is None:
        down_payment = car_price * cfg.min_down_payment

    # Validate LTV
    loan_amount = car_price - down_payment
    ltv_ratio = loan_amount / car_price

    if ltv_ratio > cfg.max_ltv_ratio:
        return {
            "valid": False,
            "message": f"LTV {ltv_ratio:.1%} exceeds maximum {cfg.max_ltv_ratio:.0%}. "
                       f"Need at least ${car_price * cfg.min_down_payment:,.0f} down payment.",
        }

    # Calculate payment
    monthly_payment = engine.payment(
        principal=loan_amount,
        rate=annual_interest_rate,
        periods=loan_term_months,
    )

    total_payment = monthly_payment * loan_term_months
    total_interest = total_payment - loan_amount

    return {
        "valid": True,
        "car_price": car_price,
        "down_payment": down_payment,
        "down_payment_percentage": down_payment / car_price,
        "loan_amount": loan_amount,
        "ltv_ratio": ltv_ratio,
        "monthly_payment": round(monthly_payment, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2),
        "annual_interest_rate": annual_interest_rate,
        "loan_term_months": loan_term_months,
    }


def compare_car_loan_terms(
    car_price: float,
    down_payment: float | None = None,
    annual_interest_rate: float | None = None,
    terms: list[int] | None = None,
) -> pd.DataFrame:
    """Compare car loan options across different terms.

    Args:
        car_price: Vehicle price
        down_payment: Down payment amount
        annual_interest_rate: Annual rate (defaults to AUTO_BASE_RATE)
        terms: List of terms in months (default: [36, 48, 60, 72])

    Returns:
        DataFrame comparing different loan terms
    """
    cfg = config.auto_loan

    if annual_interest_rate is None:
        annual_interest_rate = cfg.base_rate

    if terms is None:
        terms = [36, 48, 60, 72]

    if down_payment is None:
        down_payment = car_price * cfg.min_down_payment

    loan_amount = car_price - down_payment
    comparisons = []

    for term in terms:
        monthly_payment = engine.payment(
            principal=loan_amount,
            rate=annual_interest_rate,
            periods=term,
        )
        total_payment = monthly_payment * term
        total_interest = total_payment - loan_amount

        comparisons.append({
            "term_months": term,
            "term_years": term / 12,
            "monthly_payment": round(monthly_payment, 2),
            "total_payment": round(total_payment, 2),
            "total_interest": round(total_interest, 2),
            "interest_percentage": round((total_interest / loan_amount) * 100, 2),
        })

    return pd.DataFrame(comparisons)


# =============================================================================
# EARLY PAYOFF CALCULATOR
# =============================================================================

def calculate_early_payoff(
    loan_amount: float,
    annual_interest_rate: float,
    loan_term_months: int,
    extra_monthly_payment: float,
) -> dict:
    """Calculate savings from making extra monthly payments.

    Args:
        loan_amount: Original loan amount
        annual_interest_rate: Annual interest rate
        loan_term_months: Original loan term in months
        extra_monthly_payment: Extra amount to pay each month

    Returns:
        Dict with payoff timeline, interest saved, and comparison
    """
    monthly_rate = annual_interest_rate / 12

    # Original loan calculation
    original_payment = engine.payment(
        principal=loan_amount,
        rate=annual_interest_rate,
        periods=loan_term_months,
    )
    original_total_interest = (original_payment * loan_term_months) - loan_amount

    # Calculate with extra payment
    total_payment = original_payment + extra_monthly_payment
    balance = loan_amount
    months_paid = 0
    total_interest_paid = 0.0

    while balance > 0 and months_paid < loan_term_months:
        months_paid += 1
        interest = balance * monthly_rate
        total_interest_paid += interest
        principal_paid = min(total_payment - interest, balance)
        balance = max(0, balance - principal_paid)

    # Calculate savings
    interest_saved = original_total_interest - total_interest_paid
    months_saved = loan_term_months - months_paid

    return {
        "original_term_months": loan_term_months,
        "new_term_months": months_paid,
        "months_saved": months_saved,
        "years_saved": round(months_saved / 12, 1),
        "original_monthly_payment": round(original_payment, 2),
        "new_monthly_payment": round(total_payment, 2),
        "extra_monthly_payment": extra_monthly_payment,
        "original_total_interest": round(original_total_interest, 2),
        "new_total_interest": round(total_interest_paid, 2),
        "interest_saved": round(interest_saved, 2),
        "message": (
            f"By paying ${extra_monthly_payment:,.0f} extra per month, you'll save "
            f"${interest_saved:,.0f} in interest and pay off {months_saved} months earlier."
        ),
    }


# =============================================================================
# FACTORY FUNCTION - Get calculator with loan-type-specific config
# =============================================================================

def get_calculator(loan_type: LoanType | str = LoanType.PERSONAL) -> LoanCalculatorTool:
    """Get a LoanCalculatorTool configured for a specific loan type.

    Args:
        loan_type: LoanType enum or string ('personal', 'mortgage', 'auto')

    Returns:
        LoanCalculatorTool with appropriate DTI ratio
    """
    if isinstance(loan_type, str):
        loan_type = LoanType(loan_type.lower())

    loan_cfg = config.get_loan_config(loan_type.value)
    return LoanCalculatorTool(max_dti_ratio=loan_cfg.max_dti_ratio)
