"""Loan Rules - Simple rule-based system for loan regulations.

This module provides a simple, maintainable rule system for loan regulations
that vary by applicant status (citizen/expat), property type (first/second), etc.

Design Principles:
- Simple: One Pydantic model + one list + one function
- Readable: Rules are data, easy to understand at a glance
- Maintainable: Add/modify rules by editing the list
- Extensible: Add new conditions by adding fields

Usage:
    from src.tools.loan_rules import get_mortgage_rule

    rule = get_mortgage_rule(
        residency="expat",
        property_type="second",
        price=3_000_000,
    )
    print(f"Max LTV: {rule.max_ltv}")  # 0.65
    print(f"Min Down Payment: {rule.min_down_payment}")  # 0.35
"""

from pydantic import BaseModel, Field


# =============================================================================
# MORTGAGE RULE MODEL
# =============================================================================

class MortgageRule(BaseModel):
    """A single mortgage rule: conditions + results.

    Conditions (optional): If None, matches any value.
    Results (required): LTV and down payment values.
    """

    # === Results (required) ===
    max_ltv: float = Field(ge=0, le=1, description="Maximum Loan-to-Value ratio")
    min_down_payment: float = Field(ge=0, le=1, description="Minimum down payment")

    # === Conditions (optional, None = match any) ===
    residency: str | None = Field(
        default=None,
        description="Residency status: 'citizen', 'expat', 'non_resident'"
    )
    property_type: str | None = Field(
        default=None,
        description="Property type: 'first', 'second', 'investment'"
    )
    price_max: float | None = Field(
        default=None, ge=0,
        description="Maximum property price for this rule"
    )
    price_min: float | None = Field(
        default=None, ge=0,
        description="Minimum property price for this rule"
    )

    def matches(
        self,
        residency: str,
        property_type: str,
        price: float,
    ) -> bool:
        """Check if this rule matches the given conditions.

        Args:
            residency: Applicant's residency status
            property_type: Type of property (first/second home)
            price: Property price

        Returns:
            True if all conditions match (or are None)
        """
        # Check residency
        if self.residency is not None and self.residency != residency:
            return False

        # Check property type
        if self.property_type is not None and self.property_type != property_type:
            return False

        # Check price range
        if self.price_max is not None and price > self.price_max:
            return False
        if self.price_min is not None and price < self.price_min:
            return False

        return True


# =============================================================================
# UAE MORTGAGE RULES
# =============================================================================
# Rules are matched from top to bottom. First match wins.
# Put more specific rules (with more conditions) at the top.
#
# UAE Central Bank Regulations (2024):
# - Citizens: 85% LTV for first home (≤5M), 80% for >5M or second home
# - Expats: 80% LTV for first home, 65% for second home
# - Non-residents: 50% LTV
# =============================================================================

MORTGAGE_RULES: list[MortgageRule] = [
    # --- UAE Citizens ---
    MortgageRule(
        max_ltv=0.85,
        min_down_payment=0.15,
        residency="citizen",
        property_type="first",
        price_max=5_000_000,
    ),
    MortgageRule(
        max_ltv=0.80,
        min_down_payment=0.20,
        residency="citizen",
        property_type="first",
        price_min=5_000_000,
    ),
    MortgageRule(
        max_ltv=0.75,
        min_down_payment=0.25,
        residency="citizen",
        property_type="second",
    ),

    # --- Expats (Foreign Residents) ---
    MortgageRule(
        max_ltv=0.80,
        min_down_payment=0.20,
        residency="expat",
        property_type="first",
    ),
    MortgageRule(
        max_ltv=0.65,
        min_down_payment=0.35,
        residency="expat",
        property_type="second",
    ),

    # --- Non-Residents ---
    MortgageRule(
        max_ltv=0.50,
        min_down_payment=0.50,
        residency="non_resident",
    ),

    # --- Default Rule (fallback) ---
    MortgageRule(
        max_ltv=0.75,
        min_down_payment=0.25,
    ),
]


# =============================================================================
# RULE LOOKUP FUNCTION
# =============================================================================

def get_mortgage_rule(
    residency: str = "expat",
    property_type: str = "first",
    price: float = 0,
) -> MortgageRule:
    """Get the applicable mortgage rule for given conditions.

    Rules are matched from top to bottom. First match wins.

    Args:
        residency: 'citizen', 'expat', or 'non_resident' (default: 'expat')
        property_type: 'first', 'second', or 'investment' (default: 'first')
        price: Property price in AED (default: 0)

    Returns:
        The first matching MortgageRule

    Example:
        >>> rule = get_mortgage_rule("expat", "second", 3_000_000)
        >>> rule.max_ltv
        0.65
        >>> rule.min_down_payment
        0.35
    """
    for rule in MORTGAGE_RULES:
        if rule.matches(residency, property_type, price):
            return rule

    # Should never reach here (default rule matches everything)
    return MORTGAGE_RULES[-1]


# =============================================================================
# AUTO LOAN RULES (Simpler - less variation by residency)
# =============================================================================

class AutoLoanRule(BaseModel):
    """A single auto loan rule."""

    max_ltv: float = Field(ge=0, le=1)
    min_down_payment: float = Field(ge=0, le=1)
    residency: str | None = None
    vehicle_type: str | None = None  # "new", "used"

    def matches(self, residency: str, vehicle_type: str = "new") -> bool:
        if self.residency is not None and self.residency != residency:
            return False
        if self.vehicle_type is not None and self.vehicle_type != vehicle_type:
            return False
        return True


AUTO_LOAN_RULES: list[AutoLoanRule] = [
    # New vehicles - higher LTV
    AutoLoanRule(max_ltv=0.90, min_down_payment=0.10, vehicle_type="new"),
    # Used vehicles - lower LTV
    AutoLoanRule(max_ltv=0.80, min_down_payment=0.20, vehicle_type="used"),
    # Default
    AutoLoanRule(max_ltv=0.85, min_down_payment=0.15),
]


def get_auto_loan_rule(
    residency: str = "expat",
    vehicle_type: str = "new",
) -> AutoLoanRule:
    """Get the applicable auto loan rule."""
    for rule in AUTO_LOAN_RULES:
        if rule.matches(residency, vehicle_type):
            return rule
    return AUTO_LOAN_RULES[-1]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_available_residency_types() -> list[str]:
    """Get list of supported residency types."""
    return ["citizen", "expat", "non_resident"]


def get_available_property_types() -> list[str]:
    """Get list of supported property types."""
    return ["first", "second", "investment"]


def describe_mortgage_rules() -> str:
    """Get a human-readable description of mortgage rules."""
    lines = ["UAE Mortgage LTV Rules:", ""]
    for rule in MORTGAGE_RULES:
        conditions = []
        if rule.residency:
            conditions.append(f"Residency: {rule.residency}")
        if rule.property_type:
            conditions.append(f"Property: {rule.property_type}")
        if rule.price_max:
            conditions.append(f"Price ≤ {rule.price_max:,.0f}")
        if rule.price_min:
            conditions.append(f"Price > {rule.price_min:,.0f}")

        condition_str = ", ".join(conditions) if conditions else "Default"
        lines.append(
            f"  {condition_str}: LTV {rule.max_ltv:.0%}, "
            f"Down Payment {rule.min_down_payment:.0%}"
        )
    return "\n".join(lines)
