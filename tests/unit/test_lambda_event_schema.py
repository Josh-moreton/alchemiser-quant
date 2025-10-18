#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Comprehensive tests for LambdaEvent schema validation.

Tests cover:
- Field type validation (Literal types)
- Format validation (regex patterns)
- Range validation (positive integers)
- Email validation
- Cross-field validation (model validators)
- Immutability enforcement
- Extra field rejection
- Backward compatibility (deprecation warnings)
"""

from __future__ import annotations

import warnings

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas import LambdaEvent


class TestLambdaEventBasicValidation:
    """Test basic LambdaEvent field validation."""

    @pytest.mark.unit
    def test_valid_trade_event(self) -> None:
        """Test valid trade event."""
        event = LambdaEvent(mode="trade", trading_mode="paper")
        assert event.mode == "trade"
        assert event.trading_mode == "paper"
        assert event.schema_version == "1.0"

    @pytest.mark.unit
    def test_valid_bot_event(self) -> None:
        """Test valid bot event."""
        event = LambdaEvent(mode="bot")
        assert event.mode == "bot"
        assert event.trading_mode is None
        assert event.schema_version == "1.0"

    @pytest.mark.unit
    def test_valid_pnl_weekly_event(self) -> None:
        """Test valid P&L weekly event."""
        event = LambdaEvent(action="pnl_analysis", pnl_type="weekly")
        assert event.action == "pnl_analysis"
        assert event.pnl_type == "weekly"

    @pytest.mark.unit
    def test_valid_pnl_monthly_event(self) -> None:
        """Test valid P&L monthly event."""
        event = LambdaEvent(action="pnl_analysis", pnl_type="monthly")
        assert event.action == "pnl_analysis"
        assert event.pnl_type == "monthly"

    @pytest.mark.unit
    def test_valid_pnl_with_period(self) -> None:
        """Test valid P&L with period."""
        event = LambdaEvent(action="pnl_analysis", pnl_period="3M")
        assert event.action == "pnl_analysis"
        assert event.pnl_period == "3M"

    @pytest.mark.unit
    def test_empty_event_with_defaults(self) -> None:
        """Test empty event with all defaults."""
        event = LambdaEvent()
        assert event.mode is None
        assert event.trading_mode is None
        assert event.action is None
        assert event.schema_version == "1.0"


class TestLambdaEventLiteralTypeValidation:
    """Test Literal type validation for enum fields."""

    @pytest.mark.unit
    def test_invalid_mode_rejected(self) -> None:
        """Test invalid mode is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LambdaEvent(mode="invalid_mode")
        assert "mode" in str(exc_info.value)

    @pytest.mark.unit
    def test_invalid_trading_mode_rejected(self) -> None:
        """Test invalid trading_mode is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LambdaEvent(mode="trade", trading_mode="invalid")
        assert "trading_mode" in str(exc_info.value)

    @pytest.mark.unit
    def test_invalid_action_rejected(self) -> None:
        """Test invalid action is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LambdaEvent(action="invalid_action")
        assert "action" in str(exc_info.value)

    @pytest.mark.unit
    def test_monthly_summary_action_rejected(self) -> None:
        """Test deprecated monthly_summary action is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LambdaEvent(action="monthly_summary")
        assert "action" in str(exc_info.value)

    @pytest.mark.unit
    def test_invalid_pnl_type_rejected(self) -> None:
        """Test invalid pnl_type is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LambdaEvent(action="pnl_analysis", pnl_type="invalid")
        assert "pnl_type" in str(exc_info.value)

    @pytest.mark.unit
    def test_valid_mode_values(self) -> None:
        """Test all valid mode values are accepted."""
        for mode in ["trade", "bot"]:
            event = LambdaEvent(mode=mode)
            assert event.mode == mode

    @pytest.mark.unit
    def test_valid_trading_mode_values(self) -> None:
        """Test all valid trading_mode values are accepted."""
        for trading_mode in ["paper", "live"]:
            event = LambdaEvent(mode="trade", trading_mode=trading_mode)
            assert event.trading_mode == trading_mode

    @pytest.mark.unit
    def test_valid_pnl_type_values(self) -> None:
        """Test all valid pnl_type values are accepted."""
        for pnl_type in ["weekly", "monthly"]:
            event = LambdaEvent(action="pnl_analysis", pnl_type=pnl_type)
            assert event.pnl_type == pnl_type


