"""Business Unit: shared | Status: current.

Tests for DynamoDB trade ledger repository.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from the_alchemiser.shared.repositories.dynamodb_trade_ledger_repository import (
    DynamoDBTradeLedgerRepository,
)
from the_alchemiser.shared.schemas.trade_ledger import TradeLedgerEntry


class TestDynamoDBTradeLedgerRepository:
    """Test suite for DynamoDBTradeLedgerRepository."""

    @pytest.fixture
    def mock_dynamodb_table(self):
        """Create a mock DynamoDB table."""
        mock_table = MagicMock()
        mock_table.put_item = MagicMock()
        mock_table.get_item = MagicMock()
        mock_table.query = MagicMock()
        return mock_table

    @pytest.fixture
    def repository(self, mock_dynamodb_table):
        """Create repository instance with mocked DynamoDB."""
        # Create a mock that avoids actual boto3 import
        repo = MagicMock(spec=DynamoDBTradeLedgerRepository)
        repo._table = mock_dynamodb_table

        # Bind the actual methods to the mock
        repo.put_trade = DynamoDBTradeLedgerRepository.put_trade.__get__(repo)
        repo._write_strategy_links = DynamoDBTradeLedgerRepository._write_strategy_links.__get__(
            repo
        )
        repo.get_trade = DynamoDBTradeLedgerRepository.get_trade.__get__(repo)
        repo.query_trades_by_correlation = (
            DynamoDBTradeLedgerRepository.query_trades_by_correlation.__get__(repo)
        )
        repo.query_trades_by_symbol = DynamoDBTradeLedgerRepository.query_trades_by_symbol.__get__(
            repo
        )
        repo.query_trades_by_strategy = (
            DynamoDBTradeLedgerRepository.query_trades_by_strategy.__get__(repo)
        )
        repo._group_trades_by_symbol = (
            DynamoDBTradeLedgerRepository._group_trades_by_symbol.__get__(repo)
        )
        repo._match_trades_fifo = DynamoDBTradeLedgerRepository._match_trades_fifo.__get__(repo)
        repo._calculate_realized_pnl_fifo = (
            DynamoDBTradeLedgerRepository._calculate_realized_pnl_fifo.__get__(repo)
        )
        repo.compute_strategy_performance = (
            DynamoDBTradeLedgerRepository.compute_strategy_performance.__get__(repo)
        )

        return repo

    @pytest.fixture
    def sample_entry(self):
        """Create a sample trade ledger entry."""
        return TradeLedgerEntry(
            order_id="order-123",
            correlation_id="corr-456",
            symbol="AAPL",
            direction="BUY",
            filled_qty=Decimal("10"),
            fill_price=Decimal("150.25"),
            bid_at_fill=Decimal("150.24"),
            ask_at_fill=Decimal("150.26"),
            fill_timestamp=datetime(2025, 1, 15, 14, 30, 0, tzinfo=UTC),
            order_type="MARKET",
            strategy_names=["nuclear", "tecl"],
            strategy_weights={"nuclear": Decimal("0.6"), "tecl": Decimal("0.4")},
        )

    def test_put_trade_creates_main_item(self, repository, mock_dynamodb_table, sample_entry):
        """Test that put_trade creates the main trade item."""
        repository.put_trade(sample_entry, "ledger-123")

        # Verify put_item was called at least once (main item + strategy links)
        assert mock_dynamodb_table.put_item.call_count >= 1

        # Get the first call (main trade item)
        main_call = mock_dynamodb_table.put_item.call_args_list[0]
        item = main_call.kwargs["Item"]

        # Verify main trade item structure
        assert item["PK"] == "TRADE#order-123"
        assert item["SK"] == "METADATA"
        assert item["EntityType"] == "TRADE"
        assert item["order_id"] == "order-123"
        assert item["correlation_id"] == "corr-456"
        assert item["symbol"] == "AAPL"
        assert item["direction"] == "BUY"
        assert item["filled_qty"] == "10"
        assert item["fill_price"] == "150.25"
        assert item["order_type"] == "MARKET"

    def test_put_trade_creates_strategy_links(self, repository, mock_dynamodb_table, sample_entry):
        """Test that put_trade creates strategy link items."""
        repository.put_trade(sample_entry, "ledger-123")

        # Should have 3 calls: 1 main item + 2 strategy links
        assert mock_dynamodb_table.put_item.call_count == 3

        # Check strategy link items
        strategy_calls = mock_dynamodb_table.put_item.call_args_list[1:]

        strategy_names = set()
        for call in strategy_calls:
            item = call.kwargs["Item"]
            assert item["EntityType"] == "STRATEGY_TRADE"
            strategy_names.add(item["strategy_name"])

        assert strategy_names == {"nuclear", "tecl"}

    def test_put_trade_without_strategies(self, repository, mock_dynamodb_table):
        """Test put_trade with no strategy attribution."""
        entry = TradeLedgerEntry(
            order_id="order-999",
            correlation_id="corr-999",
            symbol="TSLA",
            direction="SELL",
            filled_qty=Decimal("5"),
            fill_price=Decimal("250.00"),
            fill_timestamp=datetime.now(UTC),
            order_type="MARKET",
        )

        repository.put_trade(entry, "ledger-999")

        # Should only have 1 call (main item, no strategy links)
        assert mock_dynamodb_table.put_item.call_count == 1

    def test_get_trade_success(self, repository, mock_dynamodb_table):
        """Test getting a trade by order_id."""
        mock_dynamodb_table.get_item.return_value = {
            "Item": {
                "PK": "TRADE#order-123",
                "SK": "METADATA",
                "order_id": "order-123",
                "symbol": "AAPL",
            }
        }

        result = repository.get_trade("order-123")

        assert result is not None
        assert result["order_id"] == "order-123"
        mock_dynamodb_table.get_item.assert_called_once()

    def test_get_trade_not_found(self, repository, mock_dynamodb_table):
        """Test getting a trade that doesn't exist."""
        mock_dynamodb_table.get_item.return_value = {}

        result = repository.get_trade("nonexistent")

        assert result is None

    def test_query_trades_by_correlation(self, repository, mock_dynamodb_table):
        """Test querying trades by correlation_id."""
        mock_dynamodb_table.query.return_value = {
            "Items": [
                {"order_id": "order-1", "symbol": "AAPL"},
                {"order_id": "order-2", "symbol": "TSLA"},
            ]
        }

        results = repository.query_trades_by_correlation("corr-123", limit=10)

        assert len(results) == 2
        assert results[0]["order_id"] == "order-1"
        mock_dynamodb_table.query.assert_called_once()

        # Verify query parameters
        call_kwargs = mock_dynamodb_table.query.call_args.kwargs
        assert call_kwargs["IndexName"] == "GSI1-CorrelationIndex"
        assert call_kwargs["Limit"] == 10

    def test_query_trades_by_symbol(self, repository, mock_dynamodb_table):
        """Test querying trades by symbol."""
        mock_dynamodb_table.query.return_value = {
            "Items": [{"order_id": "order-1", "symbol": "AAPL"}]
        }

        results = repository.query_trades_by_symbol("AAPL")

        assert len(results) == 1
        mock_dynamodb_table.query.assert_called_once()

        # Verify query parameters
        call_kwargs = mock_dynamodb_table.query.call_args.kwargs
        assert call_kwargs["IndexName"] == "GSI2-SymbolIndex"
        assert "SYMBOL#AAPL" in str(call_kwargs["ExpressionAttributeValues"])

    def test_query_trades_by_strategy(self, repository, mock_dynamodb_table):
        """Test querying trades by strategy name."""
        mock_dynamodb_table.query.return_value = {
            "Items": [
                {
                    "strategy_name": "nuclear",
                    "order_id": "order-1",
                    "direction": "BUY",
                    "strategy_trade_value": "1000.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-15T14:30:00Z",
                }
            ]
        }

        results = repository.query_trades_by_strategy("nuclear", limit=5)

        assert len(results) == 1
        assert results[0]["strategy_name"] == "nuclear"
        mock_dynamodb_table.query.assert_called_once()

        # Verify query parameters
        call_kwargs = mock_dynamodb_table.query.call_args.kwargs
        assert call_kwargs["Limit"] == 5

    def test_compute_strategy_performance(self, repository, mock_dynamodb_table):
        """Test computing strategy performance metrics."""
        mock_dynamodb_table.query.return_value = {
            "Items": [
                {
                    "direction": "BUY",
                    "strategy_trade_value": "1000.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-15T14:30:00Z",
                },
                {
                    "direction": "BUY",
                    "strategy_trade_value": "500.00",
                    "symbol": "TSLA",
                    "fill_timestamp": "2025-01-16T10:00:00Z",
                },
                {
                    "direction": "SELL",
                    "strategy_trade_value": "800.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-17T15:00:00Z",
                },
            ]
        }

        performance = repository.compute_strategy_performance("nuclear")

        assert performance["strategy_name"] == "nuclear"
        assert performance["total_trades"] == 3
        assert performance["buy_trades"] == 2
        assert performance["sell_trades"] == 1
        assert performance["total_buy_value"] == Decimal("1500.00")
        assert performance["total_sell_value"] == Decimal("800.00")
        assert performance["gross_pnl"] == Decimal("-700.00")
        assert set(performance["symbols_traded"]) == {"AAPL", "TSLA"}

    def test_compute_strategy_performance_no_trades(self, repository, mock_dynamodb_table):
        """Test computing performance for strategy with no trades."""
        mock_dynamodb_table.query.return_value = {"Items": []}

        performance = repository.compute_strategy_performance("nonexistent")

        assert performance["strategy_name"] == "nonexistent"
        assert performance["total_trades"] == 0
        assert performance["total_buy_value"] == Decimal("0")
        assert performance["symbols_traded"] == []

    def test_query_error_handling(self, repository, mock_dynamodb_table):
        """Test that query errors are handled gracefully."""
        mock_dynamodb_table.query.side_effect = Exception("DynamoDB error")

        results = repository.query_trades_by_correlation("corr-123")

        assert results == []

    def test_realized_pnl_single_matched_pair(self, repository, mock_dynamodb_table):
        """Test realized P&L calculation with a single matched buy-sell pair."""
        mock_dynamodb_table.query.return_value = {
            "Items": [
                {
                    "direction": "BUY",
                    "strategy_trade_value": "1000.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-15T14:30:00Z",
                },
                {
                    "direction": "SELL",
                    "strategy_trade_value": "1200.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-16T10:00:00Z",
                },
            ]
        }

        performance = repository.compute_strategy_performance("nuclear")

        # Realized P&L should be sell value - buy value
        assert performance["realized_pnl"] == Decimal("200.00")
        assert performance["gross_pnl"] == Decimal("200.00")
        assert performance["total_trades"] == 2

    def test_realized_pnl_multiple_matched_pairs(self, repository, mock_dynamodb_table):
        """Test realized P&L calculation with multiple matched pairs."""
        mock_dynamodb_table.query.return_value = {
            "Items": [
                {
                    "direction": "BUY",
                    "strategy_trade_value": "1000.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-15T14:30:00Z",
                },
                {
                    "direction": "BUY",
                    "strategy_trade_value": "1500.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-16T09:00:00Z",
                },
                {
                    "direction": "SELL",
                    "strategy_trade_value": "1200.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-16T10:00:00Z",
                },
                {
                    "direction": "SELL",
                    "strategy_trade_value": "1800.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-17T15:00:00Z",
                },
            ]
        }

        performance = repository.compute_strategy_performance("nuclear")

        # First pair: 1200 - 1000 = 200
        # Second pair: 1800 - 1500 = 300
        # Total realized P&L: 500
        assert performance["realized_pnl"] == Decimal("500.00")
        assert performance["gross_pnl"] == Decimal("500.00")

    def test_realized_pnl_unmatched_trades(self, repository, mock_dynamodb_table):
        """Test realized P&L with unmatched trades (open positions)."""
        mock_dynamodb_table.query.return_value = {
            "Items": [
                {
                    "direction": "BUY",
                    "strategy_trade_value": "1000.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-15T14:30:00Z",
                },
                {
                    "direction": "BUY",
                    "strategy_trade_value": "1500.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-16T09:00:00Z",
                },
                {
                    "direction": "SELL",
                    "strategy_trade_value": "1200.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-16T10:00:00Z",
                },
            ]
        }

        performance = repository.compute_strategy_performance("nuclear")

        # Only one matched pair: 1200 - 1000 = 200
        # Second buy (1500) remains unmatched (open position)
        assert performance["realized_pnl"] == Decimal("200.00")
        # Gross P&L includes all trades: (1200) - (1000 + 1500) = -1300
        assert performance["gross_pnl"] == Decimal("-1300.00")

    def test_realized_pnl_multiple_symbols(self, repository, mock_dynamodb_table):
        """Test realized P&L calculation with trades across multiple symbols."""
        mock_dynamodb_table.query.return_value = {
            "Items": [
                {
                    "direction": "BUY",
                    "strategy_trade_value": "1000.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-15T14:30:00Z",
                },
                {
                    "direction": "SELL",
                    "strategy_trade_value": "1100.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-16T10:00:00Z",
                },
                {
                    "direction": "BUY",
                    "strategy_trade_value": "2000.00",
                    "symbol": "TSLA",
                    "fill_timestamp": "2025-01-15T15:00:00Z",
                },
                {
                    "direction": "SELL",
                    "strategy_trade_value": "1900.00",
                    "symbol": "TSLA",
                    "fill_timestamp": "2025-01-16T11:00:00Z",
                },
            ]
        }

        performance = repository.compute_strategy_performance("nuclear")

        # AAPL: 1100 - 1000 = 100
        # TSLA: 1900 - 2000 = -100
        # Total realized P&L: 0
        assert performance["realized_pnl"] == Decimal("0.00")

    def test_realized_pnl_fifo_ordering(self, repository, mock_dynamodb_table):
        """Test that FIFO ordering is correctly applied for matched pairs."""
        mock_dynamodb_table.query.return_value = {
            "Items": [
                {
                    "direction": "BUY",
                    "strategy_trade_value": "1000.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-15T14:30:00Z",
                },
                {
                    "direction": "BUY",
                    "strategy_trade_value": "1200.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-16T09:00:00Z",
                },
                {
                    "direction": "SELL",
                    "strategy_trade_value": "1150.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-17T15:00:00Z",
                },
            ]
        }

        performance = repository.compute_strategy_performance("nuclear")

        # FIFO: First sell should match against first buy
        # 1150 - 1000 = 150 (not 1150 - 1200 = -50)
        assert performance["realized_pnl"] == Decimal("150.00")

    def test_realized_pnl_loss_scenario(self, repository, mock_dynamodb_table):
        """Test realized P&L calculation with a loss scenario."""
        mock_dynamodb_table.query.return_value = {
            "Items": [
                {
                    "direction": "BUY",
                    "strategy_trade_value": "2000.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-15T14:30:00Z",
                },
                {
                    "direction": "SELL",
                    "strategy_trade_value": "1500.00",
                    "symbol": "AAPL",
                    "fill_timestamp": "2025-01-16T10:00:00Z",
                },
            ]
        }

        performance = repository.compute_strategy_performance("nuclear")

        # Realized loss: 1500 - 2000 = -500
        assert performance["realized_pnl"] == Decimal("-500.00")
        assert performance["gross_pnl"] == Decimal("-500.00")
