"""Business Unit: shared | Status: current

Comprehensive unit tests for data conversion utilities.

This test suite provides full coverage of data conversion utility functions
including string-to-type conversions, field conversion helpers, and nested
data structure conversions.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

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
    """Test string to datetime conversion."""

    def test_iso_format_timestamp(self):
        """Test conversion of ISO format timestamp."""
        timestamp_str = "2023-10-05T12:30:45+00:00"
        result = convert_string_to_datetime(timestamp_str)
        
        assert isinstance(result, datetime)
        assert result.year == 2023
        assert result.month == 10
        assert result.day == 5
        assert result.hour == 12
        assert result.minute == 30
        assert result.second == 45

    def test_zulu_time_suffix(self):
        """Test conversion of timestamp with Z suffix (Zulu time)."""
        timestamp_str = "2023-10-05T12:30:45Z"
        result = convert_string_to_datetime(timestamp_str)
        
        assert isinstance(result, datetime)
        assert result.year == 2023
        assert result.month == 10
        assert result.day == 5
        assert result.hour == 12
        assert result.minute == 30
        assert result.second == 45
        assert result.tzinfo is not None

    def test_invalid_timestamp_raises_error(self):
        """Test that invalid timestamp raises ValueError."""
        with pytest.raises(ValueError, match="Invalid timestamp format"):
            convert_string_to_datetime("invalid-timestamp")

    def test_custom_field_name_in_error(self):
        """Test that custom field name appears in error message."""
        with pytest.raises(ValueError, match="Invalid execution_time format"):
            convert_string_to_datetime("invalid-timestamp", field_name="execution_time")

    def test_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError):
            convert_string_to_datetime("")

    def test_microseconds_preserved(self):
        """Test that microseconds are preserved in conversion."""
        timestamp_str = "2023-10-05T12:30:45.123456+00:00"
        result = convert_string_to_datetime(timestamp_str)
        
        assert result.microsecond == 123456


class TestConvertStringToDecimal:
    """Test string to Decimal conversion."""

    def test_integer_string(self):
        """Test conversion of integer string to Decimal."""
        result = convert_string_to_decimal("100")
        
        assert isinstance(result, Decimal)
        assert result == Decimal("100")

    def test_decimal_string(self):
        """Test conversion of decimal string to Decimal."""
        result = convert_string_to_decimal("123.456")
        
        assert isinstance(result, Decimal)
        assert result == Decimal("123.456")

    def test_negative_value(self):
        """Test conversion of negative decimal string."""
        result = convert_string_to_decimal("-50.25")
        
        assert isinstance(result, Decimal)
        assert result == Decimal("-50.25")

    def test_scientific_notation(self):
        """Test conversion of scientific notation string."""
        result = convert_string_to_decimal("1.5e3")
        
        assert isinstance(result, Decimal)
        assert result == Decimal("1500")

    def test_invalid_string_raises_error(self):
        """Test that invalid string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid decimal_field value"):
            convert_string_to_decimal("invalid")

    def test_custom_field_name_in_error(self):
        """Test that custom field name appears in error message."""
        with pytest.raises(ValueError, match="Invalid price value"):
            convert_string_to_decimal("invalid", field_name="price")

    def test_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError):
            convert_string_to_decimal("")

    def test_zero_value(self):
        """Test conversion of zero string."""
        result = convert_string_to_decimal("0")
        
        assert result == Decimal("0")

    def test_high_precision_decimal(self):
        """Test conversion of high precision decimal."""
        result = convert_string_to_decimal("0.123456789012345678")
        
        assert result == Decimal("0.123456789012345678")


