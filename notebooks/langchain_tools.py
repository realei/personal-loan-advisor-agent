"""LangChain Tools for Loan Advisor Agent.

This module provides LangChain-compatible tools for loan calculations,
supporting multiple loan types: Personal, Mortgage (Home), and Auto (Car).

Tools:
    - calculate_personal_loan: Personal loan payment calculation
    - calculate_mortgage: Mortgage/home loan with down payment and LTV
    - calculate_auto_loan: Auto/car loan calculation
    - check_loan_eligibility: Check if applicant qualifies for a loan
    - check_affordability: Analyze debt-to-income ratio
    - compare_loan_options: Compare different loan terms

Usage:
    from langchain_tools import get_all_tools
    tools = get_all_tools()
"""

import json
from typing import Literal
from langchain_core.tools import tool


# =============================================================================
# Loan Type Definitions
# =============================================================================

LOAN_TYPES = {
    "personal": {
        "name": "Personal Loan",
        "description": "Unsecured loan for personal expenses",
        "typical_rate_range": (0.08, 0.24),  # 8% - 24%
        "typical_term_range": (12, 84),       # 1-7 years
        "requires_collateral": False,
    },
    "mortgage": {
        "name": "Mortgage / Home Loan",
        "description": "Secured loan for property purchase",
        "typical_rate_range": (0.04, 0.08),  # 4% - 8%
        "typical_term_range": (180, 360),     # 15-30 years
        "requires_collateral": True,
        "collateral": "Real Estate",
        "max_ltv": 0.80,  # 80% loan-to-value
    },
    "auto": {
        "name": "Auto / Car Loan",
        "description": "Secured loan for vehicle purchase",
        "typical_rate_range": (0.04, 0.12),  # 4% - 12%
        "typical_term_range": (24, 84),       # 2-7 years
        "requires_collateral": True,
        "collateral": "Vehicle",
        "max_ltv": 0.90,  # 90% loan-to-value
    },
}


# =============================================================================
# Core Calculation Functions
# =============================================================================

def _calculate_monthly_payment(principal: float, annual_rate: float, months: int) -> float:
    """Calculate monthly payment using amortization formula."""
    if annual_rate == 0:
        return principal / months

    monthly_rate = annual_rate / 12
    payment = principal * (
        monthly_rate * (1 + monthly_rate) ** months
    ) / ((1 + monthly_rate) ** months - 1)
    return round(payment, 2)


def _calculate_totals(principal: float, monthly_payment: float, months: int) -> dict:
    """Calculate total payment and interest."""
    total_payment = monthly_payment * months
    total_interest = total_payment - principal
    return {
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2),
        "interest_percentage": round(total_interest / principal * 100, 2),
    }


# =============================================================================
# LangChain Tools - Personal Loan
# =============================================================================

@tool
def calculate_personal_loan(
    loan_amount: float,
    annual_interest_rate: float,
    loan_term_months: int,
) -> str:
    """Calculate monthly payment for a personal loan.

    Personal loans are unsecured loans typically used for debt consolidation,
    home improvements, medical expenses, or other personal needs.

    Args:
        loan_amount: Principal loan amount in dollars (e.g., 25000)
        annual_interest_rate: Annual interest rate as decimal (e.g., 0.10 for 10%)
        loan_term_months: Loan term in months (typically 12-84)

    Returns:
        JSON with monthly_payment, total_payment, total_interest, and loan details
    """
    monthly = _calculate_monthly_payment(loan_amount, annual_interest_rate, loan_term_months)
    totals = _calculate_totals(loan_amount, monthly, loan_term_months)

    result = {
        "loan_type": "personal",
        "loan_amount": loan_amount,
        "annual_interest_rate": annual_interest_rate,
        "loan_term_months": loan_term_months,
        "monthly_payment": monthly,
        **totals,
    }
    return json.dumps(result)


# =============================================================================
# LangChain Tools - Mortgage (Home Loan)
# =============================================================================

@tool
def calculate_mortgage(
    home_price: float,
    down_payment_percent: float,
    annual_interest_rate: float,
    loan_term_years: int,
) -> str:
    """Calculate monthly payment for a mortgage (home loan).

    Mortgages are secured loans for purchasing real estate. The home serves
    as collateral. Down payment is typically 10-20% of home price.

    Args:
        home_price: Total home price in dollars (e.g., 500000)
        down_payment_percent: Down payment as percentage (e.g., 0.20 for 20%)
        annual_interest_rate: Annual interest rate as decimal (e.g., 0.065 for 6.5%)
        loan_term_years: Loan term in years (typically 15 or 30)

    Returns:
        JSON with monthly_payment, loan_amount, down_payment, LTV ratio, and totals
    """
    down_payment = home_price * down_payment_percent
    loan_amount = home_price - down_payment
    loan_term_months = loan_term_years * 12
    ltv_ratio = loan_amount / home_price

    monthly = _calculate_monthly_payment(loan_amount, annual_interest_rate, loan_term_months)
    totals = _calculate_totals(loan_amount, monthly, loan_term_months)

    result = {
        "loan_type": "mortgage",
        "home_price": home_price,
        "down_payment": round(down_payment, 2),
        "down_payment_percent": down_payment_percent,
        "loan_amount": round(loan_amount, 2),
        "ltv_ratio": round(ltv_ratio, 3),
        "annual_interest_rate": annual_interest_rate,
        "loan_term_years": loan_term_years,
        "loan_term_months": loan_term_months,
        "monthly_payment": monthly,
        **totals,
        "ltv_warning": "LTV exceeds 80%, PMI may be required" if ltv_ratio > 0.80 else None,
    }
    return json.dumps(result)


