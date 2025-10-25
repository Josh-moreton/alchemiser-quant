"""Business Unit: shared | Status: current.

Tests for error context data module.
"""

from the_alchemiser.shared.errors.context import ErrorContextData


class TestErrorContextData:
    """Test ErrorContextData dataclass."""

    def test_create_empty_context(self):
        """Test creating ErrorContextData with no fields."""
        context = ErrorContextData()
        assert context.module is None
        assert context.function is None
        assert context.operation is None
        assert context.correlation_id is None
        assert context.additional_data == {}  # Pydantic default_factory returns empty dict

    def test_create_context_with_all_fields(self):
        """Test creating ErrorContextData with all fields populated."""
        context = ErrorContextData(
            module="test_module",
            function="test_function",
            operation="test_operation",
            correlation_id="test-correlation-123",
            additional_data={"key": "value", "count": 42},
        )
        assert context.module == "test_module"
        assert context.function == "test_function"
        assert context.operation == "test_operation"
        assert context.correlation_id == "test-correlation-123"
        assert context.additional_data == {"key": "value", "count": 42}

    def test_create_context_with_partial_fields(self):
        """Test creating ErrorContextData with only some fields."""
        context = ErrorContextData(
            module="strategy_v2",
            correlation_id="corr-456",
        )
        assert context.module == "strategy_v2"
        assert context.function is None
        assert context.operation is None
        assert context.correlation_id == "corr-456"
        assert context.additional_data == {}  # Pydantic default_factory returns empty dict

    def test_correlation_id_preservation(self):
        """Test that correlation_id is preserved correctly."""
        correlation_id = "abc-123-def-456"
        context = ErrorContextData(correlation_id=correlation_id)
        assert context.correlation_id == correlation_id

    def test_causation_id_in_additional_data(self):
        """Test that causation_id can be stored in additional_data."""
        context = ErrorContextData(
            correlation_id="corr-123",
            additional_data={"causation_id": "cause-456"},
        )
        assert context.correlation_id == "corr-123"
        assert context.additional_data["causation_id"] == "cause-456"


class TestErrorContextDataToDict:
    """Test ErrorContextData.to_dict() method."""

    def test_to_dict_with_empty_context(self):
        """Test to_dict() with empty context."""
        context = ErrorContextData()
        result = context.to_dict()
        assert isinstance(result, dict)
        # exclude_none=True means None values are omitted
        assert "module" not in result
        assert "function" not in result
        assert "operation" not in result
        assert "correlation_id" not in result
        # But empty dict is included
        assert result["additional_data"] == {}
        # Timestamp is always present
        assert "timestamp" in result

    def test_to_dict_with_all_fields(self):
        """Test to_dict() with all fields populated."""
        context = ErrorContextData(
            module="portfolio_v2",
            function="calculate_positions",
            operation="rebalance",
            correlation_id="corr-789",
            additional_data={"symbol": "AAPL", "quantity": 10},
        )
        result = context.to_dict()
        assert result["module"] == "portfolio_v2"
        assert result["function"] == "calculate_positions"
        assert result["operation"] == "rebalance"
        assert result["correlation_id"] == "corr-789"
        assert result["additional_data"] == {"symbol": "AAPL", "quantity": 10}

    def test_to_dict_preserves_correlation_id(self):
        """Test that to_dict() preserves correlation_id."""
        correlation_id = "test-corr-999"
        context = ErrorContextData(correlation_id=correlation_id)
        result = context.to_dict()
        assert result["correlation_id"] == correlation_id

    def test_to_dict_handles_none_additional_data(self):
        """Test that to_dict() converts None additional_data to empty dict."""
        context = ErrorContextData(module="test")
        result = context.to_dict()
        assert result["additional_data"] == {}
        assert isinstance(result["additional_data"], dict)

    def test_to_dict_preserves_additional_data(self):
        """Test that to_dict() preserves all additional_data."""
        additional = {
            "causation_id": "cause-123",
            "user_id": "user-456",
            "session_id": "session-789",
            "metadata": {"nested": "value"},
        }
        context = ErrorContextData(additional_data=additional)
        result = context.to_dict()
        assert result["additional_data"] == additional

    def test_to_dict_with_complex_additional_data(self):
        """Test to_dict() with complex nested additional_data."""
        context = ErrorContextData(
            module="execution_v2",
            additional_data={
                "order_id": "order-123",
                "details": {
                    "symbol": "TSLA",
                    "side": "buy",
                    "quantity": 100,
                },
                "timestamps": ["2024-01-01T10:00:00Z", "2024-01-01T10:05:00Z"],
            },
        )
        result = context.to_dict()
        assert result["additional_data"]["order_id"] == "order-123"
        assert result["additional_data"]["details"]["symbol"] == "TSLA"
        assert len(result["additional_data"]["timestamps"]) == 2


class TestErrorContextDataSerialization:
    """Test ErrorContextData serialization scenarios."""

    def test_context_can_be_serialized_to_json(self):
        """Test that context dict can be serialized (e.g., for logging)."""
        import json

        context = ErrorContextData(
            module="test_module",
            function="test_function",
            correlation_id="corr-123",
            additional_data={"key": "value", "number": 42},
        )
        result = context.to_dict()
        # Should be JSON-serializable
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
        # Should be deserializable
        deserialized = json.loads(json_str)
        assert deserialized["module"] == "test_module"
        assert deserialized["correlation_id"] == "corr-123"

    def test_context_with_event_metadata(self):
        """Test context with event-related metadata (correlation and causation)."""
        context = ErrorContextData(
            module="orchestration",
            operation="handle_signal_generated",
            correlation_id="evt-corr-123",
            additional_data={
                "causation_id": "evt-cause-456",
                "event_id": "evt-789",
                "schema_version": "1.0",
            },
        )
        result = context.to_dict()
        assert result["correlation_id"] == "evt-corr-123"
        assert result["additional_data"]["causation_id"] == "evt-cause-456"
        assert result["additional_data"]["event_id"] == "evt-789"
