"""Loan Advisor Tools - Standalone tool functions for Agno agent.

This module defines all loan-related tools as standalone functions following
Agno best practices. Tools are defined as simple functions without class wrapping.

Supports loan types: Personal, Mortgage, Auto
"""

from typing import Optional
from agno.tools import tool
from src.tools.loan_eligibility import (
    LoanEligibilityTool,
    ApplicantInfo,
    EmploymentStatus,
    get_eligibility_checker,
)
from src.tools.loan_calculator import (
    LoanCalculatorTool,
    LoanRequest,
    get_calculator,
    calculate_home_affordability,
    calculate_mortgage_payment,
    calculate_car_loan,
    compare_car_loan_terms,
    calculate_early_payoff,
)
from src.tools.loan_types import LoanType
from src.utils.config import config
from src.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Initialize tool instances (these are utility classes, not agents)
eligibility_checker = LoanEligibilityTool(
    min_age=config.loan.min_age,
    max_age=config.loan.max_age,
    min_monthly_income=config.loan.min_income,
    min_credit_score=config.loan.min_credit_score,
    max_dti_ratio=config.loan.max_dti_ratio,
    min_employment_length=1.0,
    max_loan_amount=config.loan.max_loan_amount,
)

loan_calculator = LoanCalculatorTool(max_dti_ratio=config.loan.max_dti_ratio)


@tool(name="check_loan_eligibility", show_result=True)
def check_loan_eligibility(
    age: int,
    monthly_income: float,
    credit_score: int,
    employment_status: str,
    employment_length_years: float,
    requested_loan_amount: float,
    loan_term_months: int,
    monthly_debt_obligations: float = 0.0,
    has_existing_loans: bool = False,
    previous_defaults: bool = False,
) -> str:
    """Check if customer is eligible for a personal loan.

    This tool assesses loan eligibility based on the applicant's profile including
    age, income, credit score, employment status, and debt obligations.

    Args:
        age: Customer age (must be between min and max age limits)
        monthly_income: Monthly income in local currency
        credit_score: Credit score (300-850 range)
        employment_status: One of: full_time, part_time, self_employed, unemployed, retired
        employment_length_years: Years at current employment
        requested_loan_amount: Desired loan amount
        loan_term_months: Desired loan term in months
        monthly_debt_obligations: Total monthly debt payments (default: 0)
        has_existing_loans: Whether customer has other active loans (default: False)
        previous_defaults: Whether customer has previous loan defaults (default: False)

    Returns:
        Detailed eligibility assessment with status, score, and recommendations
    """
    try:
        # Map employment status string to enum
        emp_status_map = {
            "full_time": EmploymentStatus.FULL_TIME,
            "part_time": EmploymentStatus.PART_TIME,
            "self_employed": EmploymentStatus.SELF_EMPLOYED,
            "unemployed": EmploymentStatus.UNEMPLOYED,
            "retired": EmploymentStatus.RETIRED,
        }
        emp_status = emp_status_map.get(
            employment_status.lower(), EmploymentStatus.FULL_TIME
        )

        # Create applicant profile
        applicant = ApplicantInfo(
            age=age,
            monthly_income=monthly_income,
            credit_score=credit_score,
            employment_status=emp_status,
            employment_length_years=employment_length_years,
            monthly_debt_obligations=monthly_debt_obligations,
            requested_loan_amount=requested_loan_amount,
            loan_term_months=loan_term_months,
            has_existing_loans=has_existing_loans,
            previous_defaults=previous_defaults,
        )

        # Check eligibility
        result = eligibility_checker.check_eligibility(applicant)

        # Format response
        response = f"## Loan Eligibility Assessment\n\n"
        response += f"**Status**: {result.status.value.upper()}\n"
        response += f"**Eligible**: {'✅ Yes' if result.eligible else '❌ No'}\n"
        response += f"**Eligibility Score**: {result.score:.1f}/100\n\n"

        if result.reasons:
            response += "### Assessment Details:\n"
            for reason in result.reasons:
                response += f"- {reason}\n"
            response += "\n"

        if result.recommendations:
            response += "### Recommendations:\n"
            for rec in result.recommendations:
                response += f"- {rec}\n"

        logger.info(f"Eligibility check completed for age={age}, score={result.score}")
        return response

    except Exception as e:
        logger.error(f"Error in eligibility check: {str(e)}")
        return f"Error checking eligibility: {str(e)}"


