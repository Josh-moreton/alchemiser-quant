#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Comprehensive test suite for data conversion utilities.

Tests cover:
- Valid conversions (datetime, Decimal)
- Invalid inputs and error handling
- Edge cases (None, empty strings, boundary values)
- In-place mutation behavior
- Round-trip conversion preservation
- Property-based tests for mathematical correctness
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from the_alchemiser.shared.utils.data_conversion import (
    convert_datetime_fields_from_dict,
    convert_datetime_fields_to_dict,
    convert_decimal_fields_from_dict,
    convert_decimal_fields_to_dict,
    convert_nested_order_data,
    convert_nested_rebalance_item_data,
    convert_string_to_datetime,
    convert_string_to_decimal,
)


class TestConvertStringToDatetime:
    """Test convert_string_to_datetime function."""

    @pytest.mark.unit
    def test_convert_valid_iso_format(self):
        """Test converting valid ISO format datetime string."""
        timestamp_str = "2025-01-06T12:30:45+00:00"
        result = convert_string_to_datetime(timestamp_str)

        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 6
        assert result.hour == 12
        assert result.minute == 30
        assert result.second == 45
        assert result.tzinfo is not None

    @pytest.mark.unit
    def test_convert_zulu_suffix(self):
        """Test converting datetime string with 'Z' suffix (Zulu time)."""
        timestamp_str = "2025-01-06T12:30:45Z"
        result = convert_string_to_datetime(timestamp_str)

        assert isinstance(result, datetime)
        assert result.tzinfo is not None
        # Z suffix should be converted to +00:00
        assert result.tzinfo.utcoffset(None).total_seconds() == 0

    @pytest.mark.unit
    def test_convert_with_custom_field_name(self):
        """Test error message includes custom field name."""
        invalid_str = "not-a-datetime"
        field_name = "custom_timestamp"

        with pytest.raises(ValueError) as exc_info:
            convert_string_to_datetime(invalid_str, field_name)

        assert field_name in str(exc_info.value)
        assert invalid_str in str(exc_info.value)

    @pytest.mark.unit
    def test_convert_invalid_format_raises_error(self):
        """Test that invalid datetime format raises ValueError."""
        invalid_str = "2025-13-45"  # Invalid month and day

        with pytest.raises(ValueError) as exc_info:
            convert_string_to_datetime(invalid_str)

        assert "Invalid timestamp format" in str(exc_info.value)
        assert invalid_str in str(exc_info.value)

    @pytest.mark.unit
    def test_convert_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError):
            convert_string_to_datetime("")

    @pytest.mark.unit
    def test_convert_microseconds_preserved(self):
        """Test that microseconds are preserved in conversion."""
        timestamp_str = "2025-01-06T12:30:45.123456+00:00"
        result = convert_string_to_datetime(timestamp_str)

        assert result.microsecond == 123456


class TestConvertStringToDecimal:
    """Test convert_string_to_decimal function."""

    @pytest.mark.unit
    def test_convert_valid_decimal_string(self):
        """Test converting valid decimal string."""
        decimal_str = "123.45"
        result = convert_string_to_decimal(decimal_str)

        assert isinstance(result, Decimal)
        assert result == Decimal("123.45")

    @pytest.mark.unit
    def test_convert_integer_string(self):
        """Test converting integer string to Decimal."""
        decimal_str = "100"
        result = convert_string_to_decimal(decimal_str)

        assert isinstance(result, Decimal)
        assert result == Decimal("100")

    @pytest.mark.unit
    def test_convert_negative_decimal(self):
        """Test converting negative decimal string."""
        decimal_str = "-50.75"
        result = convert_string_to_decimal(decimal_str)

        assert isinstance(result, Decimal)
        assert result == Decimal("-50.75")

    @pytest.mark.unit
    def test_convert_zero(self):
        """Test converting zero."""
        decimal_str = "0"
        result = convert_string_to_decimal(decimal_str)

        assert isinstance(result, Decimal)
        assert result == Decimal("0")

    @pytest.mark.unit
    def test_convert_with_custom_field_name(self):
        """Test error message includes custom field name."""
        invalid_str = "not-a-number"
        field_name = "custom_price"

        with pytest.raises(ValueError) as exc_info:
            convert_string_to_decimal(invalid_str, field_name)

        assert field_name in str(exc_info.value)
        assert invalid_str in str(exc_info.value)

    @pytest.mark.unit
    def test_convert_invalid_string_raises_error(self):
        """Test that invalid decimal string raises ValueError."""
        invalid_str = "abc"

        with pytest.raises(ValueError) as exc_info:
            convert_string_to_decimal(invalid_str)

        assert "Invalid decimal_field value" in str(exc_info.value)

    @pytest.mark.unit
    def test_convert_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError):
            convert_string_to_decimal("")

    @pytest.mark.unit
    def test_convert_scientific_notation(self):
        """Test converting scientific notation."""
        decimal_str = "1.23E+3"
        result = convert_string_to_decimal(decimal_str)

        assert isinstance(result, Decimal)
        assert result == Decimal("1230")


