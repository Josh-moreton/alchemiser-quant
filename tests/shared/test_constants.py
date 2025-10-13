"""Business Unit: shared | Status: current.

Comprehensive unit tests for shared constants module.

Tests validate type correctness, immutability, and value integrity
of all constants defined in the_alchemiser.shared.constants module.
"""

import pytest
from decimal import Decimal
from hypothesis import given, strategies as st

from the_alchemiser.shared.constants import (
    ACCOUNT_VALUE_LOGGING_DISABLED,
    ALERT_SEVERITIES,
    APPLICATION_NAME,
    CLI_DEPLOY_COMPONENT,
    CONFIDENCE_RANGE,
    DECIMAL_ZERO,
    DEFAULT_AWS_REGION,
    DEFAULT_DATE_FORMAT,
    DSL_ENGINE_MODULE,
    EVENT_SCHEMA_VERSION_DESCRIPTION,
    EVENT_TYPE_DESCRIPTION,
    EXECUTION_HANDLERS_MODULE,
    MINIMUM_PRICE,
    MIN_TRADE_AMOUNT_USD,
    NO_TRADES_REQUIRED,
    ORDER_SIDES,
    ORDER_TYPES,
    PERCENTAGE_RANGE,
    PROGRESS_DESCRIPTION_FORMAT,
    REBALANCE_PLAN_GENERATED,
    RECIPIENT_OVERRIDE_DESCRIPTION,
    SIGNAL_ACTIONS,
    STYLE_BOLD_BLUE,
    STYLE_BOLD_CYAN,
    STYLE_BOLD_GREEN,
    STYLE_BOLD_MAGENTA,
    STYLE_BOLD_RED,
    STYLE_BOLD_YELLOW,
    STYLE_ITALIC,
    UTC_TIMEZONE_SUFFIX,
)


class TestApplicationConstants:
    """Test application-level constants."""

    @pytest.mark.unit
    def test_application_name_type(self):
        """Test APPLICATION_NAME is a string."""
        assert isinstance(APPLICATION_NAME, str)
        assert len(APPLICATION_NAME) > 0

    @pytest.mark.unit
    def test_application_name_value(self):
        """Test APPLICATION_NAME has expected value."""
        assert APPLICATION_NAME == "The Alchemiser"


class TestDateTimeConstants:
    """Test date and time format constants."""

    @pytest.mark.unit
    def test_default_date_format_type(self):
        """Test DEFAULT_DATE_FORMAT is a valid string."""
        assert isinstance(DEFAULT_DATE_FORMAT, str)
        assert "%" in DEFAULT_DATE_FORMAT

    @pytest.mark.unit
    def test_utc_timezone_suffix_type(self):
        """Test UTC_TIMEZONE_SUFFIX is a string."""
        assert isinstance(UTC_TIMEZONE_SUFFIX, str)
        assert UTC_TIMEZONE_SUFFIX == "+00:00"


class TestUIMessageConstants:
    """Test UI and message constants."""

    @pytest.mark.unit
    def test_rebalance_plan_generated_contains_emoji(self):
        """Test REBALANCE_PLAN_GENERATED contains expected emoji."""
        assert isinstance(REBALANCE_PLAN_GENERATED, str)
        assert "📋" in REBALANCE_PLAN_GENERATED

    @pytest.mark.unit
    def test_no_trades_required_message(self):
        """Test NO_TRADES_REQUIRED message format."""
        assert isinstance(NO_TRADES_REQUIRED, str)
        assert "📋" in NO_TRADES_REQUIRED
        assert "balanced" in NO_TRADES_REQUIRED.lower()

    @pytest.mark.unit
    def test_account_value_logging_disabled_message(self):
        """Test ACCOUNT_VALUE_LOGGING_DISABLED is a string."""
        assert isinstance(ACCOUNT_VALUE_LOGGING_DISABLED, str)