@tool(name="calculate_loan_payment", show_result=True)
def calculate_loan_payment(
    loan_amount: float,
    annual_interest_rate: float,
    loan_term_months: int,
) -> str:
    """Calculate monthly loan payment and total costs.

    This tool calculates the monthly payment amount, total payment, and total
    interest for a given loan amount, interest rate, and term.

    Args:
        loan_amount: Principal loan amount
        annual_interest_rate: Annual interest rate (e.g., 0.0499 for 4.99%)
        loan_term_months: Loan term in months

    Returns:
        Payment calculation details including monthly payment, total payment, and total interest
    """
    try:
        loan_request = LoanRequest(
            loan_amount=loan_amount,
            annual_interest_rate=annual_interest_rate,
            loan_term_months=loan_term_months,
        )

        calc = loan_calculator.calculate_monthly_payment(loan_request)

        response = f"## Loan Payment Calculation\n\n"
        response += f"**Loan Amount**: ${calc.total_principal:,.2f}\n"
        response += f"**Interest Rate**: {calc.annual_interest_rate*100:.2f}% per year\n"
        response += f"**Loan Term**: {calc.loan_term_months} months ({calc.loan_term_months/12:.1f} years)\n\n"
        response += f"### Monthly Payment: ${calc.monthly_payment:,.2f}\n\n"
        response += f"**Total Payment**: ${calc.total_payment:,.2f}\n"
        response += f"**Total Interest**: ${calc.total_interest:,.2f}\n"
        response += f"**Interest as % of Principal**: {(calc.total_interest/calc.total_principal)*100:.1f}%\n"

        logger.info(f"Payment calculation: amount=${loan_amount}, payment=${calc.monthly_payment}")
        return response

    except Exception as e:
        logger.error(f"Error calculating payment: {str(e)}")
        return f"Error calculating payment: {str(e)}"


@tool(name="generate_payment_schedule", show_result=True)
def generate_payment_schedule(
    loan_amount: float,
    annual_interest_rate: float,
    loan_term_months: int,
    show_first_n_months: int = 12,
) -> str:
    """Generate amortization schedule showing payment breakdown over time.

    This tool creates a detailed payment schedule showing how each payment is
    split between principal and interest, and the remaining balance after each payment.

    Args:
        loan_amount: Principal loan amount
        annual_interest_rate: Annual interest rate
        loan_term_months: Loan term in months
        show_first_n_months: Number of initial months to display (default: 12)

    Returns:
        Formatted amortization schedule table
    """
    try:
        loan_request = LoanRequest(
            loan_amount=loan_amount,
            annual_interest_rate=annual_interest_rate,
            loan_term_months=loan_term_months,
        )

        schedule = loan_calculator.generate_amortization_schedule(loan_request)

        response = f"## Amortization Schedule\n\n"
        response += f"Showing first {min(show_first_n_months, loan_term_months)} months:\n\n"

        # Format first N months
        df_subset = schedule.schedule.head(show_first_n_months)
        response += "| Month | Payment | Principal | Interest | Remaining Balance |\n"
        response += "|-------|---------|-----------|----------|-------------------|\n"

        for _, row in df_subset.iterrows():
            response += (
                f"| {int(row['month'])} | "
                f"${row['payment']:,.2f} | "
                f"${row['principal']:,.2f} | "
                f"${row['interest']:,.2f} | "
                f"${row['balance']:,.2f} |\n"
            )

        if loan_term_months > show_first_n_months:
            response += f"\n... ({loan_term_months - show_first_n_months} more months)\n\n"

            # Show last month
            last_row = schedule.schedule.iloc[-1]
            response += f"**Final Month ({int(last_row['month'])})**: "
            response += f"${last_row['payment']:,.2f} payment, "
            response += f"Balance: ${last_row['balance']:,.2f}\n"

        logger.info(f"Generated payment schedule for ${loan_amount} over {loan_term_months} months")
        return response

    except Exception as e:
        logger.error(f"Error generating schedule: {str(e)}")
        return f"Error generating schedule: {str(e)}"