class TestConvertDatetimeFieldsFromDict:
    """Test convert_datetime_fields_from_dict function."""

    @pytest.mark.unit
    def test_convert_single_field(self):
        """Test converting single datetime field in dict."""
        data = {"timestamp": "2025-01-06T12:30:45Z"}
        convert_datetime_fields_from_dict(data, ["timestamp"])

        assert isinstance(data["timestamp"], datetime)
        assert data["timestamp"].year == 2025

    @pytest.mark.unit
    def test_convert_multiple_fields(self):
        """Test converting multiple datetime fields."""
        data = {
            "created_at": "2025-01-06T12:00:00Z",
            "updated_at": "2025-01-06T13:00:00Z",
        }
        convert_datetime_fields_from_dict(data, ["created_at", "updated_at"])

        assert isinstance(data["created_at"], datetime)
        assert isinstance(data["updated_at"], datetime)
        assert data["created_at"].hour == 12
        assert data["updated_at"].hour == 13

    @pytest.mark.unit
    def test_skip_missing_fields(self):
        """Test that missing fields are skipped."""
        data = {"timestamp": "2025-01-06T12:30:45Z"}
        convert_datetime_fields_from_dict(data, ["timestamp", "missing_field"])

        assert isinstance(data["timestamp"], datetime)
        assert "missing_field" not in data

    @pytest.mark.unit
    def test_skip_none_values(self):
        """Test that None values are skipped without error."""
        data = {"timestamp": None}
        # Should not raise error
        convert_datetime_fields_from_dict(data, ["timestamp"])

        # Value should remain None
        assert data["timestamp"] is None

    @pytest.mark.unit
    def test_skip_non_string_values(self):
        """Test that non-string values are skipped."""
        dt = datetime.now(timezone.utc)
        data = {"timestamp": dt}

        # Should not raise error or modify already-datetime value
        convert_datetime_fields_from_dict(data, ["timestamp"])

        assert data["timestamp"] is dt

    @pytest.mark.unit
    def test_in_place_mutation(self):
        """Test that dict is mutated in-place."""
        data = {"timestamp": "2025-01-06T12:30:45Z"}
        original_id = id(data)

        convert_datetime_fields_from_dict(data, ["timestamp"])

        assert id(data) == original_id  # Same dict object
        assert isinstance(data["timestamp"], datetime)

    @pytest.mark.unit
    def test_invalid_datetime_raises_error(self):
        """Test that invalid datetime string raises error."""
        data = {"timestamp": "not-a-datetime"}

        with pytest.raises(ValueError) as exc_info:
            convert_datetime_fields_from_dict(data, ["timestamp"])

        assert "timestamp" in str(exc_info.value)


