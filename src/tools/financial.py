"""Financial calculation engine using numpy-financial.

This module provides a clean abstraction over numpy-financial functions,
following SOLID principles:

- Single Responsibility: Only handles mathematical calculations
- Open/Closed: Extend by adding methods, not modifying existing ones
- Dependency Inversion: Other modules depend on this abstraction

Why use numpy-financial?
- Industry standard, compatible with Excel PMT/IPMT/PPMT
- Vectorized operations for better performance
- Well-tested and maintained by the community
"""

from typing import Protocol

import numpy as np
import numpy_financial as npf
import pandas as pd


class FinancialEngine:
    """Financial calculation engine wrapping numpy-financial.

    This class encapsulates all numpy-financial calls, providing:
    - Consistent interface for loan calculations
    - Easy mocking for unit tests
    - Single place to modify if npf API changes

    Example:
        >>> engine = FinancialEngine()
        >>> monthly = engine.payment(principal=50000, rate=0.05, periods=36)
        >>> print(f"Monthly payment: ${monthly:.2f}")
        Monthly payment: $1498.88
    """

    def payment(self, principal: float, rate: float, periods: int) -> float:
        """Calculate monthly payment (EMI - Equated Monthly Installment).

        Uses the standard amortization formula:
        PMT = P * r * (1+r)^n / ((1+r)^n - 1)

        Args:
            principal: Loan amount
            rate: Annual interest rate (e.g., 0.05 for 5%)
            periods: Number of monthly payments

        Returns:
            Monthly payment amount
        """
        if rate == 0:
            return principal / periods

        monthly_rate = rate / 12
        # npf.pmt returns negative (cash outflow), we return positive
        return float(-npf.pmt(monthly_rate, periods, principal))

    def max_principal(self, payment: float, rate: float, periods: int) -> float:
        """Calculate maximum principal for a given monthly payment.

        Reverse calculation of the PMT formula to find principal.

        Args:
            payment: Maximum affordable monthly payment
            rate: Annual interest rate
            periods: Loan term in months

        Returns:
            Maximum loan amount (principal)
        """
        if rate == 0:
            return payment * periods

        monthly_rate = rate / 12
        # npf.pv calculates present value (principal)
        return float(-npf.pv(monthly_rate, periods, payment))

    def interest_payment(self, principal: float, rate: float, period: int, periods: int) -> float:
        """Calculate interest portion for a specific period.

        Args:
            principal: Original loan amount
            rate: Annual interest rate
            period: Which payment period (1-indexed)
            periods: Total number of periods

        Returns:
            Interest portion of payment for that period
        """
        if rate == 0:
            return 0.0

        monthly_rate = rate / 12
        return float(-npf.ipmt(monthly_rate, period, periods, principal))

    def principal_payment(self, principal: float, rate: float, period: int, periods: int) -> float:
        """Calculate principal portion for a specific period.

        Args:
            principal: Original loan amount
            rate: Annual interest rate
            period: Which payment period (1-indexed)
            periods: Total number of periods

        Returns:
            Principal portion of payment for that period
        """
        if rate == 0:
            return principal / periods

        monthly_rate = rate / 12
        return float(-npf.ppmt(monthly_rate, period, periods, principal))

    def remaining_balance(self, principal: float, rate: float, period: int, periods: int) -> float:
        """Calculate remaining balance after a specific period.

        Args:
            principal: Original loan amount
            rate: Annual interest rate
            period: After which payment period
            periods: Total number of periods

        Returns:
            Remaining balance
        """
        if rate == 0:
            pmt = principal / periods
            return max(0.0, principal - pmt * period)

        monthly_rate = rate / 12
        # Calculate cumulative principal paid up to this period
        per = np.arange(1, period + 1)
        principal_paid = -npf.ppmt(monthly_rate, per, periods, principal)
        total_principal_paid = float(np.sum(principal_paid))
        balance = principal - total_principal_paid
        return max(0.0, balance)

    def amortization_table(
        self,
        principal: float,
        rate: float,
        periods: int,
    ) -> pd.DataFrame:
        """Generate full amortization schedule using vectorized operations.

        This is significantly faster than loop-based calculation,
        especially for long-term loans (e.g., 360 months for mortgage).

        Args:
            principal: Loan amount
            rate: Annual interest rate
            periods: Number of monthly payments

        Returns:
            DataFrame with columns: month, payment, principal, interest, balance
        """
        if rate == 0:
            return self._zero_rate_table(principal, periods)

        monthly_rate = rate / 12
        pmt = float(-npf.pmt(monthly_rate, periods, principal))

        # Vectorized calculation - all periods at once
        per = np.arange(1, periods + 1)
        interest = -npf.ipmt(monthly_rate, per, periods, principal)
        principal_paid = -npf.ppmt(monthly_rate, per, periods, principal)

        # Calculate balance using cumulative principal paid
        # This avoids sign convention issues with npf.fv
        balance = principal - np.cumsum(principal_paid)

        # Fix floating point errors
        balance = np.maximum(0, balance)
        # Ensure final balance is exactly 0
        if len(balance) > 0:
            balance[-1] = 0

        return pd.DataFrame({
            "month": per,
            "payment": pmt,
            "principal": principal_paid,
            "interest": interest,
            "balance": balance,
        })

    def _zero_rate_table(self, principal: float, periods: int) -> pd.DataFrame:
        """Generate amortization table for zero interest rate loans."""
        pmt = principal / periods
        per = np.arange(1, periods + 1)
        balance = principal - pmt * per
        balance = np.maximum(0, balance)

        return pd.DataFrame({
            "month": per,
            "payment": pmt,
            "principal": pmt,
            "interest": 0.0,
            "balance": balance,
        })


# Module-level shared instance - stateless, safe to share
engine = FinancialEngine()