@tool(name="check_loan_affordability", show_result=True)
def check_loan_affordability(
    loan_amount: float,
    annual_interest_rate: float,
    loan_term_months: int,
    monthly_income: float,
    existing_monthly_debt: float = 0.0,
) -> str:
    """Check if a loan is affordable based on income and existing debt.

    This tool calculates the debt-to-income ratio and determines if the loan
    payment would be affordable given the applicant's financial situation.

    Args:
        loan_amount: Principal loan amount
        annual_interest_rate: Annual interest rate
        loan_term_months: Loan term in months
        monthly_income: Monthly income
        existing_monthly_debt: Existing monthly debt payments (default: 0)

    Returns:
        Affordability assessment with DTI ratio and recommendations
    """
    try:
        loan_request = LoanRequest(
            loan_amount=loan_amount,
            annual_interest_rate=annual_interest_rate,
            loan_term_months=loan_term_months,
            monthly_income=monthly_income,
        )

        result = loan_calculator.check_affordability(loan_request, existing_monthly_debt)

        response = f"## Affordability Assessment\n\n"

        if result["affordable"]:
            response += "✅ **This loan appears AFFORDABLE**\n\n"
        else:
            response += "⚠️ **WARNING: This loan may be UNAFFORDABLE**\n\n"

        response += f"**Monthly Income**: ${result['monthly_income']:,.2f}\n"
        response += f"**Existing Monthly Debt**: ${result['existing_debt']:,.2f}\n"
        response += f"**New Loan Payment**: ${result['monthly_payment']:,.2f}\n"
        response += f"**Total Monthly Debt**: ${result['total_monthly_debt']:,.2f}\n\n"
        response += (
            f"**Debt-to-Income Ratio**: {result['dti_ratio']*100:.1f}% "
            f"(Max Recommended: {result['max_recommended_dti']*100:.0f}%)\n\n"
        )
        response += f"### Analysis:\n{result['message']}\n"

        logger.info(f"Affordability check: DTI={result['dti_ratio']*100:.1f}%, affordable={result['affordable']}")
        return response

    except Exception as e:
        logger.error(f"Error checking affordability: {str(e)}")
        return f"Error checking affordability: {str(e)}"


@tool(name="compare_loan_terms", show_result=True)
def compare_loan_terms(
    loan_amount: float,
    annual_interest_rate: float,
    term_options: Optional[list[int]] = None,
) -> str:
    """Compare different loan term options to help choose the best term.

    This tool compares multiple loan term lengths, showing how the term affects
    monthly payment, total payment, and total interest paid.

    Args:
        loan_amount: Principal loan amount
        annual_interest_rate: Annual interest rate
        term_options: List of terms in months to compare (default: [24, 36, 48, 60])

    Returns:
        Comparison table of different loan terms with insights
    """
    try:
        if term_options is None:
            term_options = [24, 36, 48, 60]

        comparison = loan_calculator.compare_loan_options(
            loan_amount=loan_amount, annual_rate=annual_interest_rate, terms=term_options
        )

        response = f"## Loan Term Comparison\n\n"
        response += f"Comparing different terms for ${loan_amount:,.2f} at {annual_interest_rate*100:.2f}% APR:\n\n"

        response += (
            "| Term | Monthly Payment | Total Payment | Total Interest | "
            "Interest as % |\n"
        )
        response += (
            "|------|----------------|---------------|----------------|---------------|\n"
        )

        for _, row in comparison.iterrows():
            response += (
                f"| {int(row['term_months'])} months ({row['term_years']:.1f} yrs) | "
                f"${row['monthly_payment']:,.2f} | "
                f"${row['total_payment']:,.2f} | "
                f"${row['total_interest']:,.2f} | "
                f"{row['interest_percentage']:.1f}% |\n"
            )

        response += "\n### Key Insights:\n"
        response += "- **Shorter terms**: Higher monthly payment, less total interest\n"
        response += "- **Longer terms**: Lower monthly payment, more total interest\n"

        logger.info(f"Compared {len(term_options)} loan terms for ${loan_amount}")
        return response

    except Exception as e:
        logger.error(f"Error comparing terms: {str(e)}")
        return f"Error comparing terms: {str(e)}"