class TestConvertDecimalFieldsFromDict:
    """Test convert_decimal_fields_from_dict function."""

    @pytest.mark.unit
    def test_convert_single_field(self):
        """Test converting single decimal field in dict."""
        data = {"price": "123.45"}
        convert_decimal_fields_from_dict(data, ["price"])

        assert isinstance(data["price"], Decimal)
        assert data["price"] == Decimal("123.45")

    @pytest.mark.unit
    def test_convert_multiple_fields(self):
        """Test converting multiple decimal fields."""
        data = {
            "price": "100.00",
            "quantity": "5.5",
            "total": "550.00",
        }
        convert_decimal_fields_from_dict(data, ["price", "quantity", "total"])

        assert isinstance(data["price"], Decimal)
        assert isinstance(data["quantity"], Decimal)
        assert isinstance(data["total"], Decimal)

    @pytest.mark.unit
    def test_skip_missing_fields(self):
        """Test that missing fields are skipped."""
        data = {"price": "123.45"}
        convert_decimal_fields_from_dict(data, ["price", "missing_field"])

        assert isinstance(data["price"], Decimal)
        assert "missing_field" not in data

    @pytest.mark.unit
    def test_skip_none_values(self):
        """Test that None values are skipped without error."""
        data = {"price": None}
        # Should not raise error
        convert_decimal_fields_from_dict(data, ["price"])

        # Value should remain None
        assert data["price"] is None

    @pytest.mark.unit
    def test_skip_non_string_values(self):
        """Test that non-string values are skipped."""
        decimal_val = Decimal("100.00")
        data = {"price": decimal_val}

        # Should not raise error or modify already-Decimal value
        convert_decimal_fields_from_dict(data, ["price"])

        assert data["price"] is decimal_val

    @pytest.mark.unit
    def test_in_place_mutation(self):
        """Test that dict is mutated in-place."""
        data = {"price": "123.45"}
        original_id = id(data)

        convert_decimal_fields_from_dict(data, ["price"])

        assert id(data) == original_id  # Same dict object
        assert isinstance(data["price"], Decimal)


class TestConvertDatetimeFieldsToDict:
    """Test convert_datetime_fields_to_dict function."""

    @pytest.mark.unit
    def test_convert_single_field(self):
        """Test converting single datetime field to ISO string."""
        dt = datetime(2025, 1, 6, 12, 30, 45, tzinfo=timezone.utc)
        data = {"timestamp": dt}

        convert_datetime_fields_to_dict(data, ["timestamp"])

        assert isinstance(data["timestamp"], str)
        assert "2025-01-06" in data["timestamp"]
        assert "12:30:45" in data["timestamp"]

    @pytest.mark.unit
    def test_convert_multiple_fields(self):
        """Test converting multiple datetime fields."""
        dt1 = datetime(2025, 1, 6, 12, 0, 0, tzinfo=timezone.utc)
        dt2 = datetime(2025, 1, 6, 13, 0, 0, tzinfo=timezone.utc)
        data = {"created_at": dt1, "updated_at": dt2}

        convert_datetime_fields_to_dict(data, ["created_at", "updated_at"])

        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)

    @pytest.mark.unit
    def test_skip_none_values(self):
        """Test that None values are skipped."""
        data = {"timestamp": None}

        convert_datetime_fields_to_dict(data, ["timestamp"])

        # Value should remain None (truthy check skips it)
        assert data["timestamp"] is None

    @pytest.mark.unit
    def test_skip_missing_fields(self):
        """Test that missing fields are skipped."""
        data = {"timestamp": datetime.now(timezone.utc)}

        convert_datetime_fields_to_dict(data, ["timestamp", "missing_field"])

        assert isinstance(data["timestamp"], str)
        assert "missing_field" not in data

    @pytest.mark.unit
    def test_in_place_mutation(self):
        """Test that dict is mutated in-place."""
        dt = datetime(2025, 1, 6, 12, 30, 45, tzinfo=timezone.utc)
        data = {"timestamp": dt}
        original_id = id(data)

        convert_datetime_fields_to_dict(data, ["timestamp"])

        assert id(data) == original_id  # Same dict object
        assert isinstance(data["timestamp"], str)