class TestConvertDatetimeFieldsFromDict:
    """Test in-place datetime field conversion from dict."""

    def test_converts_single_datetime_field(self):
        """Test conversion of single datetime field."""
        data = {"timestamp": "2023-10-05T12:30:45+00:00", "other": "value"}
        convert_datetime_fields_from_dict(data, ["timestamp"])
        
        assert isinstance(data["timestamp"], datetime)
        assert data["other"] == "value"

    def test_converts_multiple_datetime_fields(self):
        """Test conversion of multiple datetime fields."""
        data = {
            "created_at": "2023-10-05T12:30:45+00:00",
            "updated_at": "2023-10-05T13:30:45+00:00",
            "other": "value",
        }
        convert_datetime_fields_from_dict(data, ["created_at", "updated_at"])
        
        assert isinstance(data["created_at"], datetime)
        assert isinstance(data["updated_at"], datetime)
        assert data["other"] == "value"

    def test_skips_missing_fields(self):
        """Test that missing fields are skipped without error."""
        data = {"timestamp": "2023-10-05T12:30:45+00:00"}
        convert_datetime_fields_from_dict(data, ["timestamp", "missing_field"])
        
        assert isinstance(data["timestamp"], datetime)
        assert "missing_field" not in data

    def test_skips_non_string_fields(self):
        """Test that non-string fields are skipped."""
        existing_dt = datetime(2023, 10, 5, 12, 30, 45, tzinfo=timezone.utc)
        data = {"timestamp": existing_dt, "other": 123}
        convert_datetime_fields_from_dict(data, ["timestamp", "other"])
        
        assert data["timestamp"] is existing_dt
        assert data["other"] == 123

    def test_handles_zulu_time_suffix(self):
        """Test conversion of timestamp with Z suffix."""
        data = {"timestamp": "2023-10-05T12:30:45Z"}
        convert_datetime_fields_from_dict(data, ["timestamp"])
        
        assert isinstance(data["timestamp"], datetime)

    def test_empty_field_list(self):
        """Test with empty field list."""
        data = {"timestamp": "2023-10-05T12:30:45+00:00"}
        convert_datetime_fields_from_dict(data, [])
        
        assert isinstance(data["timestamp"], str)

    def test_modifies_dict_in_place(self):
        """Test that the function modifies dict in-place."""
        data = {"timestamp": "2023-10-05T12:30:45+00:00"}
        original_id = id(data)
        convert_datetime_fields_from_dict(data, ["timestamp"])
        
        assert id(data) == original_id


class TestConvertDecimalFieldsFromDict:
    """Test in-place decimal field conversion from dict."""

    def test_converts_single_decimal_field(self):
        """Test conversion of single decimal field."""
        data = {"price": "123.456", "other": "value"}
        convert_decimal_fields_from_dict(data, ["price"])
        
        assert isinstance(data["price"], Decimal)
        assert data["price"] == Decimal("123.456")
        assert data["other"] == "value"

    def test_converts_multiple_decimal_fields(self):
        """Test conversion of multiple decimal fields."""
        data = {"price": "123.45", "quantity": "10", "other": "value"}
        convert_decimal_fields_from_dict(data, ["price", "quantity"])
        
        assert isinstance(data["price"], Decimal)
        assert isinstance(data["quantity"], Decimal)
        assert data["other"] == "value"

    def test_skips_missing_fields(self):
        """Test that missing fields are skipped without error."""
        data = {"price": "123.456"}
        convert_decimal_fields_from_dict(data, ["price", "missing_field"])
        
        assert isinstance(data["price"], Decimal)
        assert "missing_field" not in data

    def test_skips_none_fields(self):
        """Test that None fields are skipped."""
        data = {"price": "123.456", "optional": None}
        convert_decimal_fields_from_dict(data, ["price", "optional"])
        
        assert isinstance(data["price"], Decimal)
        assert data["optional"] is None

    def test_skips_non_string_fields(self):
        """Test that non-string fields are skipped."""
        existing_decimal = Decimal("123.456")
        data = {"price": existing_decimal, "other": 123}
        convert_decimal_fields_from_dict(data, ["price", "other"])
        
        assert data["price"] is existing_decimal
        assert data["other"] == 123

    def test_empty_field_list(self):
        """Test with empty field list."""
        data = {"price": "123.456"}
        convert_decimal_fields_from_dict(data, [])
        
        assert isinstance(data["price"], str)

    def test_modifies_dict_in_place(self):
        """Test that the function modifies dict in-place."""
        data = {"price": "123.456"}
        original_id = id(data)
        convert_decimal_fields_from_dict(data, ["price"])
        
        assert id(data) == original_id


