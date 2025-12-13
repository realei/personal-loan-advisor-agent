"""Output Formatter - Configurable output formatting system.

Supports both streaming markdown and structured JSON output.
Follows SOLID principles:
- Single Responsibility: Each formatter handles one output type
- Open/Closed: Add new formatters without modifying existing code
- Liskov Substitution: All formatters are interchangeable
- Interface Segregation: Simple, focused protocol
- Dependency Inversion: Depend on OutputFormatter protocol

Usage:
    formatter = get_formatter("markdown")  # or "structured"
    output = formatter.format_payment(payment_data)
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Protocol, runtime_checkable
import os

from src.agent.response_models import (
    LoanAdvisorResponse,
    EligibilityResult,
    PaymentResult,
    AffordabilityResult,
    TermComparisonResult,
    TermComparisonItem,
    MaxLoanResult,
    HomeAffordabilityResult,
    MortgagePaymentResult,
    CarLoanResult,
    EarlyPayoffResult,
)


# =============================================================================
# OUTPUT MODE ENUM
# =============================================================================

class OutputMode(str, Enum):
    """Output format modes."""
    MARKDOWN = "markdown"      # Human-readable, streaming-friendly
    STRUCTURED = "structured"  # Machine-readable, Pydantic-validated

    @classmethod
    def from_env(cls) -> "OutputMode":
        """Get output mode from environment variable."""
        mode = os.getenv("OUTPUT_MODE", "markdown").lower()
        if mode in ("structured", "json", "pydantic"):
            return cls.STRUCTURED
        return cls.MARKDOWN


# =============================================================================
# OUTPUT FORMATTER PROTOCOL (Interface)
# =============================================================================

@runtime_checkable
class OutputFormatter(Protocol):
    """Protocol defining the output formatter interface.

    All formatters must implement these methods.
    This allows for easy extension and substitution.
    """

    def format_eligibility(self, data: dict) -> Any:
        """Format eligibility check result."""
        ...

    def format_payment(self, data: dict) -> Any:
        """Format payment calculation result."""
        ...

    def format_affordability(self, data: dict) -> Any:
        """Format affordability check result."""
        ...

    def format_schedule(self, data: dict, schedule_df: Any) -> Any:
        """Format amortization schedule."""
        ...

    def format_term_comparison(self, data: dict, comparison_df: Any) -> Any:
        """Format term comparison result."""
        ...

    def format_max_loan(self, data: dict) -> Any:
        """Format max loan calculation result."""
        ...

    def format_home_affordability(self, data: dict) -> Any:
        """Format home affordability result."""
        ...

    def format_mortgage(self, data: dict) -> Any:
        """Format mortgage payment result."""
        ...

    def format_car_loan(self, data: dict) -> Any:
        """Format car loan result."""
        ...

    def format_early_payoff(self, data: dict) -> Any:
        """Format early payoff result."""
        ...


# =============================================================================
# MARKDOWN FORMATTER (Streaming-friendly)
# =============================================================================

class MarkdownFormatter:
    """Formats output as human-readable markdown.

    Best for:
    - Chat interfaces
    - Streaming output
    - Human consumption

    Returns: str (markdown formatted text)
    """

    def format_eligibility(self, data: dict) -> str:
        """Format eligibility check as markdown."""
        response = "## Loan Eligibility Assessment\n\n"
        response += f"**Status**: {data.get('status', 'unknown').upper()}\n"
        response += f"**Eligible**: {'✅ Yes' if data.get('eligible') else '❌ No'}\n"
        response += f"**Eligibility Score**: {data.get('score', 0):.1f}/100\n\n"

        if data.get("reasons"):
            response += "### Assessment Details:\n"
            for reason in data["reasons"]:
                response += f"- {reason}\n"
            response += "\n"

        if data.get("recommendations"):
            response += "### Recommendations:\n"
            for rec in data["recommendations"]:
                response += f"- {rec}\n"

        return response

    def format_payment(self, data: dict) -> str:
        """Format payment calculation as markdown."""
        response = "## Loan Payment Calculation\n\n"
        response += f"**Loan Amount**: ${data.get('loan_amount', 0):,.2f}\n"
        response += f"**Interest Rate**: {data.get('annual_interest_rate', 0)*100:.2f}% per year\n"
        response += f"**Loan Term**: {data.get('loan_term_months', 0)} months\n\n"
        response += f"### Monthly Payment: ${data.get('monthly_payment', 0):,.2f}\n\n"
        response += f"**Total Payment**: ${data.get('total_payment', 0):,.2f}\n"
        response += f"**Total Interest**: ${data.get('total_interest', 0):,.2f}\n"

        if data.get('loan_amount', 0) > 0:
            interest_pct = (data.get('total_interest', 0) / data.get('loan_amount', 1)) * 100
            response += f"**Interest as % of Principal**: {interest_pct:.1f}%\n"

        return response

    def format_affordability(self, data: dict) -> str:
        """Format affordability check as markdown."""
        response = "## Affordability Assessment\n\n"

        if data.get("affordable"):
            response += "✅ **This loan appears AFFORDABLE**\n\n"
        else:
            response += "⚠️ **WARNING: This loan may be UNAFFORDABLE**\n\n"

        response += f"**Monthly Income**: ${data.get('monthly_income', 0):,.2f}\n"
        response += f"**Existing Monthly Debt**: ${data.get('existing_debt', 0):,.2f}\n"
        response += f"**New Loan Payment**: ${data.get('monthly_payment', 0):,.2f}\n"
        response += f"**Total Monthly Debt**: ${data.get('total_monthly_debt', 0):,.2f}\n\n"
        response += f"**Debt-to-Income Ratio**: {data.get('dti_ratio', 0)*100:.1f}% "
        response += f"(Max Recommended: {data.get('max_recommended_dti', 0.5)*100:.0f}%)\n\n"
        response += f"### Analysis:\n{data.get('message', '')}\n"

        return response

    def format_schedule(self, data: dict, schedule_df: Any) -> str:
        """Format amortization schedule as markdown table."""
        show_months = data.get("show_first_n_months", 12)
        total_months = data.get("loan_term_months", 0)

        response = "## Amortization Schedule\n\n"
        response += f"Showing first {min(show_months, total_months)} months:\n\n"

        response += "| Month | Payment | Principal | Interest | Remaining Balance |\n"
        response += "|-------|---------|-----------|----------|-------------------|\n"

        df_subset = schedule_df.head(show_months)
        for _, row in df_subset.iterrows():
            response += (
                f"| {int(row['month'])} | "
                f"${row['payment']:,.2f} | "
                f"${row['principal']:,.2f} | "
                f"${row['interest']:,.2f} | "
                f"${row['balance']:,.2f} |\n"
            )

        if total_months > show_months:
            response += f"\n... ({total_months - show_months} more months)\n\n"
            last_row = schedule_df.iloc[-1]
            response += f"**Final Month ({int(last_row['month'])})**: "
            response += f"${last_row['payment']:,.2f} payment, "
            response += f"Balance: ${last_row['balance']:,.2f}\n"

        return response

    def format_term_comparison(self, data: dict, comparison_df: Any) -> str:
        """Format term comparison as markdown table."""
        response = "## Loan Term Comparison\n\n"
        response += f"Comparing terms for ${data.get('loan_amount', 0):,.2f} "
        response += f"at {data.get('annual_interest_rate', 0)*100:.2f}% APR:\n\n"

        response += "| Term | Monthly Payment | Total Payment | Total Interest | Interest % |\n"
        response += "|------|----------------|---------------|----------------|------------|\n"

        for _, row in comparison_df.iterrows():
            response += (
                f"| {int(row['term_months'])} mo ({row['term_years']:.1f} yr) | "
                f"${row['monthly_payment']:,.2f} | "
                f"${row['total_payment']:,.2f} | "
                f"${row['total_interest']:,.2f} | "
                f"{row['interest_percentage']:.1f}% |\n"
            )

        response += "\n### Key Insights:\n"
        response += "- **Shorter terms**: Higher monthly payment, less total interest\n"
        response += "- **Longer terms**: Lower monthly payment, more total interest\n"

        return response

    def format_max_loan(self, data: dict) -> str:
        """Format max loan calculation as markdown."""
        response = "## Maximum Affordable Loan\n\n"

        if data.get("max_loan_amount", 0) > 0:
            response += f"✅ **Maximum Loan Amount**: ${data['max_loan_amount']:,.2f}\n\n"
            response += f"**Monthly Income**: ${data.get('monthly_income', 0):,.2f}\n"
            response += f"**Existing Debt**: ${data.get('existing_debt', 0):,.2f}\n"
            response += f"**Maximum Monthly Payment**: ${data.get('max_monthly_payment', 0):,.2f}\n"
            response += f"**Loan Term**: {data.get('term_months', 0)} months\n"
            response += f"**Interest Rate**: {data.get('annual_interest_rate', 0)*100:.2f}%\n\n"
        else:
            response += "❌ **Cannot afford additional loan**\n\n"

        response += f"### Analysis:\n{data.get('message', '')}\n"
        return response

    def format_home_affordability(self, data: dict) -> str:
        """Format home affordability as markdown."""
        if not data.get("affordable", True):
            return f"## Home Affordability\n\n{data.get('message', '')}"

        response = "## Home Affordability Analysis\n\n"
        response += f"**Applicant**: {data.get('residency', 'expat').title()} "
        response += f"buying {data.get('property_type', 'first')} home\n"
        response += f"**Maximum Home Price**: ${data.get('max_home_price', 0):,.0f}\n"
        response += f"**Maximum Loan Amount**: ${data.get('max_loan_amount', 0):,.0f}\n"
        response += f"**Required Down Payment**: ${data.get('required_down_payment', 0):,.0f} "
        response += f"({data.get('down_payment_percentage', 0):.0%})\n"
        response += f"**Monthly Payment**: ${data.get('monthly_payment', 0):,.0f}\n\n"
        response += f"**Max LTV**: {data.get('ltv_ratio', 0):.0%}\n"
        response += f"**Max DTI Used**: {data.get('dti_ratio', 0):.0%}\n\n"
        response += f"### Summary:\n{data.get('message', '')}\n"

        return response

    def format_mortgage(self, data: dict) -> str:
        """Format mortgage payment as markdown."""
        if not data.get("valid", True):
            return f"## Mortgage Calculation\n\n{data.get('message', '')}"

        response = "## Mortgage Payment Calculation\n\n"
        response += f"**Home Price**: ${data.get('home_price', 0):,.0f}\n"
        response += f"**Down Payment**: ${data.get('down_payment', 0):,.0f} "
        response += f"({data.get('down_payment_percentage', 0):.0%})\n"
        response += f"**Loan Amount**: ${data.get('loan_amount', 0):,.0f}\n"
        response += f"**LTV Ratio**: {data.get('ltv_ratio', 0):.0%}\n\n"
        response += f"### Monthly Payment: ${data.get('monthly_payment', 0):,.2f}\n\n"
        response += f"**Interest Rate**: {data.get('annual_interest_rate', 0):.2%}\n"
        response += f"**Loan Term**: {data.get('loan_term_years', 30)} years\n"
        response += f"**Total Payment**: ${data.get('total_payment', 0):,.0f}\n"
        response += f"**Total Interest**: ${data.get('total_interest', 0):,.0f}\n"

        return response

    def format_car_loan(self, data: dict) -> str:
        """Format car loan as markdown."""
        if not data.get("valid", True):
            return f"## Car Loan Calculation\n\n{data.get('message', '')}"

        response = "## Car Loan Calculation\n\n"
        response += f"**Vehicle Price**: ${data.get('car_price', 0):,.0f}\n"
        response += f"**Down Payment**: ${data.get('down_payment', 0):,.0f} "
        response += f"({data.get('down_payment_percentage', 0):.0%})\n"
        response += f"**Loan Amount**: ${data.get('loan_amount', 0):,.0f}\n"
        response += f"**LTV Ratio**: {data.get('ltv_ratio', 0):.0%}\n\n"
        response += f"### Monthly Payment: ${data.get('monthly_payment', 0):,.2f}\n\n"
        response += f"**Interest Rate**: {data.get('annual_interest_rate', 0):.2%}\n"
        response += f"**Loan Term**: {data.get('loan_term_months', 60)} months\n"
        response += f"**Total Payment**: ${data.get('total_payment', 0):,.0f}\n"
        response += f"**Total Interest**: ${data.get('total_interest', 0):,.0f}\n"

        return response

    def format_early_payoff(self, data: dict) -> str:
        """Format early payoff as markdown."""
        response = "## Early Payoff Analysis\n\n"
        response += f"**Extra Payment**: ${data.get('extra_monthly_payment', 0):,.0f}/month\n\n"

        response += "### Results:\n"
        response += f"**New Payoff Time**: {data.get('new_term_months', 0)} months "
        response += f"(saved {data.get('months_saved', 0)} months / "
        response += f"{data.get('years_saved', 0)} years)\n"
        response += f"**Original Monthly Payment**: ${data.get('original_monthly_payment', 0):,.2f}\n"
        response += f"**New Monthly Payment**: ${data.get('new_monthly_payment', 0):,.2f}\n\n"

        response += "### Interest Savings:\n"
        response += f"**Original Total Interest**: ${data.get('original_total_interest', 0):,.0f}\n"
        response += f"**New Total Interest**: ${data.get('new_total_interest', 0):,.0f}\n"
        response += f"**Interest Saved**: ${data.get('interest_saved', 0):,.0f}\n\n"

        response += f"### Summary:\n{data.get('message', '')}\n"

        return response


# =============================================================================
# STRUCTURED FORMATTER (API-friendly)
# =============================================================================

class StructuredFormatter:
    """Formats output as structured Pydantic models.

    Best for:
    - API responses
    - Programmatic consumption
    - Data extraction

    Returns: Pydantic model instances or dicts
    """

    def format_eligibility(self, data: dict) -> EligibilityResult:
        """Format eligibility check as Pydantic model."""
        return EligibilityResult(
            eligible=data.get("eligible", False),
            status=data.get("status", "denied"),
            score=data.get("score", 0),
            reasons=data.get("reasons", []),
            recommendations=data.get("recommendations", []),
        )

    def format_payment(self, data: dict) -> PaymentResult:
        """Format payment calculation as Pydantic model."""
        loan_amount = data.get("loan_amount", 0)
        total_interest = data.get("total_interest", 0)
        interest_pct = (total_interest / loan_amount * 100) if loan_amount > 0 else 0

        return PaymentResult(
            loan_amount=loan_amount,
            annual_interest_rate=data.get("annual_interest_rate", 0),
            loan_term_months=data.get("loan_term_months", 0),
            monthly_payment=data.get("monthly_payment", 0),
            total_payment=data.get("total_payment", 0),
            total_interest=total_interest,
            interest_percentage=interest_pct,
        )

    def format_affordability(self, data: dict) -> AffordabilityResult:
        """Format affordability check as Pydantic model."""
        return AffordabilityResult(
            affordable=data.get("affordable", False),
            monthly_income=data.get("monthly_income", 0),
            existing_debt=data.get("existing_debt", 0),
            monthly_payment=data.get("monthly_payment", 0),
            total_monthly_debt=data.get("total_monthly_debt", 0),
            dti_ratio=data.get("dti_ratio", 0),
            max_recommended_dti=data.get("max_recommended_dti", 0.5),
            message=data.get("message", ""),
        )

    def format_schedule(self, data: dict, schedule_df: Any) -> dict:
        """Format amortization schedule as dict with DataFrame."""
        return {
            "loan_amount": data.get("loan_amount", 0),
            "annual_interest_rate": data.get("annual_interest_rate", 0),
            "loan_term_months": data.get("loan_term_months", 0),
            "monthly_payment": data.get("monthly_payment", 0),
            "schedule": schedule_df.to_dict(orient="records"),
        }

    def format_term_comparison(self, data: dict, comparison_df: Any) -> TermComparisonResult:
        """Format term comparison as Pydantic model."""
        options = [
            TermComparisonItem(
                term_months=int(row["term_months"]),
                term_years=row["term_years"],
                monthly_payment=row["monthly_payment"],
                total_payment=row["total_payment"],
                total_interest=row["total_interest"],
                interest_percentage=row["interest_percentage"],
            )
            for _, row in comparison_df.iterrows()
        ]

        return TermComparisonResult(
            loan_amount=data.get("loan_amount", 0),
            annual_interest_rate=data.get("annual_interest_rate", 0),
            options=options,
            recommendation="Shorter terms save interest, longer terms lower monthly payments",
        )

    def format_max_loan(self, data: dict) -> MaxLoanResult:
        """Format max loan calculation as Pydantic model."""
        return MaxLoanResult(
            max_loan_amount=data.get("max_loan_amount", 0),
            monthly_income=data.get("monthly_income", 0),
            existing_debt=data.get("existing_debt", 0),
            max_monthly_payment=data.get("max_monthly_payment", 0),
            term_months=data.get("term_months", 0),
            annual_interest_rate=data.get("annual_interest_rate", 0),
            message=data.get("message", ""),
        )

    def format_home_affordability(self, data: dict) -> HomeAffordabilityResult:
        """Format home affordability as Pydantic model."""
        return HomeAffordabilityResult(
            affordable=data.get("affordable", False),
            max_home_price=data.get("max_home_price", 0),
            max_loan_amount=data.get("max_loan_amount", 0),
            required_down_payment=data.get("required_down_payment", 0),
            down_payment_percentage=data.get("down_payment_percentage", 0),
            monthly_payment=data.get("monthly_payment", 0),
            ltv_ratio=data.get("ltv_ratio", 0),
            dti_ratio=data.get("dti_ratio", 0),
            residency=data.get("residency", "expat"),
            property_type=data.get("property_type", "first"),
            message=data.get("message", ""),
        )

    def format_mortgage(self, data: dict) -> MortgagePaymentResult:
        """Format mortgage payment as Pydantic model."""
        return MortgagePaymentResult(
            valid=data.get("valid", False),
            home_price=data.get("home_price", 0),
            down_payment=data.get("down_payment", 0),
            down_payment_percentage=data.get("down_payment_percentage", 0),
            loan_amount=data.get("loan_amount", 0),
            ltv_ratio=data.get("ltv_ratio", 0),
            max_ltv_allowed=data.get("max_ltv_allowed", 0.8),
            monthly_payment=data.get("monthly_payment", 0),
            total_payment=data.get("total_payment", 0),
            total_interest=data.get("total_interest", 0),
            annual_interest_rate=data.get("annual_interest_rate", 0),
            loan_term_years=data.get("loan_term_years", 30),
            message=data.get("message"),
        )

    def format_car_loan(self, data: dict) -> CarLoanResult:
        """Format car loan as Pydantic model."""
        return CarLoanResult(
            valid=data.get("valid", False),
            car_price=data.get("car_price", 0),
            down_payment=data.get("down_payment", 0),
            down_payment_percentage=data.get("down_payment_percentage", 0),
            loan_amount=data.get("loan_amount", 0),
            ltv_ratio=data.get("ltv_ratio", 0),
            monthly_payment=data.get("monthly_payment", 0),
            total_payment=data.get("total_payment", 0),
            total_interest=data.get("total_interest", 0),
            annual_interest_rate=data.get("annual_interest_rate", 0),
            loan_term_months=data.get("loan_term_months", 60),
            message=data.get("message"),
        )

    def format_early_payoff(self, data: dict) -> EarlyPayoffResult:
        """Format early payoff as Pydantic model."""
        return EarlyPayoffResult(
            original_term_months=data.get("original_term_months", 0),
            new_term_months=data.get("new_term_months", 0),
            months_saved=data.get("months_saved", 0),
            years_saved=data.get("years_saved", 0),
            original_monthly_payment=data.get("original_monthly_payment", 0),
            new_monthly_payment=data.get("new_monthly_payment", 0),
            extra_monthly_payment=data.get("extra_monthly_payment", 0),
            original_total_interest=data.get("original_total_interest", 0),
            new_total_interest=data.get("new_total_interest", 0),
            interest_saved=data.get("interest_saved", 0),
            message=data.get("message", ""),
        )


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_formatter(mode: OutputMode | str | None = None) -> OutputFormatter:
    """Factory function to get the appropriate formatter.

    Args:
        mode: Output mode - "markdown", "structured", or None (auto-detect from env)

    Returns:
        OutputFormatter instance

    Example:
        formatter = get_formatter("markdown")
        output = formatter.format_payment(payment_data)

        # Auto-detect from OUTPUT_MODE env var
        formatter = get_formatter()
    """
    if mode is None:
        mode = OutputMode.from_env()
    elif isinstance(mode, str):
        mode = OutputMode(mode.lower())

    formatters = {
        OutputMode.MARKDOWN: MarkdownFormatter,
        OutputMode.STRUCTURED: StructuredFormatter,
    }

    formatter_class = formatters.get(mode, MarkdownFormatter)
    return formatter_class()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "OutputMode",
    "OutputFormatter",
    "MarkdownFormatter",
    "StructuredFormatter",
    "get_formatter",
]