# =============================================================================
# LangChain Tools - Auto Loan (Car Loan)
# =============================================================================

@tool
def calculate_auto_loan(
    vehicle_price: float,
    down_payment: float,
    annual_interest_rate: float,
    loan_term_months: int,
    trade_in_value: float = 0,
) -> str:
    """Calculate monthly payment for an auto (car) loan.

    Auto loans are secured loans for purchasing vehicles. The vehicle serves
    as collateral. Consider trade-in value if trading an existing vehicle.

    Args:
        vehicle_price: Total vehicle price in dollars (e.g., 35000)
        down_payment: Down payment amount in dollars (e.g., 5000)
        annual_interest_rate: Annual interest rate as decimal (e.g., 0.059 for 5.9%)
        loan_term_months: Loan term in months (typically 36, 48, 60, or 72)
        trade_in_value: Value of trade-in vehicle, if any (default 0)

    Returns:
        JSON with monthly_payment, loan_amount, effective_price, and totals
    """
    effective_price = vehicle_price - trade_in_value
    loan_amount = effective_price - down_payment
    ltv_ratio = loan_amount / vehicle_price

    monthly = _calculate_monthly_payment(loan_amount, annual_interest_rate, loan_term_months)
    totals = _calculate_totals(loan_amount, monthly, loan_term_months)

    result = {
        "loan_type": "auto",
        "vehicle_price": vehicle_price,
        "trade_in_value": trade_in_value,
        "effective_price": round(effective_price, 2),
        "down_payment": down_payment,
        "loan_amount": round(loan_amount, 2),
        "ltv_ratio": round(ltv_ratio, 3),
        "annual_interest_rate": annual_interest_rate,
        "loan_term_months": loan_term_months,
        "monthly_payment": monthly,
        **totals,
    }
    return json.dumps(result)


# =============================================================================
# LangChain Tools - Eligibility & Affordability
# =============================================================================

@tool
def check_loan_eligibility(
    age: int,
    monthly_income: float,
    credit_score: int,
    employment_status: str,
    requested_loan_amount: float,
    loan_type: str = "personal",
) -> str:
    """Check if an applicant is eligible for a loan.

    Evaluates eligibility based on age, income, credit score, and employment.
    Different loan types may have different requirements.

    Args:
        age: Applicant's age in years
        monthly_income: Monthly gross income in dollars
        credit_score: Credit score (300-850 range)
        employment_status: One of: full_time, part_time, self_employed, unemployed
        requested_loan_amount: Desired loan amount in dollars
        loan_type: Type of loan: personal, mortgage, or auto

    Returns:
        JSON with eligibility decision, credit rating, and detailed reasons
    """
    reasons = []
    is_eligible = True

    # Age check (18-65 for most loans)
    min_age, max_age = 18, 65
    if age < min_age:
        is_eligible = False
        reasons.append(f"Age {age} below minimum ({min_age})")
    elif age > max_age:
        is_eligible = False
        reasons.append(f"Age {age} above maximum ({max_age})")
    else:
        reasons.append("Age requirement met")

    # Income check
    min_income = 3000 if loan_type == "personal" else 4000
    if monthly_income < min_income:
        is_eligible = False
        reasons.append(f"Income ${monthly_income:,.0f} below minimum (${min_income:,.0f})")
    else:
        reasons.append(f"Income requirement met (${monthly_income:,.0f}/month)")

    # Credit score check
    min_scores = {"personal": 600, "mortgage": 620, "auto": 580}
    min_score = min_scores.get(loan_type, 600)

    if credit_score < min_score:
        is_eligible = False
        credit_rating = "Poor"
        reasons.append(f"Credit score {credit_score} below minimum ({min_score})")
    elif credit_score < 670:
        credit_rating = "Fair"
        reasons.append(f"Credit score acceptable ({credit_score})")
    elif credit_score < 740:
        credit_rating = "Good"
        reasons.append(f"Credit score good ({credit_score})")
    else:
        credit_rating = "Excellent"
        reasons.append(f"Credit score excellent ({credit_score})")

    # Employment check
    if employment_status == "unemployed":
        is_eligible = False
        reasons.append("Employment required for loan approval")
    else:
        reasons.append(f"Employment status acceptable ({employment_status})")

    # Simple DTI estimate
    estimated_payment = requested_loan_amount / 36
    dti_estimate = estimated_payment / monthly_income
    max_dti = 0.43 if loan_type == "mortgage" else 0.50

    if dti_estimate > max_dti:
        is_eligible = False
        reasons.append(f"Estimated DTI {dti_estimate:.1%} exceeds maximum ({max_dti:.0%})")

    result = {
        "loan_type": loan_type,
        "is_eligible": is_eligible,
        "credit_rating": credit_rating,
        "estimated_dti": round(dti_estimate, 3),
        "max_dti": max_dti,
        "reasons": reasons,
        "max_recommended_loan": round(monthly_income * max_dti * 36, 2),
    }
    return json.dumps(result)