class TestConvertDatetimeFieldsToDict:
    """Test in-place datetime to string conversion in dict."""

    def test_converts_single_datetime_field(self):
        """Test conversion of single datetime field to string."""
        dt = datetime(2023, 10, 5, 12, 30, 45, tzinfo=timezone.utc)
        data = {"timestamp": dt, "other": "value"}
        convert_datetime_fields_to_dict(data, ["timestamp"])
        
        assert isinstance(data["timestamp"], str)
        assert "2023-10-05T12:30:45" in data["timestamp"]
        assert data["other"] == "value"

    def test_converts_multiple_datetime_fields(self):
        """Test conversion of multiple datetime fields."""
        dt1 = datetime(2023, 10, 5, 12, 30, 45, tzinfo=timezone.utc)
        dt2 = datetime(2023, 10, 5, 13, 30, 45, tzinfo=timezone.utc)
        data = {"created_at": dt1, "updated_at": dt2, "other": "value"}
        convert_datetime_fields_to_dict(data, ["created_at", "updated_at"])
        
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)

    def test_skips_missing_fields(self):
        """Test that missing fields are skipped without error."""
        dt = datetime(2023, 10, 5, 12, 30, 45, tzinfo=timezone.utc)
        data = {"timestamp": dt}
        convert_datetime_fields_to_dict(data, ["timestamp", "missing_field"])
        
        assert isinstance(data["timestamp"], str)

    def test_skips_none_or_falsy_fields(self):
        """Test that None or falsy fields are skipped."""
        dt = datetime(2023, 10, 5, 12, 30, 45, tzinfo=timezone.utc)
        data = {"timestamp": dt, "optional": None, "empty": ""}
        convert_datetime_fields_to_dict(data, ["timestamp", "optional", "empty"])
        
        assert isinstance(data["timestamp"], str)
        assert data["optional"] is None
        assert data["empty"] == ""

    def test_empty_field_list(self):
        """Test with empty field list."""
        dt = datetime(2023, 10, 5, 12, 30, 45, tzinfo=timezone.utc)
        data = {"timestamp": dt}
        convert_datetime_fields_to_dict(data, [])
        
        assert isinstance(data["timestamp"], datetime)

    def test_modifies_dict_in_place(self):
        """Test that the function modifies dict in-place."""
        dt = datetime(2023, 10, 5, 12, 30, 45, tzinfo=timezone.utc)
        data = {"timestamp": dt}
        original_id = id(data)
        convert_datetime_fields_to_dict(data, ["timestamp"])
        
        assert id(data) == original_id


class TestConvertDecimalFieldsToDict:
    """Test in-place Decimal to string conversion in dict."""

    def test_converts_single_decimal_field(self):
        """Test conversion of single Decimal field to string."""
        data = {"price": Decimal("123.456"), "other": "value"}
        convert_decimal_fields_to_dict(data, ["price"])
        
        assert isinstance(data["price"], str)
        assert data["price"] == "123.456"
        assert data["other"] == "value"

    def test_converts_multiple_decimal_fields(self):
        """Test conversion of multiple Decimal fields."""
        data = {"price": Decimal("123.45"), "quantity": Decimal("10"), "other": "value"}
        convert_decimal_fields_to_dict(data, ["price", "quantity"])
        
        assert isinstance(data["price"], str)
        assert isinstance(data["quantity"], str)

    def test_skips_missing_fields(self):
        """Test that missing fields are skipped without error."""
        data = {"price": Decimal("123.456")}
        convert_decimal_fields_to_dict(data, ["price", "missing_field"])
        
        assert isinstance(data["price"], str)

    def test_skips_none_fields(self):
        """Test that None fields are skipped."""
        data = {"price": Decimal("123.456"), "optional": None}
        convert_decimal_fields_to_dict(data, ["price", "optional"])
        
        assert isinstance(data["price"], str)
        assert data["optional"] is None

    def test_converts_zero_decimal(self):
        """Test conversion of zero Decimal value."""
        data = {"price": Decimal("0")}
        convert_decimal_fields_to_dict(data, ["price"])
        
        assert data["price"] == "0"

    def test_empty_field_list(self):
        """Test with empty field list."""
        data = {"price": Decimal("123.456")}
        convert_decimal_fields_to_dict(data, [])
        
        assert isinstance(data["price"], Decimal)

    def test_modifies_dict_in_place(self):
        """Test that the function modifies dict in-place."""
        data = {"price": Decimal("123.456")}
        original_id = id(data)
        convert_decimal_fields_to_dict(data, ["price"])
        
        assert id(data) == original_id


