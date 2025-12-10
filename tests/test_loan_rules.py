"""Unit tests for loan_rules module.

Tests the rule-based LTV system for UAE mortgage regulations.
Follows pytest best practices:
- Parametrized tests for multiple scenarios
- Clear test naming: test_<what>_<scenario>_<expected>
- AAA pattern: Arrange, Act, Assert
"""

import pytest
from src.tools.loan_rules import (
    MortgageRule,
    AutoLoanRule,
    get_mortgage_rule,
    get_auto_loan_rule,
    MORTGAGE_RULES,
    AUTO_LOAN_RULES,
    get_available_residency_types,
    get_available_property_types,
    describe_mortgage_rules,
)


# =============================================================================
# TEST DATA - UAE Central Bank Regulations (2024)
# =============================================================================

# Mortgage rule test cases: (residency, property_type, price, expected_ltv, expected_down)
UAE_MORTGAGE_TEST_CASES = [
    # UAE Citizens
    pytest.param("citizen", "first", 3_000_000, 0.85, 0.15, id="citizen-first-under5m"),
    pytest.param("citizen", "first", 5_000_000, 0.85, 0.15, id="citizen-first-at5m"),
    pytest.param("citizen", "first", 6_000_000, 0.80, 0.20, id="citizen-first-over5m"),
    pytest.param("citizen", "second", 2_000_000, 0.75, 0.25, id="citizen-second"),
    # Expats
    pytest.param("expat", "first", 2_000_000, 0.80, 0.20, id="expat-first"),
    pytest.param("expat", "second", 3_000_000, 0.65, 0.35, id="expat-second"),
    # Non-residents
    pytest.param("non_resident", "first", 1_000_000, 0.50, 0.50, id="non-resident-first"),
    pytest.param("non_resident", "second", 1_000_000, 0.50, 0.50, id="non-resident-second"),
]


# =============================================================================
# MORTGAGE RULE MODEL TESTS
# =============================================================================

class TestMortgageRuleModel:
    """Tests for MortgageRule Pydantic model validation."""

    def test_valid_rule_creation(self):
        """Valid parameters should create a rule successfully."""
        rule = MortgageRule(max_ltv=0.80, min_down_payment=0.20)

        assert rule.max_ltv == 0.80
        assert rule.min_down_payment == 0.20

    def test_rule_with_all_conditions(self):
        """Rule with all conditions should be created correctly."""
        rule = MortgageRule(
            max_ltv=0.85,
            min_down_payment=0.15,
            residency="citizen",
            property_type="first",
            price_max=5_000_000,
        )

        assert rule.residency == "citizen"
        assert rule.property_type == "first"
        assert rule.price_max == 5_000_000

    @pytest.mark.parametrize("invalid_ltv", [1.5, -0.1, 2.0])
    def test_ltv_validation_rejects_invalid_values(self, invalid_ltv):
        """LTV outside [0, 1] range should be rejected."""
        with pytest.raises(ValueError):
            MortgageRule(max_ltv=invalid_ltv, min_down_payment=0.20)

    @pytest.mark.parametrize("invalid_down", [1.5, -0.1, 2.0])
    def test_down_payment_validation_rejects_invalid_values(self, invalid_down):
        """Down payment outside [0, 1] range should be rejected."""
        with pytest.raises(ValueError):
            MortgageRule(max_ltv=0.80, min_down_payment=invalid_down)