@tool(name="calculate_max_affordable_loan", show_result=True)
def calculate_max_affordable_loan(
    monthly_income: float,
    annual_interest_rate: float,
    loan_term_months: int,
    existing_monthly_debt: float = 0.0,
) -> str:
    """Calculate the maximum loan amount that would be affordable.

    This tool determines the maximum loan amount based on income, existing debt,
    and the maximum recommended debt-to-income ratio.

    Args:
        monthly_income: Monthly income
        annual_interest_rate: Annual interest rate
        loan_term_months: Desired loan term in months
        existing_monthly_debt: Existing monthly debt payments (default: 0)

    Returns:
        Maximum affordable loan amount with supporting calculations
    """
    try:
        result = loan_calculator.calculate_max_loan_amount(
            monthly_income=monthly_income,
            annual_interest_rate=annual_interest_rate,
            loan_term_months=loan_term_months,
            existing_monthly_debt=existing_monthly_debt,
        )

        response = f"## Maximum Affordable Loan\n\n"

        if result["max_loan_amount"] > 0:
            response += f"✅ **Maximum Loan Amount**: ${result['max_loan_amount']:,.2f}\n\n"
            response += f"**Monthly Income**: ${result['monthly_income']:,.2f}\n"
            response += f"**Existing Debt**: ${result['existing_debt']:,.2f}\n"
            response += f"**Maximum Monthly Payment**: ${result['max_monthly_payment']:,.2f}\n"
            response += f"**Loan Term**: {result['term_months']} months\n"
            response += f"**Interest Rate**: {result['annual_interest_rate']*100:.2f}%\n\n"
            response += f"### Analysis:\n{result['message']}\n"
        else:
            response += f"❌ **Cannot afford additional loan**\n\n"
            response += f"{result['message']}\n"

        logger.info(f"Max loan calculation: income=${monthly_income}, max=${result.get('max_loan_amount', 0)}")
        return response

    except Exception as e:
        logger.error(f"Error calculating max loan: {str(e)}")
        return f"Error calculating max loan: {str(e)}"


# =============================================================================
# MORTGAGE / HOME LOAN TOOLS
# =============================================================================

@tool(name="calculate_home_affordability", show_result=True)
def calculate_home_affordability_tool(
    monthly_income: float,
    residency: str = "expat",
    property_type: str = "first",
    existing_debt_payment: float = 0.0,
    annual_interest_rate: Optional[float] = None,
    loan_term_years: int = 30,
) -> str:
    """Calculate maximum home price you can afford based on income and residency.

    LTV (Loan-to-Value) limits vary by residency status:
    - UAE Citizen, first home ≤5M: 85% LTV (15% down)
    - UAE Citizen, first home >5M: 80% LTV (20% down)
    - Expat, first home: 80% LTV (20% down)
    - Expat, second home: 65% LTV (35% down)
    - Non-resident: 50% LTV (50% down)

    Args:
        monthly_income: Gross monthly income
        residency: 'citizen', 'expat', or 'non_resident' (default: 'expat')
        property_type: 'first' or 'second' home (default: 'first')
        existing_debt_payment: Existing monthly debt payments (default: 0)
        annual_interest_rate: Annual rate (optional, uses bank default)
        loan_term_years: Loan term in years (default: 30)

    Returns:
        Maximum home price, loan amount, down payment, and monthly payment
    """
    try:
        result = calculate_home_affordability(
            monthly_income=monthly_income,
            existing_debt_payment=existing_debt_payment,
            annual_interest_rate=annual_interest_rate,
            loan_term_months=loan_term_years * 12,
            residency=residency,
            property_type=property_type,
        )

        if not result.get("affordable", True):
            return f"## Home Affordability\n\n{result['message']}"

        response = f"## Home Affordability Analysis\n\n"
        response += f"**Applicant**: {residency.title()} buying {property_type} home\n"
        response += f"**Maximum Home Price**: ${result['max_home_price']:,.0f}\n"
        response += f"**Maximum Loan Amount**: ${result['max_loan_amount']:,.0f}\n"
        response += f"**Required Down Payment**: ${result['required_down_payment']:,.0f} ({result['down_payment_percentage']:.0%})\n"
        response += f"**Monthly Payment**: ${result['monthly_payment']:,.0f}\n\n"
        response += f"**Interest Rate**: {result['annual_interest_rate']:.2%}\n"
        response += f"**Loan Term**: {result['loan_term_years']} years\n"
        response += f"**Max DTI Used**: {result['dti_ratio']:.0%}\n"
        response += f"**Max LTV for {residency}/{property_type}**: {result['ltv_ratio']:.0%}\n\n"
        response += f"### Summary:\n{result['message']}\n"

        logger.info(f"Home affordability: {residency}/{property_type}, income=${monthly_income}, max_home=${result['max_home_price']}")
        return response

    except Exception as e:
        logger.error(f"Error calculating home affordability: {str(e)}")
        return f"Error calculating home affordability: {str(e)}"