class TestModuleIdentifiers:
    """Test module identifier constants."""

    @pytest.mark.unit
    def test_cli_deploy_component_format(self):
        """Test CLI_DEPLOY_COMPONENT follows naming convention."""
        assert isinstance(CLI_DEPLOY_COMPONENT, str)
        assert "." in CLI_DEPLOY_COMPONENT
        assert CLI_DEPLOY_COMPONENT == "cli.deploy"

    @pytest.mark.unit
    def test_dsl_engine_module_format(self):
        """Test DSL_ENGINE_MODULE follows naming convention."""
        assert isinstance(DSL_ENGINE_MODULE, str)
        assert "." in DSL_ENGINE_MODULE
        assert DSL_ENGINE_MODULE.startswith("strategy_v2")

    @pytest.mark.unit
    def test_execution_handlers_module_format(self):
        """Test EXECUTION_HANDLERS_MODULE follows naming convention."""
        assert isinstance(EXECUTION_HANDLERS_MODULE, str)
        assert "." in EXECUTION_HANDLERS_MODULE
        assert EXECUTION_HANDLERS_MODULE.startswith("execution_v2")


class TestEventSchemaConstants:
    """Test event schema description constants."""

    @pytest.mark.unit
    def test_event_schema_version_description_type(self):
        """Test EVENT_SCHEMA_VERSION_DESCRIPTION is a string."""
        assert isinstance(EVENT_SCHEMA_VERSION_DESCRIPTION, str)
        assert len(EVENT_SCHEMA_VERSION_DESCRIPTION) > 0

    @pytest.mark.unit
    def test_event_type_description_type(self):
        """Test EVENT_TYPE_DESCRIPTION is a string."""
        assert isinstance(EVENT_TYPE_DESCRIPTION, str)

    @pytest.mark.unit
    def test_recipient_override_description_type(self):
        """Test RECIPIENT_OVERRIDE_DESCRIPTION is a string."""
        assert isinstance(RECIPIENT_OVERRIDE_DESCRIPTION, str)


class TestStyleConstants:
    """Test UI/CLI styling constants."""

    @pytest.mark.unit
    def test_all_style_constants_are_strings(self):
        """Test all STYLE_* constants are strings."""
        styles = [
            STYLE_BOLD_CYAN,
            STYLE_ITALIC,
            STYLE_BOLD_BLUE,
            STYLE_BOLD_GREEN,
            STYLE_BOLD_RED,
            STYLE_BOLD_YELLOW,
            STYLE_BOLD_MAGENTA,
        ]
        for style in styles:
            assert isinstance(style, str)

    @pytest.mark.unit
    def test_progress_description_format(self):
        """Test PROGRESS_DESCRIPTION_FORMAT is a valid format string."""
        assert isinstance(PROGRESS_DESCRIPTION_FORMAT, str)
        assert "{" in PROGRESS_DESCRIPTION_FORMAT
        assert "}" in PROGRESS_DESCRIPTION_FORMAT


class TestBusinessLogicConstants:
    """Test business logic constants with Decimal types."""

    @pytest.mark.unit
    def test_decimal_zero_type(self):
        """Test DECIMAL_ZERO is a Decimal type."""
        assert isinstance(DECIMAL_ZERO, Decimal)
        assert DECIMAL_ZERO == Decimal("0")

    @pytest.mark.unit
    def test_min_trade_amount_usd_type(self):
        """Test MIN_TRADE_AMOUNT_USD is a Decimal."""
        assert isinstance(MIN_TRADE_AMOUNT_USD, Decimal)
        assert MIN_TRADE_AMOUNT_USD > Decimal("0")

    @pytest.mark.unit
    def test_min_trade_amount_usd_value(self):
        """Test MIN_TRADE_AMOUNT_USD has expected value."""
        assert MIN_TRADE_AMOUNT_USD == Decimal("5")

    @pytest.mark.unit
    def test_minimum_price_type(self):
        """Test MINIMUM_PRICE is a Decimal."""
        assert isinstance(MINIMUM_PRICE, Decimal)
        assert MINIMUM_PRICE > Decimal("0")

    @pytest.mark.unit
    def test_minimum_price_value(self):
        """Test MINIMUM_PRICE has expected value (1 cent)."""
        assert MINIMUM_PRICE == Decimal("0.01")

    @pytest.mark.unit
    def test_decimal_zero_immutable(self):
        """Test DECIMAL_ZERO immutability (Decimal is immutable by design)."""
        original_value = DECIMAL_ZERO
        # Attempt to modify (Decimal is immutable, so this creates a new object)
        _ = DECIMAL_ZERO + Decimal("1")
        assert DECIMAL_ZERO == original_value


