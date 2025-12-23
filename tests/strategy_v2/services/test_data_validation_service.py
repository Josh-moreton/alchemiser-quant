"""Business Unit: strategy_v2 | Status: current.

Tests for data validation service.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.data_v2.data_freshness_validator import DataFreshnessValidator
from the_alchemiser.data_v2.market_data_store import SymbolMetadata
from the_alchemiser.shared.errors.exceptions import DataProviderError
from the_alchemiser.strategy_v2.services.data_validation_service import (
    DataValidationService,
)


class TestDataValidationService:
    """Test suite for DataValidationService."""

    @pytest.fixture
    def mock_market_data_store(self) -> Mock:
        """Create mock market data store."""
        store = Mock()
        yesterday = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
        store.get_metadata.return_value = SymbolMetadata(
            symbol="AAPL",
            last_bar_date=yesterday,
            row_count=1000,
            updated_at=datetime.now(UTC).isoformat(),
        )
        return store

    @pytest.fixture
    def mock_lambda_client(self) -> Mock:
        """Create mock Lambda client."""
        client = Mock()
        success_response = {
            "statusCode": 200,
            "body": {"status": "success", "symbol": "AAPL", "bars_fetched": 1},
        }
        client.invoke.return_value = {
            "Payload": Mock(read=Mock(return_value=json.dumps(success_response)))
        }
        return client

    @pytest.fixture
    def validation_service(
        self, mock_market_data_store: Mock, mock_lambda_client: Mock
    ) -> DataValidationService:
        """Create data validation service with mocked dependencies."""
        validator = DataFreshnessValidator(
            market_data_store=mock_market_data_store, max_staleness_days=2
        )
        service = DataValidationService(
            validator=validator,
            market_data_store=mock_market_data_store,
            data_lambda_name="test-data-lambda",
        )
        service.lambda_client = mock_lambda_client
        return service

    def test_validation_passes_with_fresh_data(
        self,
        validation_service: DataValidationService,
        mock_lambda_client: Mock,
    ) -> None:
        """Test that validation passes when data is fresh."""
        with patch(
            "the_alchemiser.strategy_v2.services.data_validation_service.extract_symbols_from_file",
            return_value={"AAPL"},
        ):
            validation_service.validate_and_refresh_if_needed(
                "test-strategy.clj", "test-correlation-id"
            )

        mock_lambda_client.invoke.assert_not_called()

    def test_validation_detects_stale_data_and_refreshes(
        self,
        validation_service: DataValidationService,
        mock_market_data_store: Mock,
        mock_lambda_client: Mock,
    ) -> None:
        """Test that stale data is detected and refresh is triggered."""
        five_days_ago = (datetime.now(UTC) - timedelta(days=5)).strftime("%Y-%m-%d")
        yesterday = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")

        mock_market_data_store.get_metadata.side_effect = [
            SymbolMetadata(
                symbol="AAPL",
                last_bar_date=five_days_ago,
                row_count=1000,
                updated_at=datetime.now(UTC).isoformat(),
            ),
            SymbolMetadata(
                symbol="AAPL",
                last_bar_date=yesterday,
                row_count=1001,
                updated_at=datetime.now(UTC).isoformat(),
            ),
        ]

        with patch(
            "the_alchemiser.strategy_v2.services.data_validation_service.extract_symbols_from_file",
            return_value={"AAPL"},
        ):
            validation_service.validate_and_refresh_if_needed(
                "test-strategy.clj", "test-correlation-id"
            )

        mock_lambda_client.invoke.assert_called_once()
        call_args = mock_lambda_client.invoke.call_args
        assert call_args[1]["FunctionName"] == "test-data-lambda"
        assert call_args[1]["InvocationType"] == "RequestResponse"

        payload = json.loads(call_args[1]["Payload"])
        assert payload["symbols"] == ["AAPL"]
        assert payload["full_seed"] is False

    def test_validation_fails_when_refresh_unsuccessful(
        self,
        validation_service: DataValidationService,
        mock_market_data_store: Mock,
        mock_lambda_client: Mock,
    ) -> None:
        """Test that validation fails if data is still stale after refresh."""
        five_days_ago = (datetime.now(UTC) - timedelta(days=5)).strftime("%Y-%m-%d")
        mock_market_data_store.get_metadata.return_value = SymbolMetadata(
            symbol="AAPL",
            last_bar_date=five_days_ago,
            row_count=1000,
            updated_at=datetime.now(UTC).isoformat(),
        )

        with patch(
            "the_alchemiser.strategy_v2.services.data_validation_service.extract_symbols_from_file",
            return_value={"AAPL"},
        ):
            with pytest.raises(
                DataProviderError, match="Data validation failed after refresh"
            ):
                validation_service.validate_and_refresh_if_needed(
                    "test-strategy.clj", "test-correlation-id"
                )

        mock_lambda_client.invoke.assert_called_once()