class TestLambdaEventFormatValidation:
    """Test format validation for pattern-constrained fields."""

    @pytest.mark.unit
    def test_valid_month_format(self) -> None:
        """Test valid month format is accepted."""
        event = LambdaEvent(month="2024-01")
        assert event.month == "2024-01"

    @pytest.mark.unit
    def test_invalid_month_format_rejected(self) -> None:
        """Test invalid month format is rejected."""
        invalid_months = [
            "2024-13",  # Invalid month
            "24-01",  # Invalid year format
            "2024-1",  # Missing leading zero
            "2024/01",  # Wrong separator
            "202401",  # Missing separator
        ]
        for invalid_month in invalid_months:
            with pytest.raises(ValidationError) as exc_info:
                LambdaEvent(month=invalid_month)
            assert "month" in str(exc_info.value).lower()

    @pytest.mark.unit
    def test_valid_pnl_period_formats(self) -> None:
        """Test valid pnl_period formats are accepted."""
        valid_periods = ["1W", "1M", "3M", "1A", "12W", "52W"]
        for period in valid_periods:
            event = LambdaEvent(action="pnl_analysis", pnl_period=period)
            assert event.pnl_period == period

    @pytest.mark.unit
    def test_invalid_pnl_period_format_rejected(self) -> None:
        """Test invalid pnl_period format is rejected."""
        invalid_periods = [
            "3X",  # Invalid unit
            "W3",  # Wrong order
            "3m",  # Lowercase unit
            "3.5M",  # Decimal not supported
            "M",  # Missing number
        ]
        for invalid_period in invalid_periods:
            with pytest.raises(ValidationError) as exc_info:
                LambdaEvent(action="pnl_analysis", pnl_period=invalid_period)
            assert "pnl_period" in str(exc_info.value).lower()


class TestLambdaEventRangeValidation:
    """Test range validation for numeric fields."""

    @pytest.mark.unit
    def test_valid_pnl_periods(self) -> None:
        """Test valid pnl_periods values are accepted."""
        for periods in [1, 3, 5, 10, 52]:
            event = LambdaEvent(action="pnl_analysis", pnl_type="weekly", pnl_periods=periods)
            assert event.pnl_periods == periods

    @pytest.mark.unit
    def test_zero_pnl_periods_rejected(self) -> None:
        """Test zero pnl_periods is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LambdaEvent(action="pnl_analysis", pnl_type="weekly", pnl_periods=0)
        assert "pnl_periods" in str(exc_info.value).lower()

    @pytest.mark.unit
    def test_negative_pnl_periods_rejected(self) -> None:
        """Test negative pnl_periods is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LambdaEvent(action="pnl_analysis", pnl_type="weekly", pnl_periods=-1)
        assert "pnl_periods" in str(exc_info.value).lower()


class TestLambdaEventEmailValidation:
    """Test email field validation."""

    @pytest.mark.unit
    def test_valid_email_accepted(self) -> None:
        """Test valid email is accepted."""
        valid_emails = [
            "user@example.com",
            "test.user@example.co.uk",
            "admin+test@domain.io",
        ]
        for email in valid_emails:
            event = LambdaEvent(to=email)
            assert event.to == email

    @pytest.mark.unit
    def test_invalid_email_not_validated(self) -> None:
        """Test that invalid email is not validated at schema level.

        Note: Email validation is intentionally NOT enforced in LambdaEvent schema.
        Validation happens at the notification service level where it's actually used.
        This design choice keeps the Lambda event schema lightweight and flexible.
        """
        # These should all be accepted (no validation at schema level)
        test_emails = [
            "not_an_email",
            "@example.com",
            "user@",
            "user@.com",
            "user space@example.com",
        ]
        for email in test_emails:
            event = LambdaEvent(to=email)
            assert event.to == email  # Accepts anything


class TestLambdaEventModelValidator:
    """Test model validator for cross-field validation."""

    @pytest.mark.unit
    def test_pnl_analysis_with_pnl_type_valid(self) -> None:
        """Test pnl_analysis with pnl_type is valid."""
        event = LambdaEvent(action="pnl_analysis", pnl_type="weekly")
        assert event.action == "pnl_analysis"
        assert event.pnl_type == "weekly"

    @pytest.mark.unit
    def test_pnl_analysis_with_pnl_period_valid(self) -> None:
        """Test pnl_analysis with pnl_period is valid."""
        event = LambdaEvent(action="pnl_analysis", pnl_period="3M")
        assert event.action == "pnl_analysis"
        assert event.pnl_period == "3M"

    @pytest.mark.unit
    def test_pnl_analysis_with_both_valid(self) -> None:
        """Test pnl_analysis with both pnl_type and pnl_period is valid."""
        event = LambdaEvent(action="pnl_analysis", pnl_type="weekly", pnl_period="3M")
        assert event.action == "pnl_analysis"
        assert event.pnl_type == "weekly"
        assert event.pnl_period == "3M"

    @pytest.mark.unit
    def test_pnl_analysis_without_type_or_period_rejected(self) -> None:
        """Test pnl_analysis without pnl_type or pnl_period is rejected."""
        with pytest.raises(ValueError) as exc_info:
            LambdaEvent(action="pnl_analysis")
        assert "pnl_type" in str(exc_info.value).lower()
        assert "pnl_period" in str(exc_info.value).lower()


