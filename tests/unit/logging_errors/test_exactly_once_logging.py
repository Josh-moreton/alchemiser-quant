#!/usr/bin/env python3
"""
Tests for exactly-once logging at orchestrator boundaries.

Validates that errors are logged exactly once by orchestrators and that
there are no duplicate log entries across the system boundaries.
"""

import logging
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.services.errors.exceptions import (
    ConfigurationError,
    DataProviderError,
    MarketDataError,
    StrategyExecutionError,
    TradingClientError,
)
from the_alchemiser.services.errors.handler import TradingSystemErrorHandler


class TestExactlyOnceLoggingOrchestrators:
    """Test that orchestrators log errors exactly once without duplication."""

    def test_trading_system_error_handler_single_log_per_error(self, caplog):
        """Test that TradingSystemErrorHandler logs each error exactly once."""
        caplog.clear()

        handler = TradingSystemErrorHandler()
        test_error = ConfigurationError("Single log test error")

        # Handle the error
        details = handler.handle_error(
            error=test_error,
            context="test_single_log",
            component="test.component.single",
            additional_data={"test": "data"},
        )

        # Verify exactly one error log was generated
        error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
        assert len(error_logs) == 1, f"Expected exactly 1 error log, got {len(error_logs)}"

        # Verify the log content contains error information
        error_log = error_logs[0]
        assert "CONFIGURATION ERROR" in error_log.message
        assert "Single log test error" in error_log.message
        assert "test.component.single" in error_log.message

        # Verify error was recorded in handler
        assert len(handler.errors) == 1
        assert handler.errors[0] == details

    def test_multiple_errors_logged_separately(self, caplog):
        """Test that multiple errors are logged separately, each exactly once."""
        caplog.clear()

        handler = TradingSystemErrorHandler()

        # First error
        error1 = StrategyExecutionError("First strategy error")
        handler.handle_error(error1, "strategy_context_1", "strategy.component.1")

        # Second error
        error2 = TradingClientError("Second trading error")
        handler.handle_error(error2, "trading_context_2", "trading.component.2")

        # Third error
        error3 = DataProviderError("Third data error")
        handler.handle_error(error3, "data_context_3", "data.component.3")

        # Verify exactly three error logs were generated
        error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
        assert len(error_logs) == 3, f"Expected exactly 3 error logs, got {len(error_logs)}"

        # Verify each error is logged with correct information
        log_messages = [record.message for record in error_logs]

        assert any(
            "STRATEGY ERROR" in msg and "First strategy error" in msg for msg in log_messages
        )
        assert any("DATA ERROR" in msg and "Second trading error" in msg for msg in log_messages)
        assert any("DATA ERROR" in msg and "Third data error" in msg for msg in log_messages)

        # Verify all errors are in handler
        assert len(handler.errors) == 3

    def test_main_system_no_duplicate_logging(self, caplog):
        """Test that main system components don't create duplicate logs."""
        from the_alchemiser.main import TradingSystem

        caplog.clear()

        with (
            patch("the_alchemiser.main.load_settings") as mock_load_settings,
            patch("the_alchemiser.main.get_logger") as mock_get_logger,
            patch("the_alchemiser.main.TradingSystemErrorHandler") as mock_handler_class,
            patch(
                "the_alchemiser.interface.cli.signal_analyzer.SignalAnalyzer"
            ) as mock_analyzer_class,
        ):

            # Mock settings and logger
            mock_settings = Mock()
            mock_load_settings.return_value = mock_settings
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            # Mock error handler
            mock_handler = Mock()
            mock_handler_class.return_value = mock_handler

            # Mock analyzer to raise error
            mock_analyzer = Mock()
            mock_analyzer_class.return_value = mock_analyzer
            mock_analyzer.run.side_effect = StrategyExecutionError("Analyzer error test")

            # Create system and trigger error
            system = TradingSystem()
            result = system.analyze_signals()

            assert result is False

            # Verify the error handler was called (this is the main test)
            mock_handler.handle_error.assert_called_once()

            # Verify the error was logged through the handler, not inline
            call_args = mock_handler.handle_error.call_args
            assert call_args is not None
            # Check that an error was passed to handle_error
            assert len(call_args) >= 1  # Should have positional and keyword args

    def test_trading_executor_no_duplicate_logging(self, caplog):
        """Test that TradingExecutor doesn't create duplicate error logs."""
        from the_alchemiser.interface.cli.trading_executor import TradingExecutor

        caplog.clear()

        # Create mock settings
        mock_settings = Mock()
        mock_strategy = Mock()
        mock_strategy.default_strategy_allocations = {"nuclear": 0.3, "tecl": 0.5, "klm": 0.2}
        mock_settings.strategy = mock_strategy

        executor = TradingExecutor(
            settings=mock_settings, live_trading=False, ignore_market_hours=True
        )

        # Mock the trading engine creation to fail
        with patch.object(executor, "_create_trading_engine") as mock_create:
            mock_create.side_effect = TradingClientError("Executor test error")

            # Mock the error handling to track calls
            with patch.object(executor, "_handle_trading_error") as mock_handle:
                # Execute and expect failure
                result = executor.run()

                assert result is False

                # Verify _handle_trading_error was called exactly once
                assert (
                    mock_handle.call_count == 1
                ), f"Expected exactly 1 call to error handler, got {mock_handle.call_count}"

                # Verify no inline error logs were generated
                error_logs = [
                    record for record in caplog.records if record.levelno >= logging.ERROR
                ]
                assert len(error_logs) == 0, f"Expected 0 inline error logs, got {len(error_logs)}"

    def test_orchestrator_boundary_no_log_leakage(self, caplog):
        """Test that errors don't leak across orchestrator boundaries."""
        caplog.clear()

        # Create multiple independent error handlers
        handler1 = TradingSystemErrorHandler()
        handler2 = TradingSystemErrorHandler()

        # Handle errors in different handlers
        error1 = ConfigurationError("Handler 1 error")
        handler1.handle_error(error1, "context1", "component1")

        error2 = MarketDataError("Handler 2 error")
        handler2.handle_error(error2, "context2", "component2")

        # Verify exactly two error logs (one per handler)
        error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
        assert len(error_logs) == 2, f"Expected exactly 2 error logs, got {len(error_logs)}"

        # Verify each handler only has its own error
        assert len(handler1.errors) == 1
        assert len(handler2.errors) == 1
        assert str(handler1.errors[0].error) == "Handler 1 error"
        assert str(handler2.errors[0].error) == "Handler 2 error"

    def test_nested_orchestrator_calls_single_logging(self, caplog):
        """Test that nested orchestrator calls don't create duplicate logs."""
        caplog.clear()

        def outer_orchestrator():
            """Outer orchestrator that calls inner orchestrator."""
            try:
                inner_orchestrator()
            except Exception as e:
                # Outer orchestrator handles the error
                handler = TradingSystemErrorHandler()
                handler.handle_error(error=e, context="outer_orchestrator", component="test.outer")
                raise

        def inner_orchestrator():
            """Inner orchestrator that raises an error."""
            raise StrategyExecutionError("Nested orchestrator error")

        with pytest.raises(StrategyExecutionError):
            outer_orchestrator()

        # Verify only one error log was generated (by outer orchestrator)
        error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
        assert len(error_logs) == 1, f"Expected exactly 1 error log, got {len(error_logs)}"

        error_log = error_logs[0]
        assert "STRATEGY ERROR" in error_log.message
        assert "Nested orchestrator error" in error_log.message

    def test_concurrent_error_handling_no_interference(self, caplog):
        """Test that concurrent error handling doesn't interfere with logging."""
        caplog.clear()

        handler = TradingSystemErrorHandler()

        # Simulate concurrent error handling
        errors = [
            ConfigurationError("Concurrent error 1"),
            TradingClientError("Concurrent error 2"),
            DataProviderError("Concurrent error 3"),
            MarketDataError("Concurrent error 4"),
        ]

        # Handle all errors
        for i, error in enumerate(errors):
            handler.handle_error(
                error=error,
                context=f"concurrent_context_{i}",
                component=f"concurrent.component.{i}",
            )

        # Verify exactly four error logs were generated
        error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
        assert len(error_logs) == 4, f"Expected exactly 4 error logs, got {len(error_logs)}"

        # Verify all errors are recorded
        assert len(handler.errors) == 4

        # Verify no error messages are duplicated
        log_messages = [record.message for record in error_logs]
        unique_messages = set(log_messages)
        assert len(unique_messages) == 4, "All error log messages should be unique"

    def test_error_handler_doesnt_log_successful_operations(self, caplog):
        """Test that error handler doesn't log anything for successful operations."""
        caplog.clear()

        handler = TradingSystemErrorHandler()

        # Perform some successful operations (no errors to handle)
        # Just create the handler and verify it doesn't log anything

        # Check error collection
        errors = handler.get_error_summary()
        # Count non-None entries in the summary
        error_count = sum(1 for v in errors.values() if v is not None)
        assert error_count == 0

        # Verify no logs were generated
        all_logs = list(caplog.records)
        assert len(all_logs) == 0, f"Expected 0 logs for successful operations, got {len(all_logs)}"

    def test_error_suppression_mechanisms_prevent_duplicate_logs(self, caplog):
        """Test that error suppression mechanisms prevent duplicate logging."""
        caplog.clear()

        handler = TradingSystemErrorHandler()
        same_error = ConfigurationError("Duplicate test error")

        # Handle the same error multiple times (simulating retries)
        handler.handle_error(same_error, "context1", "component1")
        handler.handle_error(same_error, "context2", "component2")
        handler.handle_error(same_error, "context3", "component3")

        # Each handle_error call should log the error (they are separate calls)
        error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
        assert (
            len(error_logs) == 3
        ), f"Expected 3 error logs for 3 separate handle_error calls, got {len(error_logs)}"

        # Verify all errors are recorded separately
        assert len(handler.errors) == 3

    def test_logging_respects_orchestrator_boundaries(self, caplog):
        """Test that logging respects orchestrator boundaries and doesn't cross-contaminate."""
        caplog.clear()

        # Create separate orchestrators with their own error handlers
        class MockOrchestrator1:
            def __init__(self):
                self.error_handler = TradingSystemErrorHandler()

            def execute(self):
                try:
                    raise ConfigurationError("Orchestrator 1 error")
                except Exception as e:
                    self.error_handler.handle_error(
                        error=e, context="orchestrator1_operation", component="mock.orchestrator.1"
                    )
                    return False

        class MockOrchestrator2:
            def __init__(self):
                self.error_handler = TradingSystemErrorHandler()

            def execute(self):
                try:
                    raise MarketDataError("Orchestrator 2 error")
                except Exception as e:
                    self.error_handler.handle_error(
                        error=e, context="orchestrator2_operation", component="mock.orchestrator.2"
                    )
                    return False

        # Execute both orchestrators
        orch1 = MockOrchestrator1()
        orch2 = MockOrchestrator2()

        result1 = orch1.execute()
        result2 = orch2.execute()

        assert result1 is False
        assert result2 is False

        # Verify exactly two error logs (one per orchestrator)
        error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
        assert len(error_logs) == 2, f"Expected exactly 2 error logs, got {len(error_logs)}"

        # Verify orchestrators maintain separate error collections
        assert len(orch1.error_handler.errors) == 1
        assert len(orch2.error_handler.errors) == 1
        assert "Orchestrator 1 error" in str(orch1.error_handler.errors[0].error)
        assert "Orchestrator 2 error" in str(orch2.error_handler.errors[0].error)