class TestMortgageRuleMatching:
    """Tests for MortgageRule.matches() method."""

    @pytest.fixture
    def citizen_first_rule(self):
        """Rule for UAE citizen buying first home under 5M."""
        return MortgageRule(
            max_ltv=0.85,
            min_down_payment=0.15,
            residency="citizen",
            property_type="first",
            price_max=5_000_000,
        )

    def test_exact_match_returns_true(self, citizen_first_rule):
        """Exact condition match should return True."""
        result = citizen_first_rule.matches("citizen", "first", 3_000_000)
        assert result is True

    def test_residency_mismatch_returns_false(self, citizen_first_rule):
        """Residency mismatch should return False."""
        result = citizen_first_rule.matches("expat", "first", 3_000_000)
        assert result is False

    def test_property_type_mismatch_returns_false(self, citizen_first_rule):
        """Property type mismatch should return False."""
        result = citizen_first_rule.matches("citizen", "second", 3_000_000)
        assert result is False

    def test_price_over_max_returns_false(self, citizen_first_rule):
        """Price above price_max should return False."""
        result = citizen_first_rule.matches("citizen", "first", 6_000_000)
        assert result is False

    def test_none_conditions_match_any_value(self):
        """None conditions should match any input value."""
        rule = MortgageRule(max_ltv=0.75, min_down_payment=0.25)

        # Should match any residency, property type, and price
        assert rule.matches("citizen", "first", 1_000_000) is True
        assert rule.matches("expat", "second", 5_000_000) is True
        assert rule.matches("non_resident", "investment", 10_000_000) is True

    @pytest.mark.parametrize("price,expected", [
        pytest.param(4_999_999, True, id="below-max"),
        pytest.param(5_000_000, True, id="at-max"),
        pytest.param(5_000_001, False, id="above-max"),
    ])
    def test_price_max_boundary(self, price, expected):
        """Price max boundary should be inclusive (<=)."""
        rule = MortgageRule(
            max_ltv=0.85,
            min_down_payment=0.15,
            price_max=5_000_000,
        )
        assert rule.matches("expat", "first", price) is expected

    @pytest.mark.parametrize("price,expected", [
        pytest.param(4_999_999, False, id="below-min"),
        pytest.param(5_000_000, True, id="at-min"),
        pytest.param(5_000_001, True, id="above-min"),
    ])
    def test_price_min_boundary(self, price, expected):
        """Price min boundary should be inclusive (>=)."""
        rule = MortgageRule(
            max_ltv=0.80,
            min_down_payment=0.20,
            price_min=5_000_000,
        )
        assert rule.matches("expat", "first", price) is expected


# =============================================================================
# GET_MORTGAGE_RULE FUNCTION TESTS
# =============================================================================

class TestGetMortgageRule:
    """Tests for get_mortgage_rule() function."""

    @pytest.mark.parametrize(
        "residency,property_type,price,expected_ltv,expected_down",
        UAE_MORTGAGE_TEST_CASES,
    )
    def test_uae_mortgage_regulations(
        self, residency, property_type, price, expected_ltv, expected_down
    ):
        """UAE Central Bank regulations should be correctly applied."""
        rule = get_mortgage_rule(residency, property_type, price)

        assert rule.max_ltv == expected_ltv
        assert rule.min_down_payment == expected_down

    def test_default_parameters_return_expat_first(self):
        """Default parameters should return expat first home rule."""
        rule = get_mortgage_rule()

        assert rule.max_ltv == 0.80
        assert rule.min_down_payment == 0.20

    def test_unknown_residency_uses_default_rule(self):
        """Unknown residency should fall back to default rule."""
        rule = get_mortgage_rule("unknown_status", "first", 1_000_000)

        # Default rule: 75% LTV, 25% down
        assert rule.max_ltv == 0.75
        assert rule.min_down_payment == 0.25

    def test_unknown_property_type_uses_default_rule(self):
        """Unknown property type should fall back to default rule."""
        rule = get_mortgage_rule("expat", "commercial", 1_000_000)

        assert rule.max_ltv == 0.75
        assert rule.min_down_payment == 0.25

    def test_citizen_5m_boundary_exact(self):
        """Citizen at exactly 5M should get 85% LTV."""
        rule_at_5m = get_mortgage_rule("citizen", "first", 5_000_000)
        rule_over_5m = get_mortgage_rule("citizen", "first", 5_000_001)

        assert rule_at_5m.max_ltv == 0.85, "At 5M should get 85% LTV"
        assert rule_over_5m.max_ltv == 0.80, "Over 5M should get 80% LTV"


# =============================================================================
# AUTO LOAN RULE TESTS
# =============================================================================