class TestLambdaEventImmutability:
    """Test LambdaEvent immutability."""

    @pytest.mark.unit
    def test_frozen_model(self) -> None:
        """Test LambdaEvent is immutable (frozen)."""
        event = LambdaEvent(mode="trade")
        with pytest.raises(ValidationError):
            event.mode = "bot"  # type: ignore

    @pytest.mark.unit
    def test_cannot_add_attributes(self) -> None:
        """Test cannot add new attributes to frozen model."""
        event = LambdaEvent()
        with pytest.raises(ValidationError):
            event.new_field = "value"  # type: ignore


class TestLambdaEventExtraFieldsRejection:
    """Test extra="forbid" configuration."""

    @pytest.mark.unit
    def test_extra_fields_rejected(self) -> None:
        """Test extra fields are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LambdaEvent(mode="trade", unknown_field="value")
        assert "unknown_field" in str(exc_info.value).lower()

    @pytest.mark.unit
    def test_typo_in_field_name_rejected(self) -> None:
        """Test typo in field name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LambdaEvent(mod="trade")  # Typo: mod instead of mode
        assert "mod" in str(exc_info.value).lower()


class TestLambdaEventObservabilityFields:
    """Test observability fields for event tracing."""

    @pytest.mark.unit
    def test_correlation_id_field(self) -> None:
        """Test correlation_id field."""
        event = LambdaEvent(correlation_id="corr-123")
        assert event.correlation_id == "corr-123"

    @pytest.mark.unit
    def test_causation_id_field(self) -> None:
        """Test causation_id field."""
        event = LambdaEvent(causation_id="cause-456")
        assert event.causation_id == "cause-456"

    @pytest.mark.unit
    def test_both_tracing_fields(self) -> None:
        """Test both correlation_id and causation_id."""
        event = LambdaEvent(mode="trade", correlation_id="corr-123", causation_id="cause-456")
        assert event.correlation_id == "corr-123"
        assert event.causation_id == "cause-456"


class TestLambdaEventBackwardCompatibility:
    """Test backward compatibility features."""

    @pytest.mark.unit
    def test_deprecated_alias_emits_warning(self) -> None:
        """Test LambdaEventDTO alias emits deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from the_alchemiser.shared.schemas.lambda_event import LambdaEventDTO

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "LambdaEventDTO is deprecated" in str(w[0].message)
            assert "use LambdaEvent instead" in str(w[0].message)
            assert "3.0.0" in str(w[0].message)

            # Verify the alias still works
            assert LambdaEventDTO is LambdaEvent

    @pytest.mark.unit
    def test_schema_version_default(self) -> None:
        """Test schema_version defaults to 1.0."""
        event = LambdaEvent()
        assert event.schema_version == "1.0"

    @pytest.mark.unit
    def test_cannot_override_schema_version(self) -> None:
        """Test schema_version cannot be overridden."""
        with pytest.raises(ValidationError) as exc_info:
            LambdaEvent(schema_version="2.0")
        assert "schema_version" in str(exc_info.value).lower()


class TestLambdaEventComplexScenarios:
    """Test complex real-world scenarios."""

    @pytest.mark.unit
    def test_full_trade_event(self) -> None:
        """Test fully populated trade event."""
        event = LambdaEvent(
            mode="trade",
            trading_mode="paper",
            arguments=["--force", "--verbose"],
            correlation_id="corr-123",
            causation_id="cause-456",
        )
        assert event.mode == "trade"
        assert event.trading_mode == "paper"
        assert event.arguments == ["--force", "--verbose"]
        assert event.correlation_id == "corr-123"
        assert event.causation_id == "cause-456"

    @pytest.mark.unit
    def test_full_pnl_event(self) -> None:
        """Test fully populated P&L event."""
        event = LambdaEvent(
            action="pnl_analysis",
            pnl_type="weekly",
            pnl_periods=3,
            pnl_detailed=True,
            to="admin@example.com",
            subject="Weekly P&L Report",
            dry_run=False,
            correlation_id="corr-789",
        )
        assert event.action == "pnl_analysis"
        assert event.pnl_type == "weekly"
        assert event.pnl_periods == 3
        assert event.pnl_detailed is True
        assert event.to == "admin@example.com"
        assert event.subject == "Weekly P&L Report"
        assert event.dry_run is False
        assert event.correlation_id == "corr-789"

    @pytest.mark.unit
    def test_dict_serialization(self) -> None:
        """Test event can be serialized to dict."""
        event = LambdaEvent(mode="trade", trading_mode="paper")
        event_dict = event.model_dump()
        assert event_dict["mode"] == "trade"
        assert event_dict["trading_mode"] == "paper"
        assert event_dict["schema_version"] == "1.0"

    @pytest.mark.unit
    def test_json_serialization(self) -> None:
        """Test event can be serialized to JSON."""
        event = LambdaEvent(mode="trade", trading_mode="paper")
        event_json = event.model_dump_json()
        assert '"mode":"trade"' in event_json
        assert '"trading_mode":"paper"' in event_json
        assert '"schema_version":"1.0"' in event_json