class TestConvertNestedOrderData:
    """Test nested order data conversion."""

    def test_converts_execution_timestamp(self):
        """Test conversion of execution_timestamp field."""
        order_data = {
            "execution_timestamp": "2023-10-05T12:30:45+00:00",
            "quantity": "10",
            "price": "123.45",
        }
        result = convert_nested_order_data(order_data)
        
        assert isinstance(result["execution_timestamp"], datetime)
        assert isinstance(result["quantity"], Decimal)
        assert isinstance(result["price"], Decimal)

    def test_converts_all_decimal_fields(self):
        """Test conversion of all expected decimal fields."""
        order_data = {
            "quantity": "10",
            "filled_quantity": "10",
            "price": "123.45",
            "total_value": "1234.50",
            "commission": "1.50",
            "fees": "0.50",
        }
        result = convert_nested_order_data(order_data)
        
        assert isinstance(result["quantity"], Decimal)
        assert isinstance(result["filled_quantity"], Decimal)
        assert isinstance(result["price"], Decimal)
        assert isinstance(result["total_value"], Decimal)
        assert isinstance(result["commission"], Decimal)
        assert isinstance(result["fees"], Decimal)

    def test_handles_missing_optional_fields(self):
        """Test that missing optional fields don't cause errors."""
        order_data = {
            "quantity": "10",
            "price": "123.45",
        }
        result = convert_nested_order_data(order_data)
        
        assert isinstance(result["quantity"], Decimal)
        assert isinstance(result["price"], Decimal)

    def test_returns_same_dict_reference(self):
        """Test that the function returns the same dict reference."""
        order_data = {"quantity": "10"}
        result = convert_nested_order_data(order_data)
        
        assert result is order_data

    def test_skips_already_converted_timestamp(self):
        """Test that already converted timestamp is skipped."""
        dt = datetime(2023, 10, 5, 12, 30, 45, tzinfo=timezone.utc)
        order_data = {"execution_timestamp": dt, "quantity": "10"}
        result = convert_nested_order_data(order_data)
        
        assert result["execution_timestamp"] is dt
        assert isinstance(result["quantity"], Decimal)


class TestConvertNestedRebalanceItemData:
    """Test nested rebalance item data conversion."""

    def test_converts_all_decimal_fields(self):
        """Test conversion of all expected decimal fields."""
        item_data = {
            "current_weight": "0.5",
            "target_weight": "0.6",
            "weight_diff": "0.1",
            "target_value": "6000",
            "current_value": "5000",
            "trade_amount": "1000",
        }
        result = convert_nested_rebalance_item_data(item_data)
        
        assert isinstance(result["current_weight"], Decimal)
        assert isinstance(result["target_weight"], Decimal)
        assert isinstance(result["weight_diff"], Decimal)
        assert isinstance(result["target_value"], Decimal)
        assert isinstance(result["current_value"], Decimal)
        assert isinstance(result["trade_amount"], Decimal)

    def test_handles_missing_fields(self):
        """Test that missing fields don't cause errors."""
        item_data = {"current_weight": "0.5"}
        result = convert_nested_rebalance_item_data(item_data)
        
        assert isinstance(result["current_weight"], Decimal)

    def test_returns_same_dict_reference(self):
        """Test that the function returns the same dict reference."""
        item_data = {"current_weight": "0.5"}
        result = convert_nested_rebalance_item_data(item_data)
        
        assert result is item_data

    def test_handles_negative_trade_amount(self):
        """Test conversion of negative trade amount (sell)."""
        item_data = {"trade_amount": "-1000"}
        result = convert_nested_rebalance_item_data(item_data)
        
        assert result["trade_amount"] == Decimal("-1000")


class TestDataConversionEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_round_trip_datetime_conversion(self):
        """Test round-trip datetime conversion (to string and back)."""
        original_dt = datetime(2023, 10, 5, 12, 30, 45, tzinfo=timezone.utc)
        data = {"timestamp": original_dt}
        
        # Convert to string
        convert_datetime_fields_to_dict(data, ["timestamp"])
        timestamp_str = data["timestamp"]
        
        # Convert back to datetime
        data = {"timestamp": timestamp_str}
        convert_datetime_fields_from_dict(data, ["timestamp"])
        
        assert isinstance(data["timestamp"], datetime)
        assert data["timestamp"].year == original_dt.year
        assert data["timestamp"].month == original_dt.month
        assert data["timestamp"].day == original_dt.day

    def test_round_trip_decimal_conversion(self):
        """Test round-trip Decimal conversion (to string and back)."""
        original_value = Decimal("123.456")
        data = {"price": original_value}
        
        # Convert to string
        convert_decimal_fields_to_dict(data, ["price"])
        price_str = data["price"]
        
        # Convert back to Decimal
        data = {"price": price_str}
        convert_decimal_fields_from_dict(data, ["price"])
        
        assert data["price"] == original_value

    def test_complex_nested_structure(self):
        """Test conversion on complex nested structure."""
        data = {
            "order": {
                "execution_timestamp": "2023-10-05T12:30:45+00:00",
                "quantity": "10",
            },
            "metadata": {"created_at": "2023-10-05T10:00:00+00:00"},
        }
        
        # Convert nested order
        convert_nested_order_data(data["order"])
        
        assert isinstance(data["order"]["execution_timestamp"], datetime)
        assert isinstance(data["order"]["quantity"], Decimal)