@tool
def check_affordability(
    monthly_income: float,
    existing_monthly_debt: float,
    proposed_loan_amount: float,
    annual_interest_rate: float,
    loan_term_months: int,
) -> str:
    """Analyze if a loan is affordable based on debt-to-income ratio.

    Calculates current and projected DTI ratios to determine if adding
    a new loan payment would exceed recommended limits (typically 43-50%).

    Args:
        monthly_income: Monthly gross income in dollars
        existing_monthly_debt: Current monthly debt payments (credit cards, other loans)
        proposed_loan_amount: New loan amount being considered
        annual_interest_rate: Interest rate for the new loan
        loan_term_months: Term of the new loan in months

    Returns:
        JSON with affordability analysis including current/new DTI and recommendation
    """
    new_payment = _calculate_monthly_payment(
        proposed_loan_amount, annual_interest_rate, loan_term_months
    )

    current_dti = existing_monthly_debt / monthly_income
    new_total_debt = existing_monthly_debt + new_payment
    new_dti = new_total_debt / monthly_income

    max_dti = 0.50
    is_affordable = new_dti <= max_dti
    remaining_capacity = (monthly_income * max_dti) - new_total_debt

    if new_dti <= 0.30:
        assessment = "Excellent - very comfortable debt level"
    elif new_dti <= 0.40:
        assessment = "Good - manageable debt level"
    elif new_dti <= 0.50:
        assessment = "Acceptable - at the higher end of recommended range"
    else:
        assessment = "Not recommended - debt exceeds safe limits"

    result = {
        "is_affordable": is_affordable,
        "monthly_income": monthly_income,
        "existing_monthly_debt": existing_monthly_debt,
        "new_monthly_payment": new_payment,
        "total_monthly_debt": round(new_total_debt, 2),
        "current_dti": round(current_dti, 3),
        "new_dti": round(new_dti, 3),
        "max_dti": max_dti,
        "remaining_capacity": round(max(0, remaining_capacity), 2),
        "assessment": assessment,
    }
    return json.dumps(result)


@tool
def compare_loan_options(
    loan_amount: float,
    annual_interest_rate: float,
    term_options: str = "36,48,60",
) -> str:
    """Compare monthly payments across different loan terms.

    Helps users understand the trade-off between monthly payment and
    total interest paid for different loan durations.

    Args:
        loan_amount: Principal loan amount in dollars
        annual_interest_rate: Annual interest rate as decimal
        term_options: Comma-separated loan terms in months (default: "36,48,60")

    Returns:
        JSON with comparison of monthly payment and total interest for each term
    """
    terms = [int(t.strip()) for t in term_options.split(",")]
    comparisons = []

    for months in terms:
        monthly = _calculate_monthly_payment(loan_amount, annual_interest_rate, months)
        totals = _calculate_totals(loan_amount, monthly, months)

        comparisons.append({
            "term_months": months,
            "term_years": round(months / 12, 1),
            "monthly_payment": monthly,
            "total_interest": totals["total_interest"],
            "total_payment": totals["total_payment"],
        })

    # Sort by term length
    comparisons.sort(key=lambda x: x["term_months"])

    # Add savings comparison (vs longest term)
    if len(comparisons) > 1:
        longest = comparisons[-1]
        for comp in comparisons:
            comp["interest_savings_vs_longest"] = round(
                longest["total_interest"] - comp["total_interest"], 2
            )

    result = {
        "loan_amount": loan_amount,
        "annual_interest_rate": annual_interest_rate,
        "comparisons": comparisons,
        "recommendation": (
            f"Shorter terms save money on interest but have higher monthly payments. "
            f"The {comparisons[0]['term_months']}-month option saves "
            f"${comparisons[0].get('interest_savings_vs_longest', 0):,.2f} in interest."
        ) if len(comparisons) > 1 else None,
    }
    return json.dumps(result)


# =============================================================================
# Tool Registry
# =============================================================================

def get_all_tools():
    """Get all available LangChain tools for the loan advisor agent."""
    return [
        calculate_personal_loan,
        calculate_mortgage,
        calculate_auto_loan,
        check_loan_eligibility,
        check_affordability,
        compare_loan_options,
    ]


def get_tool_descriptions() -> str:
    """Get formatted descriptions of all available tools."""
    tools = get_all_tools()
    descriptions = []
    for t in tools:
        descriptions.append(f"- **{t.name}**: {t.description.split('.')[0]}")
    return "\n".join(descriptions)


# For direct testing
if __name__ == "__main__":
    print("Available Tools:")
    print(get_tool_descriptions())
    print("\n--- Testing calculate_personal_loan ---")
    print(calculate_personal_loan.invoke({
        "loan_amount": 25000,
        "annual_interest_rate": 0.10,
        "loan_term_months": 48
    }))