class TestConvertDecimalFieldsToDict:
    """Test convert_decimal_fields_to_dict function."""

    @pytest.mark.unit
    def test_convert_single_field(self):
        """Test converting single Decimal field to string."""
        data = {"price": Decimal("123.45")}
        convert_decimal_fields_to_dict(data, ["price"])

        assert isinstance(data["price"], str)
        assert data["price"] == "123.45"

    @pytest.mark.unit
    def test_convert_multiple_fields(self):
        """Test converting multiple Decimal fields."""
        data = {
            "price": Decimal("100.00"),
            "quantity": Decimal("5.5"),
            "total": Decimal("550.00"),
        }
        convert_decimal_fields_to_dict(data, ["price", "quantity", "total"])

        assert isinstance(data["price"], str)
        assert isinstance(data["quantity"], str)
        assert isinstance(data["total"], str)
        assert data["price"] == "100.00"

    @pytest.mark.unit
    def test_skip_none_values(self):
        """Test that None values are skipped."""
        data = {"price": None}

        convert_decimal_fields_to_dict(data, ["price"])

        # Value should remain None
        assert data["price"] is None

    @pytest.mark.unit
    def test_skip_missing_fields(self):
        """Test that missing fields are skipped."""
        data = {"price": Decimal("123.45")}

        convert_decimal_fields_to_dict(data, ["price", "missing_field"])

        assert isinstance(data["price"], str)
        assert "missing_field" not in data

    @pytest.mark.unit
    def test_in_place_mutation(self):
        """Test that dict is mutated in-place."""
        data = {"price": Decimal("123.45")}
        original_id = id(data)

        convert_decimal_fields_to_dict(data, ["price"])

        assert id(data) == original_id  # Same dict object
        assert isinstance(data["price"], str)


class TestConvertNestedOrderData:
    """Test convert_nested_order_data function."""

    @pytest.mark.unit
    def test_convert_complete_order_data(self):
        """Test converting complete order data with all fields."""
        order_data = {
            "order_id": "12345",
            "symbol": "SPY",
            "execution_timestamp": "2025-01-06T12:30:45Z",
            "quantity": "100",
            "filled_quantity": "100",
            "price": "450.50",
            "total_value": "45050.00",
            "commission": "1.00",
            "fees": "0.50",
        }

        result = convert_nested_order_data(order_data)

        # Check datetime conversion
        assert isinstance(result["execution_timestamp"], datetime)
        assert result["execution_timestamp"].year == 2025

        # Check Decimal conversions
        assert isinstance(result["quantity"], Decimal)
        assert isinstance(result["filled_quantity"], Decimal)
        assert isinstance(result["price"], Decimal)
        assert isinstance(result["total_value"], Decimal)
        assert isinstance(result["commission"], Decimal)
        assert isinstance(result["fees"], Decimal)

    @pytest.mark.unit
    def test_convert_order_data_without_timestamp(self):
        """Test converting order data without execution_timestamp."""
        order_data = {
            "order_id": "12345",
            "quantity": "100",
            "price": "450.50",
        }

        result = convert_nested_order_data(order_data)

        # Should not raise error
        assert isinstance(result["quantity"], Decimal)
        assert isinstance(result["price"], Decimal)

    @pytest.mark.unit
    def test_convert_returns_same_dict(self):
        """Test that function returns the same dict object (in-place mutation)."""
        order_data = {
            "quantity": "100",
            "price": "450.50",
        }
        original_id = id(order_data)

        result = convert_nested_order_data(order_data)

        assert id(result) == original_id


class TestConvertNestedRebalanceItemData:
    """Test convert_nested_rebalance_item_data function."""

    @pytest.mark.unit
    def test_convert_complete_rebalance_item_data(self):
        """Test converting complete rebalance item data."""
        item_data = {
            "symbol": "SPY",
            "current_weight": "0.25",
            "target_weight": "0.30",
            "weight_diff": "0.05",
            "target_value": "30000.00",
            "current_value": "25000.00",
            "trade_amount": "5000.00",
        }

        result = convert_nested_rebalance_item_data(item_data)

        # Check all Decimal conversions
        assert isinstance(result["current_weight"], Decimal)
        assert isinstance(result["target_weight"], Decimal)
        assert isinstance(result["weight_diff"], Decimal)
        assert isinstance(result["target_value"], Decimal)
        assert isinstance(result["current_value"], Decimal)
        assert isinstance(result["trade_amount"], Decimal)

    @pytest.mark.unit
    def test_convert_returns_same_dict(self):
        """Test that function returns the same dict object (in-place mutation)."""
        item_data = {
            "current_weight": "0.25",
            "target_weight": "0.30",
        }
        original_id = id(item_data)

        result = convert_nested_rebalance_item_data(item_data)

        assert id(result) == original_id