class TestValidationConstants:
    """Test validation range and enumeration constants."""

    @pytest.mark.unit
    def test_confidence_range_is_tuple(self):
        """Test CONFIDENCE_RANGE is a tuple."""
        assert isinstance(CONFIDENCE_RANGE, tuple)
        assert len(CONFIDENCE_RANGE) == 2

    @pytest.mark.unit
    def test_confidence_range_values(self):
        """Test CONFIDENCE_RANGE has correct Decimal bounds."""
        min_val, max_val = CONFIDENCE_RANGE
        assert isinstance(min_val, Decimal)
        assert isinstance(max_val, Decimal)
        assert min_val == Decimal("0")
        assert max_val == Decimal("1")
        assert min_val <= max_val

    @pytest.mark.unit
    def test_percentage_range_is_tuple(self):
        """Test PERCENTAGE_RANGE is a tuple."""
        assert isinstance(PERCENTAGE_RANGE, tuple)
        assert len(PERCENTAGE_RANGE) == 2

    @pytest.mark.unit
    def test_percentage_range_values(self):
        """Test PERCENTAGE_RANGE has correct Decimal bounds."""
        min_val, max_val = PERCENTAGE_RANGE
        assert isinstance(min_val, Decimal)
        assert isinstance(max_val, Decimal)
        assert min_val == Decimal("0")
        assert max_val == Decimal("1")
        assert min_val <= max_val

    @pytest.mark.unit
    def test_signal_actions_is_set(self):
        """Test SIGNAL_ACTIONS is a set."""
        assert isinstance(SIGNAL_ACTIONS, (set, frozenset))

    @pytest.mark.unit
    def test_signal_actions_values(self):
        """Test SIGNAL_ACTIONS contains expected values."""
        expected = {"BUY", "SELL", "HOLD"}
        assert SIGNAL_ACTIONS == expected

    @pytest.mark.unit
    def test_signal_actions_all_uppercase(self):
        """Test all SIGNAL_ACTIONS are uppercase."""
        for action in SIGNAL_ACTIONS:
            assert action.isupper()

    @pytest.mark.unit
    def test_alert_severities_is_set(self):
        """Test ALERT_SEVERITIES is a set."""
        assert isinstance(ALERT_SEVERITIES, (set, frozenset))

    @pytest.mark.unit
    def test_alert_severities_values(self):
        """Test ALERT_SEVERITIES contains expected values."""
        expected = {"INFO", "WARNING", "ERROR"}
        assert ALERT_SEVERITIES == expected

    @pytest.mark.unit
    def test_alert_severities_all_uppercase(self):
        """Test all ALERT_SEVERITIES are uppercase."""
        for severity in ALERT_SEVERITIES:
            assert severity.isupper()

    @pytest.mark.unit
    def test_order_types_is_set(self):
        """Test ORDER_TYPES is a set."""
        assert isinstance(ORDER_TYPES, (set, frozenset))

    @pytest.mark.unit
    def test_order_types_values(self):
        """Test ORDER_TYPES contains expected values."""
        expected = {"market", "limit"}
        assert ORDER_TYPES == expected

    @pytest.mark.unit
    def test_order_types_all_lowercase(self):
        """Test all ORDER_TYPES are lowercase."""
        for order_type in ORDER_TYPES:
            assert order_type.islower()

    @pytest.mark.unit
    def test_order_sides_is_set(self):
        """Test ORDER_SIDES is a set."""
        assert isinstance(ORDER_SIDES, (set, frozenset))

    @pytest.mark.unit
    def test_order_sides_values(self):
        """Test ORDER_SIDES contains expected values."""
        expected = {"buy", "sell"}
        assert ORDER_SIDES == expected

    @pytest.mark.unit
    def test_order_sides_all_lowercase(self):
        """Test all ORDER_SIDES are lowercase."""
        for side in ORDER_SIDES:
            assert side.islower()