@tool(name="calculate_mortgage_payment", show_result=True)
def calculate_mortgage_payment_tool(
    home_price: float,
    residency: str = "expat",
    property_type: str = "first",
    down_payment: Optional[float] = None,
    annual_interest_rate: Optional[float] = None,
    loan_term_years: int = 30,
) -> str:
    """Calculate mortgage payment for a specific home price.

    LTV limits vary by residency status - see calculate_home_affordability.

    Args:
        home_price: Total home price
        residency: 'citizen', 'expat', or 'non_resident' (default: 'expat')
        property_type: 'first' or 'second' home (default: 'first')
        down_payment: Down payment amount (optional, uses minimum for your status)
        annual_interest_rate: Annual rate (optional, uses bank default)
        loan_term_years: Loan term in years (default: 30)

    Returns:
        Monthly payment, LTV ratio, total interest, and loan breakdown
    """
    try:
        result = calculate_mortgage_payment(
            home_price=home_price,
            down_payment=down_payment,
            annual_interest_rate=annual_interest_rate,
            loan_term_months=loan_term_years * 12,
            residency=residency,
            property_type=property_type,
        )

        if not result.get("valid", True):
            return f"## Mortgage Calculation\n\n{result['message']}"

        response = f"## Mortgage Payment Calculation\n\n"
        response += f"**Applicant**: {residency.title()} buying {property_type} home\n"
        response += f"**Home Price**: ${result['home_price']:,.0f}\n"
        response += f"**Down Payment**: ${result['down_payment']:,.0f} ({result['down_payment_percentage']:.0%})\n"
        response += f"**Loan Amount**: ${result['loan_amount']:,.0f}\n"
        response += f"**LTV Ratio**: {result['ltv_ratio']:.0%} (max allowed: {result['max_ltv_allowed']:.0%})\n\n"
        response += f"### Monthly Payment: ${result['monthly_payment']:,.2f}\n\n"
        response += f"**Interest Rate**: {result['annual_interest_rate']:.2%}\n"
        response += f"**Loan Term**: {result['loan_term_years']} years\n"
        response += f"**Total Payment**: ${result['total_payment']:,.0f}\n"
        response += f"**Total Interest**: ${result['total_interest']:,.0f}\n"

        logger.info(f"Mortgage calc: {residency}/{property_type}, home=${home_price}, payment=${result['monthly_payment']}")
        return response

    except Exception as e:
        logger.error(f"Error calculating mortgage: {str(e)}")
        return f"Error calculating mortgage: {str(e)}"


# =============================================================================
# AUTO / CAR LOAN TOOLS
# =============================================================================

