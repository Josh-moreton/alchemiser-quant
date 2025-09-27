#!/usr/bin/env python3
"""Tests for account value logging functionality."""

import tempfile
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from the_alchemiser.shared.persistence.local_account_value_logger import LocalAccountValueLogger
from the_alchemiser.shared.schemas.account_value_logger import AccountValueEntry, AccountValueQuery
from the_alchemiser.shared.services.account_value_logging_service import AccountValueLoggingService
from the_alchemiser.shared.types.account import AccountModel


class TestLocalAccountValueLogger:
    """Test cases for LocalAccountValueLogger."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def logger(self, temp_dir):
        """Create logger instance with temporary directory."""
        return LocalAccountValueLogger(base_path=temp_dir)

    @pytest.fixture
    def sample_entry(self):
        """Create sample account value entry."""
        return AccountValueEntry(
            entry_id="test-entry-1",
            account_id="test-account",
            portfolio_value=Decimal("10000.00"),
            cash=Decimal("2000.00"),
            equity=Decimal("8000.00"),
            timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            source="test",
        )

    def test_log_and_query_single_entry(self, logger, sample_entry):
        """Test logging and querying a single entry."""
        # Log entry
        logger.log_account_value(sample_entry)
        
        # Query all entries
        filters = AccountValueQuery()
        entries = list(logger.query_account_values(filters))
        
        assert len(entries) == 1
        assert entries[0].entry_id == sample_entry.entry_id
        assert entries[0].portfolio_value == sample_entry.portfolio_value

    def test_log_multiple_entries_same_date(self, logger):
        """Test logging multiple entries for same date (should update)."""
        # First entry
        entry1 = AccountValueEntry(
            entry_id="test-1",
            account_id="test-account",
            portfolio_value=Decimal("10000.00"),
            cash=Decimal("2000.00"),
            equity=Decimal("8000.00"),
            timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            source="test",
        )
        
        # Second entry same date, different value
        entry2 = AccountValueEntry(
            entry_id="test-2",
            account_id="test-account",
            portfolio_value=Decimal("11000.00"),
            cash=Decimal("2500.00"),
            equity=Decimal("8500.00"),
            timestamp=datetime(2024, 1, 15, 15, 0, 0, tzinfo=UTC),
            source="test",
        )
        
        logger.log_account_value(entry1)
        logger.log_account_value(entry2)
        
        # Should only have one entry (the updated one)
        filters = AccountValueQuery(account_id="test-account")
        entries = list(logger.query_account_values(filters))
        
        assert len(entries) == 1
        assert entries[0].portfolio_value == Decimal("11000.00")

    def test_query_with_date_filters(self, logger):
        """Test querying with date filters."""
        # Create entries for different dates
        entry1 = AccountValueEntry(
            entry_id="test-1",
            account_id="test-account",
            portfolio_value=Decimal("10000.00"),
            cash=Decimal("2000.00"),
            equity=Decimal("8000.00"),
            timestamp=datetime(2024, 1, 10, 10, 0, 0, tzinfo=UTC),
            source="test",
        )
        
        entry2 = AccountValueEntry(
            entry_id="test-2",
            account_id="test-account",
            portfolio_value=Decimal("11000.00"),
            cash=Decimal("2500.00"),
            equity=Decimal("8500.00"),
            timestamp=datetime(2024, 1, 20, 10, 0, 0, tzinfo=UTC),
            source="test",
        )
        
        logger.log_account_value(entry1)
        logger.log_account_value(entry2)
        
        # Query with date filter
        filters = AccountValueQuery(
            account_id="test-account",
            start_date=datetime(2024, 1, 15, tzinfo=UTC)
        )
        entries = list(logger.query_account_values(filters))
        
        assert len(entries) == 1
        assert entries[0].timestamp == entry2.timestamp

    def test_get_latest_value(self, logger):
        """Test getting latest account value."""
        # Create entries
        entry1 = AccountValueEntry(
            entry_id="test-1",
            account_id="test-account",
            portfolio_value=Decimal("10000.00"),
            cash=Decimal("2000.00"),
            equity=Decimal("8000.00"),
            timestamp=datetime(2024, 1, 10, 10, 0, 0, tzinfo=UTC),
            source="test",
        )
        
        entry2 = AccountValueEntry(
            entry_id="test-2",
            account_id="test-account",
            portfolio_value=Decimal("11000.00"),
            cash=Decimal("2500.00"),
            equity=Decimal("8500.00"),
            timestamp=datetime(2024, 1, 20, 10, 0, 0, tzinfo=UTC),
            source="test",
        )
        
        logger.log_account_value(entry1)
        logger.log_account_value(entry2)
        
        # Get latest
        latest = logger.get_latest_value("test-account")
        
        assert latest is not None
        assert latest.portfolio_value == Decimal("11000.00")
        assert latest.timestamp == entry2.timestamp


class TestAccountValueLoggingService:
    """Test cases for AccountValueLoggingService."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def mock_logger(self, temp_dir):
        """Create mock logger for testing."""
        return LocalAccountValueLogger(base_path=temp_dir)

    @pytest.fixture
    def service(self, mock_logger):
        """Create service instance with mock logger."""
        return AccountValueLoggingService(value_logger=mock_logger)

    @pytest.fixture
    def sample_account(self):
        """Create sample account model."""
        return AccountModel(
            account_id="test-account",
            equity=10000.0,
            cash=2000.0,
            buying_power=5000.0,
            day_trades_remaining=3,
            portfolio_value=12000.0,
            last_equity=9500.0,
            daytrading_buying_power=8000.0,
            regt_buying_power=5000.0,
            status="ACTIVE"
        )

    def test_log_current_account_value_disabled(self, service, sample_account):
        """Test logging when service is disabled (default)."""
        # Service should be disabled by default (no env var set)
        result = service.log_current_account_value(sample_account)
        assert result is False

    def test_get_account_value_history_disabled(self, service):
        """Test history retrieval when service is disabled."""
        history = service.get_account_value_history("test-account")
        assert history == []

    def test_is_enabled_default(self, service):
        """Test that service is disabled by default."""
        assert service.is_enabled() is False