class TestAWSConfiguration:
    """Test AWS configuration constants."""

    @pytest.mark.unit
    def test_default_aws_region_type(self):
        """Test DEFAULT_AWS_REGION is a string."""
        assert isinstance(DEFAULT_AWS_REGION, str)

    @pytest.mark.unit
    def test_default_aws_region_format(self):
        """Test DEFAULT_AWS_REGION follows AWS region format."""
        assert DEFAULT_AWS_REGION == "eu-west-2"
        # AWS region format: region-direction-number
        parts = DEFAULT_AWS_REGION.split("-")
        assert len(parts) == 3


class TestConstantsImmutability:
    """Test immutability properties of constants."""

    @pytest.mark.unit
    def test_tuple_constants_are_immutable(self):
        """Test tuple constants cannot be modified."""
        ranges = [CONFIDENCE_RANGE, PERCENTAGE_RANGE]
        for range_tuple in ranges:
            with pytest.raises(TypeError):
                range_tuple[0] = Decimal("999")  # type: ignore

    @pytest.mark.unit
    def test_decimal_constants_are_immutable(self):
        """Test Decimal constants are immutable (new object on operations)."""
        original_zero = DECIMAL_ZERO
        original_min_trade = MIN_TRADE_AMOUNT_USD
        original_min_price = MINIMUM_PRICE

        # Operations create new objects
        _ = DECIMAL_ZERO + Decimal("1")
        _ = MIN_TRADE_AMOUNT_USD * Decimal("2")
        _ = MINIMUM_PRICE / Decimal("10")

        # Originals unchanged
        assert DECIMAL_ZERO == original_zero
        assert MIN_TRADE_AMOUNT_USD == original_min_trade
        assert MINIMUM_PRICE == original_min_price


class TestConstantsExports:
    """Test __all__ exports are complete and correct."""

    @pytest.mark.unit
    def test_all_constants_exported(self):
        """Test all public constants are in __all__."""
        from the_alchemiser.shared import constants

        # Get all uppercase constants (convention for module-level constants)
        module_constants = {
            name
            for name in dir(constants)
            if not name.startswith("_") and name.isupper()
        }

        # Expected exports from __all__
        expected_exports = set(constants.__all__)

        # All uppercase constants should be in __all__
        assert module_constants.issubset(expected_exports)

    @pytest.mark.unit
    def test_no_unexpected_exports(self):
        """Test __all__ doesn't export private or imported items."""
        from the_alchemiser.shared import constants

        for name in constants.__all__:
            # Should be defined in module
            assert hasattr(constants, name)
            # Should not start with underscore
            assert not name.startswith("_")


# Property-based tests using Hypothesis
class TestConstantsProperties:
    """Property-based tests for constants validation ranges."""

    @pytest.mark.property
    @given(st.decimals(min_value="0", max_value="1", allow_nan=False, allow_infinity=False))
    def test_confidence_range_bounds(self, value):
        """Property: values in CONFIDENCE_RANGE should be valid."""
        min_val, max_val = CONFIDENCE_RANGE
        assert min_val <= value <= max_val

    @pytest.mark.property
    @given(st.decimals(min_value="0", max_value="1", allow_nan=False, allow_infinity=False))
    def test_percentage_range_bounds(self, value):
        """Property: values in PERCENTAGE_RANGE should be valid."""
        min_val, max_val = PERCENTAGE_RANGE
        assert min_val <= value <= max_val

    @pytest.mark.property
    @given(st.sampled_from(["BUY", "SELL", "HOLD"]))
    def test_signal_actions_membership(self, action):
        """Property: all valid signal actions should be in SIGNAL_ACTIONS."""
        assert action in SIGNAL_ACTIONS

    @pytest.mark.property
    @given(st.sampled_from(["INFO", "WARNING", "ERROR"]))
    def test_alert_severities_membership(self, severity):
        """Property: all valid alert severities should be in ALERT_SEVERITIES."""
        assert severity in ALERT_SEVERITIES

    @pytest.mark.property
    @given(st.sampled_from(["market", "limit"]))
    def test_order_types_membership(self, order_type):
        """Property: all valid order types should be in ORDER_TYPES."""
        assert order_type in ORDER_TYPES

    @pytest.mark.property
    @given(st.sampled_from(["buy", "sell"]))
    def test_order_sides_membership(self, side):
        """Property: all valid order sides should be in ORDER_SIDES."""
        assert side in ORDER_SIDES