@tool(name="calculate_car_loan", show_result=True)
def calculate_car_loan_tool(
    car_price: float,
    down_payment: Optional[float] = None,
    annual_interest_rate: Optional[float] = None,
    loan_term_months: int = 60,
) -> str:
    """Calculate car loan payment.

    Args:
        car_price: Vehicle price
        down_payment: Down payment amount (optional, uses minimum if not provided)
        annual_interest_rate: Annual rate (optional, uses bank default)
        loan_term_months: Loan term in months (default: 60)

    Returns:
        Monthly payment, LTV ratio, total interest, and loan breakdown
    """
    try:
        result = calculate_car_loan(
            car_price=car_price,
            down_payment=down_payment,
            annual_interest_rate=annual_interest_rate,
            loan_term_months=loan_term_months,
        )

        if not result.get("valid", True):
            return f"## Car Loan Calculation\n\n{result['message']}"

        response = f"## Car Loan Calculation\n\n"
        response += f"**Vehicle Price**: ${result['car_price']:,.0f}\n"
        response += f"**Down Payment**: ${result['down_payment']:,.0f} ({result['down_payment_percentage']:.0%})\n"
        response += f"**Loan Amount**: ${result['loan_amount']:,.0f}\n"
        response += f"**LTV Ratio**: {result['ltv_ratio']:.0%}\n\n"
        response += f"### Monthly Payment: ${result['monthly_payment']:,.2f}\n\n"
        response += f"**Interest Rate**: {result['annual_interest_rate']:.2%}\n"
        response += f"**Loan Term**: {result['loan_term_months']} months\n"
        response += f"**Total Payment**: ${result['total_payment']:,.0f}\n"
        response += f"**Total Interest**: ${result['total_interest']:,.0f}\n"

        logger.info(f"Car loan calc: price=${car_price}, payment=${result['monthly_payment']}")
        return response

    except Exception as e:
        logger.error(f"Error calculating car loan: {str(e)}")
        return f"Error calculating car loan: {str(e)}"


@tool(name="compare_car_loan_terms", show_result=True)
def compare_car_loan_terms_tool(
    car_price: float,
    down_payment: Optional[float] = None,
    annual_interest_rate: Optional[float] = None,
) -> str:
    """Compare car loan options across different term lengths.

    Compares 36, 48, 60, and 72 month terms showing trade-offs between
    monthly payment and total interest.

    Args:
        car_price: Vehicle price
        down_payment: Down payment amount (optional)
        annual_interest_rate: Annual rate (optional, uses bank default)

    Returns:
        Comparison table of different loan terms
    """
    try:
        comparison = compare_car_loan_terms(
            car_price=car_price,
            down_payment=down_payment,
            annual_interest_rate=annual_interest_rate,
        )

        response = f"## Car Loan Term Comparison\n\n"
        response += f"Comparing different terms for ${car_price:,.0f} vehicle:\n\n"

        response += (
            "| Term | Monthly Payment | Total Payment | Total Interest | Interest % |\n"
        )
        response += (
            "|------|----------------|---------------|----------------|------------|\n"
        )

        for _, row in comparison.iterrows():
            response += (
                f"| {int(row['term_months'])} mo ({row['term_years']:.1f} yr) | "
                f"${row['monthly_payment']:,.2f} | "
                f"${row['total_payment']:,.0f} | "
                f"${row['total_interest']:,.0f} | "
                f"{row['interest_percentage']:.1f}% |\n"
            )

        response += "\n### Key Insights:\n"
        response += "- **Shorter terms (36-48 mo)**: Higher payment, less interest\n"
        response += "- **Longer terms (60-72 mo)**: Lower payment, more interest\n"
        response += "- Consider your budget and total cost when choosing\n"

        logger.info(f"Compared car loan terms for ${car_price}")
        return response

    except Exception as e:
        logger.error(f"Error comparing car loan terms: {str(e)}")
        return f"Error comparing car loan terms: {str(e)}"


# =============================================================================
# EARLY PAYOFF TOOL
# =============================================================================

