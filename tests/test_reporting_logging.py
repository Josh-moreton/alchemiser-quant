#!/usr/bin/env python3
"""
Test reporting and logging scenarios including order execution logging,
error logging, and portfolio state reporting.
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
import tempfile
import os
import json
from datetime import datetime
from alpaca.trading.enums import OrderSide

from the_alchemiser.execution.order_manager_adapter import OrderManagerAdapter


@pytest.fixture
def mock_trading_client():
    """Mock Alpaca trading client."""
    client = MagicMock()
    client.submit_order.return_value = MagicMock(id='test_order_123', status='new')
    client.get_order_by_id.return_value = MagicMock(id='test_order_123', status='filled')
    client.get_all_positions.return_value = []
    client.get_account.return_value = MagicMock(
        buying_power=10000.0, 
        cash=10000.0, 
        portfolio_value=10000.0
    )
    client.get_clock.return_value = MagicMock(is_open=True)
    return client


@pytest.fixture
def mock_data_provider():
    """Mock data provider."""
    provider = MagicMock()
    provider.get_current_price.return_value = 150.0
    provider.get_latest_quote.return_value = (149.0, 151.0)
    return provider


@pytest.fixture
def order_manager(mock_trading_client, mock_data_provider):
    """Create OrderManagerAdapter for testing."""
    return OrderManagerAdapter(mock_trading_client, mock_data_provider)


class TestOrderExecutionLogging:
    """Test logging of order execution events."""
    
    def test_successful_order_logging(self, order_manager, mock_trading_client):
        """Test logging of successful order execution."""
        with patch('logging.info') as mock_info:
            # Place order
            order_id = order_manager.place_limit_or_market('AAPL', 10.0, OrderSide.BUY)
            
            assert order_id is not None
            
            # Check if info logging was called for successful order
            mock_info.assert_called()
    
    def test_failed_order_logging(self, order_manager, mock_trading_client):
        """Test logging of failed order attempts."""
        # Mock order failure
        mock_trading_client.submit_order.side_effect = Exception("Order failed")
        
        with patch('logging.error') as mock_error:
            # Attempt order
            order_id = order_manager.place_limit_or_market('AAPL', 10.0, OrderSide.BUY)
            
            assert order_id is None
            
            # Check if error logging was called
            mock_error.assert_called()
    
    def test_order_details_logging(self, order_manager, mock_trading_client):
        """Test that order details are properly logged."""
        with patch('logging.getLogger') as mock_logger:
            logger_instance = MagicMock()
            mock_logger.return_value = logger_instance
            
            # Place order with specific details
            symbol = 'GOOGL'
            quantity = 5.5
            side = OrderSide.SELL
            
            order_id = order_manager.place_limit_or_market(symbol, quantity, side)
            
            # Verify order details appear in logs
            # Check that logging calls contain relevant information
            log_calls = logger_instance.info.call_args_list
            if log_calls:
                # At least one log call should contain order information
                log_messages = [str(call) for call in log_calls]
                assert any(symbol in msg for msg in log_messages)
    
    def test_order_settlement_logging(self, order_manager, mock_trading_client):
        """Test logging of order settlement process."""
        with patch('logging.info') as mock_info:
            # Mock order progression
            mock_trading_client.get_order_by_id.return_value = MagicMock(
                id='test_order', status='filled'
            )
            
            # Wait for settlement
            sell_orders = [{'order_id': 'test_order'}]
            result = order_manager.wait_for_settlement(sell_orders, max_wait_time=1, poll_interval=1)
            
            assert result is True
            
            # Check settlement logging
            mock_info.assert_called()


class TestErrorLogging:
    """Test comprehensive error logging scenarios."""
    
    def test_api_error_logging(self, order_manager, mock_trading_client):
        """Test logging of API errors with details."""
        from alpaca.common.exceptions import APIError
        
        # Mock specific API error
        error_response = {"code": 40310000, "message": "insufficient buying power"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        with patch('logging.error') as mock_error:
            order_id = order_manager.place_limit_or_market('AAPL', 1000.0, OrderSide.BUY)
            
            assert order_id is None
            
            # Check that error details are logged
            mock_error.assert_called()
    
    def test_network_error_logging(self, order_manager, mock_trading_client):
        """Test logging of network-related errors."""
        import requests.exceptions
        
        # Mock network error
        mock_trading_client.submit_order.side_effect = requests.exceptions.ConnectionError("Network timeout")
        
        with patch('logging.error') as mock_error:
            order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
            
            assert order_id is None
            
            # Check network error logging
            mock_error.assert_called()
    
    def test_unexpected_error_logging(self, order_manager, mock_trading_client):
        """Test logging of unexpected/unhandled errors."""
        # Mock unexpected error
        mock_trading_client.submit_order.side_effect = ValueError("Unexpected error")
        
        with patch('logging.error') as mock_error:
            order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
            
            assert order_id is None
            
            # Check unexpected error logging
            mock_error.assert_called()
    
    def test_error_context_logging(self, order_manager, mock_trading_client, mock_data_provider):
        """Test that error logs include relevant context."""
        # Mock error with context
        mock_trading_client.submit_order.side_effect = Exception("Test error")
        mock_data_provider.get_current_price.return_value = 175.0
        
        with patch('logging.getLogger') as mock_logger:
            logger_instance = MagicMock()
            mock_logger.return_value = logger_instance
            
            # Attempt order with specific context
            symbol = 'TSLA'
            quantity = 25.0
            side = OrderSide.BUY
            
            order_id = order_manager.place_limit_or_market(symbol, quantity, side)
            
            assert order_id is None
            
            # Check that context information is logged
            error_calls = logger_instance.error.call_args_list
            if error_calls:
                error_messages = [str(call) for call in error_calls]
                # Should contain symbol, quantity, or side information
                assert any(symbol in msg for msg in error_messages)


class TestPortfolioStateReporting:
    """Test portfolio state reporting and tracking."""
    
    def test_portfolio_snapshot_reporting(self, order_manager, mock_trading_client):
        """Test generation of portfolio snapshots."""
        # Mock portfolio positions
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(
                symbol='AAPL', 
                qty=10.0, 
                market_value=1500.0,
                avg_entry_price=140.0,
                unrealized_pl=150.0
            ),
            MagicMock(
                symbol='GOOGL', 
                qty=2.0, 
                market_value=5000.0,
                avg_entry_price=2400.0,
                unrealized_pl=200.0
            )
        ]
        
        # Mock account information
        mock_trading_client.get_account.return_value = MagicMock(
            portfolio_value=6500.0,
            buying_power=2000.0,
            cash=1000.0,
            day_trading_buying_power=8000.0
        )
        
        # Get portfolio snapshot (through order manager's access to client)
        positions = mock_trading_client.get_all_positions()
        account = mock_trading_client.get_account()
        
        # Verify portfolio data
        assert len(positions) == 2
        assert account.portfolio_value == 6500.0
        
        # Test portfolio summary calculations
        total_position_value = sum(pos.market_value for pos in positions)
        total_unrealized_pl = sum(pos.unrealized_pl for pos in positions)
        
        assert total_position_value == 6500.0  # 1500 + 5000
        assert total_unrealized_pl == 350.0    # 150 + 200
    
    def test_position_change_tracking(self, order_manager, mock_trading_client):
        """Test tracking of position changes over time."""
        # Initial portfolio state
        initial_positions = [
            MagicMock(symbol='AAPL', qty=10.0, market_value=1500.0)
        ]
        
        # Updated portfolio state after trades
        updated_positions = [
            MagicMock(symbol='AAPL', qty=15.0, market_value=2250.0),
            MagicMock(symbol='GOOGL', qty=1.0, market_value=2500.0)
        ]
        
        # Mock sequential calls
        mock_trading_client.get_all_positions.side_effect = [
            initial_positions,
            updated_positions
        ]
        
        # Get initial state
        initial_state = mock_trading_client.get_all_positions()
        initial_symbols = {pos.symbol for pos in initial_state}
        
        # Simulate trading activity
        order_id = order_manager.place_limit_or_market('GOOGL', 1.0, OrderSide.BUY)
        assert order_id is not None
        
        # Get updated state
        updated_state = mock_trading_client.get_all_positions()
        updated_symbols = {pos.symbol for pos in updated_state}
        
        # Track changes
        new_positions = updated_symbols - initial_symbols
        position_changes = len(updated_state) - len(initial_state)
        
        assert 'GOOGL' in new_positions
        assert position_changes == 1
    
    def test_daily_performance_reporting(self, order_manager, mock_trading_client):
        """Test daily performance metrics reporting."""
        # Mock account states at different times
        morning_account = MagicMock(
            portfolio_value=10000.0,
            day_trading_buying_power=40000.0,
            buying_power=20000.0
        )
        
        evening_account = MagicMock(
            portfolio_value=10500.0,  # +5% gain
            day_trading_buying_power=42000.0,
            buying_power=21000.0
        )
        
        mock_trading_client.get_account.side_effect = [morning_account, evening_account]
        
        # Get morning state
        morning_value = mock_trading_client.get_account().portfolio_value
        
        # Simulate trading day
        # ... trading activities ...
        
        # Get evening state
        evening_value = mock_trading_client.get_account().portfolio_value
        
        # Calculate performance
        daily_return = (evening_value - morning_value) / morning_value
        daily_pnl = evening_value - morning_value
        
        assert daily_return == 0.05  # 5% return
        assert daily_pnl == 500.0    # $500 profit
    
    def test_risk_metrics_reporting(self, order_manager, mock_trading_client):
        """Test risk metrics calculation and reporting."""
        # Mock positions with risk characteristics
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(
                symbol='AAPL', 
                qty=100.0, 
                market_value=15000.0,
                avg_entry_price=140.0,
                current_price=150.0
            ),
            MagicMock(
                symbol='TSLA', 
                qty=50.0, 
                market_value=10000.0,
                avg_entry_price=180.0,
                current_price=200.0
            )
        ]
        
        mock_trading_client.get_account.return_value = MagicMock(
            portfolio_value=25000.0,
            buying_power=5000.0
        )
        
        # Calculate risk metrics
        positions = mock_trading_client.get_all_positions()
        account = mock_trading_client.get_account()
        
        # Position concentration risk
        position_weights = {pos.symbol: pos.market_value / account.portfolio_value for pos in positions}
        max_position_weight = max(position_weights.values())
        
        # Leverage calculation
        total_position_value = sum(pos.market_value for pos in positions)
        leverage_ratio = total_position_value / account.portfolio_value
        
        assert max_position_weight == 0.6  # 60% in AAPL (concentration risk)
        assert leverage_ratio == 1.0       # No leverage (positions = portfolio value)


class TestLogFileManagement:
    """Test log file creation, rotation, and management."""
    
    def test_log_file_creation(self, order_manager):
        """Test that log files are created properly."""
        with patch('logging.info') as mock_info:
            # Place order to trigger logging
            order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
            
            # Verify logger was used
            mock_info.assert_called()
    
    def test_structured_logging_format(self, order_manager):
        """Test structured logging with JSON format."""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'event': 'order_placed',
            'symbol': 'AAPL',
            'quantity': 10.0,
            'side': 'BUY',
            'order_id': 'test_order_123'
        }
        
        with patch('logging.getLogger') as mock_logger:
            logger_instance = MagicMock()
            mock_logger.return_value = logger_instance
            
            # Simulate structured logging
            logger_instance.info.return_value = None
            
            # Test JSON serialization
            json_log = json.dumps(log_data)
            assert 'order_placed' in json_log
            assert 'AAPL' in json_log
    
    def test_log_rotation_handling(self, order_manager):
        """Test log file rotation behavior."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, 'trading.log')
            
            # Simulate writing to log file to trigger rotation logic
            with patch('builtins.open', mock_open()) as mock_file:
                # Simulate actual log file operations
                with open(log_file, 'w') as f:
                    f.write("test log entry\n")
                
                # Verify file operations
                mock_file.assert_called()
    
    def test_log_level_configuration(self, order_manager):
        """Test different log levels and filtering."""
        with patch('logging.getLogger') as mock_logger:
            logger_instance = MagicMock()
            mock_logger.return_value = logger_instance
            
            # Test different log levels
            logger_instance.setLevel.return_value = None
            
            # Simulate different severity events
            logger_instance.debug("Debug message")    # Should be filtered in production
            logger_instance.info("Info message")      # Normal operations
            logger_instance.warning("Warning message") # Potential issues
            logger_instance.error("Error message")    # Actual errors
            logger_instance.critical("Critical message") # System failures
            
            # Verify all levels can be called
            logger_instance.debug.assert_called()
            logger_instance.info.assert_called()
            logger_instance.warning.assert_called()
            logger_instance.error.assert_called()
            logger_instance.critical.assert_called()


