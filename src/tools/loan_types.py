"""Loan Type Definitions.

Simple enum-based loan type system. All regulations (DTI, LTV, rates)
are configured via environment variables in config.py.

Usage:
    from src.tools.loan_types import LoanType

    loan_type = LoanType.MORTGAGE
    config = get_loan_type_config(loan_type)
"""

from enum import Enum


class LoanType(str, Enum):
    """Supported loan types."""

    PERSONAL = "personal"
    MORTGAGE = "mortgage"
    AUTO = "auto"

    @classmethod
    def from_string(cls, value: str) -> "LoanType":
        """Convert string to LoanType (case-insensitive)."""
        return cls(value.lower())

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        names = {
            LoanType.PERSONAL: "Personal Loan",
            LoanType.MORTGAGE: "Mortgage / Home Loan",
            LoanType.AUTO: "Auto / Car Loan",
        }
        return names[self]

    @property
    def description(self) -> str:
        """Brief description."""
        descriptions = {
            LoanType.PERSONAL: "Unsecured loan for personal expenses",
            LoanType.MORTGAGE: "Secured loan for property purchase",
            LoanType.AUTO: "Secured loan for vehicle purchase",
        }
        return descriptions[self]

    @property
    def requires_collateral(self) -> bool:
        """Whether this loan type requires collateral."""
        return self in (LoanType.MORTGAGE, LoanType.AUTO)

    @property
    def collateral_type(self) -> str | None:
        """Type of collateral required."""
        types = {
            LoanType.PERSONAL: None,
            LoanType.MORTGAGE: "Real Estate",
            LoanType.AUTO: "Vehicle",
        }
        return types[self]