class TestAutoLoanRule:
    """Tests for AutoLoanRule model and matching."""

    def test_valid_rule_creation(self):
        """Valid auto loan rule should be created successfully."""
        rule = AutoLoanRule(max_ltv=0.90, min_down_payment=0.10)

        assert rule.max_ltv == 0.90
        assert rule.min_down_payment == 0.10

    @pytest.mark.parametrize("vehicle_type,expected_ltv,expected_down", [
        pytest.param("new", 0.90, 0.10, id="new-vehicle"),
        pytest.param("used", 0.80, 0.20, id="used-vehicle"),
    ])
    def test_vehicle_type_rules(self, vehicle_type, expected_ltv, expected_down):
        """Auto loan rules should vary by vehicle type."""
        rule = get_auto_loan_rule("expat", vehicle_type)

        assert rule.max_ltv == expected_ltv
        assert rule.min_down_payment == expected_down

    def test_unknown_vehicle_type_uses_default(self):
        """Unknown vehicle type should use default rule."""
        rule = get_auto_loan_rule("expat", "unknown_type")

        # Default: 85% LTV, 15% down
        assert rule.max_ltv == 0.85
        assert rule.min_down_payment == 0.15


# =============================================================================
# RULE LIST INTEGRITY TESTS
# =============================================================================

class TestRuleListIntegrity:
    """Tests to verify rule lists are properly configured."""

    def test_mortgage_rules_not_empty(self):
        """Mortgage rules list should not be empty."""
        assert len(MORTGAGE_RULES) > 0

    def test_auto_loan_rules_not_empty(self):
        """Auto loan rules list should not be empty."""
        assert len(AUTO_LOAN_RULES) > 0

    def test_mortgage_rules_has_default_fallback(self):
        """Last mortgage rule should be a catch-all default (no conditions)."""
        default_rule = MORTGAGE_RULES[-1]

        assert default_rule.residency is None
        assert default_rule.property_type is None
        assert default_rule.price_max is None
        assert default_rule.price_min is None

    def test_all_mortgage_rules_ltv_plus_down_equals_one(self):
        """LTV + down payment should equal 1.0 for all rules."""
        for rule in MORTGAGE_RULES:
            total = rule.max_ltv + rule.min_down_payment
            assert abs(total - 1.0) < 0.01, (
                f"Rule LTV ({rule.max_ltv}) + down ({rule.min_down_payment}) "
                f"= {total}, expected 1.0"
            )

    def test_all_auto_loan_rules_ltv_plus_down_equals_one(self):
        """LTV + down payment should equal 1.0 for all auto loan rules."""
        for rule in AUTO_LOAN_RULES:
            total = rule.max_ltv + rule.min_down_payment
            assert abs(total - 1.0) < 0.01


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

class TestHelperFunctions:
    """Tests for helper utility functions."""

    def test_get_available_residency_types(self):
        """Should return list of supported residency types."""
        types = get_available_residency_types()

        assert "citizen" in types
        assert "expat" in types
        assert "non_resident" in types

    def test_get_available_property_types(self):
        """Should return list of supported property types."""
        types = get_available_property_types()

        assert "first" in types
        assert "second" in types

    def test_describe_mortgage_rules_returns_string(self):
        """Should return a human-readable string description."""
        description = describe_mortgage_rules()

        assert isinstance(description, str)
        assert "LTV" in description
        assert len(description) > 100  # Should be substantial


# =============================================================================
# EDGE CASES AND REGRESSION TESTS
# =============================================================================

class TestEdgeCases:
    """Edge cases and potential regression scenarios."""

    def test_zero_price_uses_default_for_price_based_rules(self):
        """Zero price should still match rules without price conditions."""
        rule = get_mortgage_rule("expat", "first", 0)

        # Should get expat first home rule (no price condition)
        assert rule.max_ltv == 0.80

    def test_very_large_price(self):
        """Very large price should still return a valid rule."""
        rule = get_mortgage_rule("citizen", "first", 100_000_000)

        # Should get citizen first >5M rule
        assert rule.max_ltv == 0.80
        assert rule.min_down_payment == 0.20

    def test_rule_matching_is_case_sensitive(self):
        """Rule matching should be case-sensitive."""
        # "Citizen" != "citizen"
        rule = get_mortgage_rule("Citizen", "first", 3_000_000)

        # Should fall back to default
        assert rule.max_ltv == 0.75


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