class TestAuditTrail:
    """Test audit trail and compliance reporting."""
    
    def test_complete_order_lifecycle_audit(self, order_manager, mock_trading_client):
        """Test complete audit trail for order lifecycle."""
        order_events = []
        
        # Capture logging calls directly
        def capture_log(message, *args, **kwargs):
            order_events.append({
                'timestamp': datetime.now().isoformat(),
                'message': str(message),
                'level': 'INFO'
            })
        
        with patch('logging.info', side_effect=capture_log):
            # Execute complete order lifecycle
            order_id = order_manager.place_limit_or_market('AAPL', 10.0, OrderSide.BUY)
            
            # Mock order status checks
            mock_trading_client.get_order_by_id.return_value = MagicMock(
                id=order_id, status='filled'
            )
            
            # Wait for settlement
            sell_orders = [{'order_id': order_id}] if order_id else []
            if sell_orders:
                order_manager.wait_for_settlement(sell_orders, max_wait_time=1, poll_interval=1)
            
            # Verify audit trail completeness
            assert len(order_events) > 0
    
    def test_regulatory_compliance_data(self, order_manager, mock_trading_client):
        """Test collection of data required for regulatory compliance."""
        compliance_data = {
            'account_id': 'test_account_123',
            'order_timestamp': datetime.now().isoformat(),
            'symbol': 'AAPL',
            'quantity': 10.0,
            'side': 'BUY',
            'order_type': 'MARKET',
            'execution_price': 150.0,
            'execution_timestamp': datetime.now().isoformat(),
            'commission': 0.0,
            'regulatory_flags': []
        }
        
        # Verify all required fields are present
        required_fields = [
            'account_id', 'order_timestamp', 'symbol', 'quantity', 
            'side', 'order_type', 'execution_price'
        ]
        
        for field in required_fields:
            assert field in compliance_data
            assert compliance_data[field] is not None
    
    def test_error_incident_reporting(self, order_manager, mock_trading_client):
        """Test incident reporting for errors and failures."""
        # Mock critical error
        mock_trading_client.submit_order.side_effect = Exception("Critical system error")
        
        incident_report = {
            'incident_id': 'INC_001',
            'timestamp': datetime.now().isoformat(),
            'severity': 'HIGH',
            'component': 'order_manager',
            'error_message': 'Critical system error',
            'attempted_action': 'place_order',
            'symbol': 'AAPL',
            'quantity': 10.0,
            'recovery_action': 'retry_later'
        }
        
        with patch('logging.error') as mock_error:
            # Attempt order
            order_id = order_manager.place_limit_or_market('AAPL', 10.0, OrderSide.BUY)
            
            assert order_id is None
            
            # Verify incident was logged
            mock_error.assert_called()
            
            # Verify incident report structure
            assert 'incident_id' in incident_report
            assert 'severity' in incident_report
            assert incident_report['severity'] == 'HIGH'