class TestRoundTripConversions:
    """Test round-trip conversions preserve values."""

    @pytest.mark.unit
    def test_decimal_round_trip(self):
        """Test Decimal -> str -> Decimal preserves value."""
        original = Decimal("123.45")
        as_string = str(original)
        back_to_decimal = Decimal(as_string)

        assert back_to_decimal == original

    @pytest.mark.unit
    def test_datetime_round_trip(self):
        """Test datetime -> ISO string -> datetime preserves value."""
        original = datetime(2025, 1, 6, 12, 30, 45, 123456, tzinfo=timezone.utc)
        as_string = original.isoformat()
        back_to_datetime = datetime.fromisoformat(as_string)

        assert back_to_datetime == original

    @pytest.mark.unit
    def test_dict_datetime_round_trip(self):
        """Test dict datetime field round-trip conversion."""
        original_dt = datetime(2025, 1, 6, 12, 30, 45, tzinfo=timezone.utc)
        data = {"timestamp": original_dt}

        # Convert to string
        convert_datetime_fields_to_dict(data, ["timestamp"])
        assert isinstance(data["timestamp"], str)

        # Convert back to datetime
        convert_datetime_fields_from_dict(data, ["timestamp"])
        assert isinstance(data["timestamp"], datetime)

        # Should be equal (might lose microseconds if not in original string)
        assert data["timestamp"].replace(microsecond=0) == original_dt.replace(microsecond=0)

    @pytest.mark.unit
    def test_dict_decimal_round_trip(self):
        """Test dict Decimal field round-trip conversion."""
        original_decimal = Decimal("123.45")
        data = {"price": original_decimal}

        # Convert to string
        convert_decimal_fields_to_dict(data, ["price"])
        assert isinstance(data["price"], str)

        # Convert back to Decimal
        convert_decimal_fields_from_dict(data, ["price"])
        assert isinstance(data["price"], Decimal)

        # Should be exactly equal
        assert data["price"] == original_decimal


class TestPropertyBasedConversions:
    """Property-based tests using Hypothesis."""

    @pytest.mark.property
    @given(
        st.decimals(
            min_value="-999999999.99",
            max_value="999999999.99",
            allow_nan=False,
            allow_infinity=False,
            places=2,
        )
    )
    def test_decimal_string_conversion_preserves_value(self, original_decimal):
        """Property: Decimal -> str -> Decimal preserves the value."""
        decimal_str = str(original_decimal)
        result = convert_string_to_decimal(decimal_str)

        assert result == original_decimal

    @pytest.mark.property
    @given(
        st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2030, 12, 31),
        )
    )
    def test_datetime_string_conversion_preserves_value(self, original_datetime):
        """Property: datetime -> ISO string -> datetime preserves the value."""
        # Make timezone-aware (as required by trading system)
        if original_datetime.tzinfo is None:
            original_datetime = original_datetime.replace(tzinfo=timezone.utc)

        iso_string = original_datetime.isoformat()
        result = convert_string_to_datetime(iso_string)

        # Timestamps should be equal
        assert result == original_datetime

    @pytest.mark.property
    @given(
        st.decimals(
            min_value="0",
            max_value="1",
            allow_nan=False,
            allow_infinity=False,
            places=4,
        )
    )
    def test_decimal_dict_conversion_idempotent(self, decimal_value):
        """Property: Converting Decimal dict fields twice should be idempotent."""
        data = {"value": str(decimal_value)}

        # First conversion
        convert_decimal_fields_from_dict(data, ["value"])
        first_result = data["value"]

        # Second conversion should not change the value (already Decimal, not string)
        convert_decimal_fields_from_dict(data, ["value"])
        second_result = data["value"]

        assert first_result is second_result  # Same object, no conversion