@tool(name="calculate_early_payoff", show_result=True)
def calculate_early_payoff_tool(
    loan_amount: float,
    annual_interest_rate: float,
    loan_term_months: int,
    extra_monthly_payment: float,
) -> str:
    """Calculate savings from making extra monthly payments.

    Shows how much interest you can save and how much earlier you'll
    pay off the loan by making additional monthly payments.

    Args:
        loan_amount: Original loan amount
        annual_interest_rate: Annual interest rate
        loan_term_months: Original loan term in months
        extra_monthly_payment: Extra amount to pay each month

    Returns:
        Payoff timeline, interest saved, and comparison
    """
    try:
        result = calculate_early_payoff(
            loan_amount=loan_amount,
            annual_interest_rate=annual_interest_rate,
            loan_term_months=loan_term_months,
            extra_monthly_payment=extra_monthly_payment,
        )

        response = f"## Early Payoff Analysis\n\n"
        response += f"**Original Loan**: ${loan_amount:,.0f} over {loan_term_months} months\n"
        response += f"**Extra Payment**: ${extra_monthly_payment:,.0f}/month\n\n"

        response += f"### Results:\n"
        response += f"**New Payoff Time**: {result['new_term_months']} months "
        response += f"(saved {result['months_saved']} months / {result['years_saved']} years)\n"
        response += f"**Original Monthly Payment**: ${result['original_monthly_payment']:,.2f}\n"
        response += f"**New Monthly Payment**: ${result['new_monthly_payment']:,.2f}\n\n"

        response += f"### Interest Savings:\n"
        response += f"**Original Total Interest**: ${result['original_total_interest']:,.0f}\n"
        response += f"**New Total Interest**: ${result['new_total_interest']:,.0f}\n"
        response += f"**Interest Saved**: ${result['interest_saved']:,.0f}\n\n"

        response += f"### Summary:\n{result['message']}\n"

        logger.info(f"Early payoff: extra=${extra_monthly_payment}, saved=${result['interest_saved']}")
        return response

    except Exception as e:
        logger.error(f"Error calculating early payoff: {str(e)}")
        return f"Error calculating early payoff: {str(e)}"


# =============================================================================
# RAW FUNCTION EXPORTS (for testing)
# =============================================================================

# For direct function calls (e.g., in tests), we need to access the underlying functions
# The @tool decorator wraps functions in a Function object, so we provide access to both
# the wrapped version (for Agent use) and the raw function (for direct calls)

# Extract raw functions from the Function objects for testing
check_loan_eligibility_raw = check_loan_eligibility.entrypoint
calculate_loan_payment_raw = calculate_loan_payment.entrypoint
generate_payment_schedule_raw = generate_payment_schedule.entrypoint
check_loan_affordability_raw = check_loan_affordability.entrypoint
compare_loan_terms_raw = compare_loan_terms.entrypoint
calculate_max_affordable_loan_raw = calculate_max_affordable_loan.entrypoint
calculate_home_affordability_raw = calculate_home_affordability_tool.entrypoint
calculate_mortgage_payment_raw = calculate_mortgage_payment_tool.entrypoint
calculate_car_loan_raw = calculate_car_loan_tool.entrypoint
compare_car_loan_terms_raw = compare_car_loan_terms_tool.entrypoint
calculate_early_payoff_raw = calculate_early_payoff_tool.entrypoint

# Export all tool functions for easy import
__all__ = [
    # Personal Loan Tools
    "check_loan_eligibility",
    "calculate_loan_payment",
    "generate_payment_schedule",
    "check_loan_affordability",
    "compare_loan_terms",
    "calculate_max_affordable_loan",
    # Mortgage Tools
    "calculate_home_affordability_tool",
    "calculate_mortgage_payment_tool",
    # Auto Loan Tools
    "calculate_car_loan_tool",
    "compare_car_loan_terms_tool",
    # Early Payoff Tool
    "calculate_early_payoff_tool",
    # Raw versions for direct calls
    "check_loan_eligibility_raw",
    "calculate_loan_payment_raw",
    "generate_payment_schedule_raw",
    "check_loan_affordability_raw",
    "compare_loan_terms_raw",
    "calculate_max_affordable_loan_raw",
    "calculate_home_affordability_raw",
    "calculate_mortgage_payment_raw",
    "calculate_car_loan_raw",
    "compare_car_loan_terms_raw",
    "calculate_early_payoff_raw",
]