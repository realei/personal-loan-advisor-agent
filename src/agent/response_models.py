"""Pydantic response models for structured agent output.

This module defines structured output models that ensure deterministic,
type-safe responses from the loan advisor agent.

Design Principles:
- Deterministic: Same input -> Same output structure
- Type-safe: All fields are validated by Pydantic
- Parseable: Easy to extract data programmatically
- Informative: Contains both summary and detailed data
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


# =============================================================================
# TOOL RESULT MODELS
# =============================================================================

class EligibilityResult(BaseModel):
    """Structured result for loan eligibility check."""

    eligible: bool = Field(description="Whether applicant is eligible")
    status: Literal["approved", "conditional", "denied"] = Field(
        description="Eligibility status"
    )
    score: float = Field(ge=0, le=100, description="Eligibility score (0-100)")
    reasons: list[str] = Field(default_factory=list, description="Assessment reasons")
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendations for applicant"
    )


class PaymentResult(BaseModel):
    """Structured result for loan payment calculation."""

    loan_amount: float = Field(gt=0, description="Principal loan amount")
    annual_interest_rate: float = Field(ge=0, description="Annual interest rate")
    loan_term_months: int = Field(gt=0, description="Loan term in months")
    monthly_payment: float = Field(gt=0, description="Monthly payment amount")
    total_payment: float = Field(gt=0, description="Total payment over loan term")
    total_interest: float = Field(ge=0, description="Total interest paid")
    interest_percentage: float = Field(
        ge=0,
        description="Interest as percentage of principal"
    )


class AffordabilityResult(BaseModel):
    """Structured result for affordability check."""

    affordable: bool = Field(description="Whether loan is affordable")
    monthly_income: float = Field(gt=0, description="Monthly income")
    existing_debt: float = Field(ge=0, description="Existing monthly debt")
    monthly_payment: float = Field(gt=0, description="New loan monthly payment")
    total_monthly_debt: float = Field(ge=0, description="Total monthly debt")
    dti_ratio: float = Field(ge=0, le=1, description="Debt-to-income ratio")
    max_recommended_dti: float = Field(
        ge=0, le=1,
        description="Maximum recommended DTI"
    )
    message: str = Field(description="Affordability analysis message")


class TermComparisonItem(BaseModel):
    """Single term option in comparison."""

    term_months: int = Field(gt=0, description="Term in months")
    term_years: float = Field(gt=0, description="Term in years")
    monthly_payment: float = Field(gt=0, description="Monthly payment")
    total_payment: float = Field(gt=0, description="Total payment")
    total_interest: float = Field(ge=0, description="Total interest")
    interest_percentage: float = Field(ge=0, description="Interest as % of principal")


class TermComparisonResult(BaseModel):
    """Structured result for loan term comparison."""

    loan_amount: float = Field(gt=0, description="Loan amount compared")
    annual_interest_rate: float = Field(ge=0, description="Interest rate used")
    options: list[TermComparisonItem] = Field(description="Term options compared")
    recommendation: str = Field(description="Recommendation based on comparison")


class MaxLoanResult(BaseModel):
    """Structured result for max affordable loan calculation."""

    max_loan_amount: float = Field(ge=0, description="Maximum affordable loan")
    monthly_income: float = Field(gt=0, description="Monthly income")
    existing_debt: float = Field(ge=0, description="Existing monthly debt")
    max_monthly_payment: float = Field(ge=0, description="Max affordable payment")
    term_months: int = Field(gt=0, description="Loan term in months")
    annual_interest_rate: float = Field(ge=0, description="Interest rate")
    message: str = Field(description="Analysis message")


class HomeAffordabilityResult(BaseModel):
    """Structured result for home affordability calculation."""

    affordable: bool = Field(description="Whether home purchase is affordable")
    max_home_price: float = Field(ge=0, description="Maximum home price")
    max_loan_amount: float = Field(ge=0, description="Maximum loan amount")
    required_down_payment: float = Field(ge=0, description="Required down payment")
    down_payment_percentage: float = Field(
        ge=0, le=1,
        description="Down payment as percentage"
    )
    monthly_payment: float = Field(ge=0, description="Monthly payment")
    ltv_ratio: float = Field(ge=0, le=1, description="Loan-to-value ratio")
    dti_ratio: float = Field(ge=0, le=1, description="Debt-to-income ratio")
    residency: str = Field(description="Residency status")
    property_type: str = Field(description="Property type")
    message: str = Field(description="Analysis message")


class MortgagePaymentResult(BaseModel):
    """Structured result for mortgage payment calculation."""

    valid: bool = Field(description="Whether calculation is valid")
    home_price: float = Field(gt=0, description="Home price")
    down_payment: float = Field(ge=0, description="Down payment amount")
    down_payment_percentage: float = Field(
        ge=0, le=1,
        description="Down payment percentage"
    )
    loan_amount: float = Field(ge=0, description="Loan amount")
    ltv_ratio: float = Field(ge=0, le=1, description="Loan-to-value ratio")
    max_ltv_allowed: float = Field(ge=0, le=1, description="Max LTV allowed")
    monthly_payment: float = Field(ge=0, description="Monthly payment")
    total_payment: float = Field(ge=0, description="Total payment")
    total_interest: float = Field(ge=0, description="Total interest")
    annual_interest_rate: float = Field(ge=0, description="Interest rate")
    loan_term_years: int = Field(gt=0, description="Loan term in years")
    message: Optional[str] = Field(default=None, description="Additional message")


class CarLoanResult(BaseModel):
    """Structured result for car loan calculation."""

    valid: bool = Field(description="Whether calculation is valid")
    car_price: float = Field(gt=0, description="Vehicle price")
    down_payment: float = Field(ge=0, description="Down payment")
    down_payment_percentage: float = Field(
        ge=0, le=1,
        description="Down payment percentage"
    )
    loan_amount: float = Field(ge=0, description="Loan amount")
    ltv_ratio: float = Field(ge=0, le=1, description="Loan-to-value ratio")
    monthly_payment: float = Field(ge=0, description="Monthly payment")
    total_payment: float = Field(ge=0, description="Total payment")
    total_interest: float = Field(ge=0, description="Total interest")
    annual_interest_rate: float = Field(ge=0, description="Interest rate")
    loan_term_months: int = Field(gt=0, description="Loan term in months")
    message: Optional[str] = Field(default=None, description="Additional message")


class EarlyPayoffResult(BaseModel):
    """Structured result for early payoff calculation."""

    original_term_months: int = Field(gt=0, description="Original loan term")
    new_term_months: int = Field(gt=0, description="New term with extra payments")
    months_saved: int = Field(ge=0, description="Months saved")
    years_saved: float = Field(ge=0, description="Years saved")
    original_monthly_payment: float = Field(gt=0, description="Original payment")
    new_monthly_payment: float = Field(gt=0, description="New payment with extra")
    extra_monthly_payment: float = Field(gt=0, description="Extra payment amount")
    original_total_interest: float = Field(ge=0, description="Original total interest")
    new_total_interest: float = Field(ge=0, description="New total interest")
    interest_saved: float = Field(ge=0, description="Interest saved")
    message: str = Field(description="Summary message")


# =============================================================================
# MAIN AGENT RESPONSE MODEL
# =============================================================================

class LoanAdvisorResponse(BaseModel):
    """Main structured response model for loan advisor agent.

    This model ensures deterministic, parseable output from the agent.
    The agent will always return data in this exact structure.
    """

    # Action metadata
    action: Literal[
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
    ] = Field(description="The type of action performed")

    # Tool execution info
    tool_called: Optional[str] = Field(
        default=None,
        description="Name of tool called, if any"
    )

    # Result data (one of these will be populated based on action)
    eligibility: Optional[EligibilityResult] = None
    payment: Optional[PaymentResult] = None
    affordability: Optional[AffordabilityResult] = None
    term_comparison: Optional[TermComparisonResult] = None
    max_loan: Optional[MaxLoanResult] = None
    home_affordability: Optional[HomeAffordabilityResult] = None
    mortgage: Optional[MortgagePaymentResult] = None
    car_loan: Optional[CarLoanResult] = None
    early_payoff: Optional[EarlyPayoffResult] = None

    # Human-readable summary
    summary: str = Field(
        description="Brief one-line summary of the result"
    )

    # Detailed explanation
    details: str = Field(
        description="Detailed explanation in markdown format"
    )

    # Actionable recommendations
    recommendations: list[str] = Field(
        default_factory=list,
        description="List of recommendations for the user"
    )

    # Warnings if any
    warnings: list[str] = Field(
        default_factory=list,
        description="Any warnings or concerns"
    )

    # Follow-up questions (for conversational flow)
    follow_up_questions: list[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions"
    )


# =============================================================================
# SIMPLE RESPONSE MODEL (Alternative - lighter weight)
# =============================================================================

class SimpleLoanResponse(BaseModel):
    """Simplified response model for basic use cases.

    Use this when you need less structure but still want determinism.
    """

    success: bool = Field(description="Whether the request was successful")
    action: str = Field(description="Action performed")
    data: dict = Field(description="Result data as dictionary")
    summary: str = Field(description="Human-readable summary")
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendations"
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Main response model
    "LoanAdvisorResponse",
    "SimpleLoanResponse",
    # Result models
    "EligibilityResult",
    "PaymentResult",
    "AffordabilityResult",
    "TermComparisonItem",
    "TermComparisonResult",
    "MaxLoanResult",
    "HomeAffordabilityResult",
    "MortgagePaymentResult",
    "CarLoanResult",
    "EarlyPayoffResult",
]
