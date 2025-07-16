import datetime as dt
import re
import json
import logging
from .config import Config

class Alert:
    """Simple alert class for trading signals."""
    def __init__(self, symbol, action, reason, timestamp, price):
        self.symbol = symbol
        self.action = action
        self.reason = reason
        self.timestamp = timestamp
        self.price = price

    def to_dict(self):
        return {
            'symbol': self.symbol,
            'action': self.action,
            'reason': self.reason,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, dt.datetime) else str(self.timestamp),
            'price': self.price
        }

# Factory function for alert creation (can be extended for more logic)
def create_alert(symbol, action, reason, price, timestamp=None):
    if timestamp is None:
        timestamp = dt.datetime.now()
    return Alert(symbol, action, reason, timestamp, price)

def create_alerts_from_signal(symbol, action, reason, indicators, market_data, data_provider, ensure_scalar_price, strategy_engine=None):
    """
    Create Alert objects based on the signal type and portfolio logic.
    data_provider: must have get_current_price(symbol)
    ensure_scalar_price: function to convert price to scalar
    strategy_engine: NuclearStrategyEngine instance to avoid circular imports
    """
    alerts = []
    
    if symbol == 'NUCLEAR_PORTFOLIO' and action == 'BUY':
        nuclear_portfolio = indicators.get('nuclear_portfolio')
        if not nuclear_portfolio and market_data and strategy_engine:
            # Use passed strategy_engine to avoid circular import
            nuclear_portfolio = strategy_engine.get_nuclear_portfolio(indicators, market_data)
        for stock_symbol, allocation in (nuclear_portfolio or {}).items():
            current_price = data_provider.get_current_price(stock_symbol)
            current_price = ensure_scalar_price(current_price)
            portfolio_reason = f"Nuclear portfolio allocation: {allocation['weight']:.1%} ({reason})"
            alerts.append(Alert(
                symbol=stock_symbol,
                action=action,
                reason=portfolio_reason,
                timestamp=dt.datetime.now(),
                price=current_price
            ))
        return alerts
    elif symbol == 'UVXY_BTAL_PORTFOLIO' and action == 'BUY':
        # UVXY 75%
        uvxy_price = data_provider.get_current_price('UVXY')
        uvxy_price = ensure_scalar_price(uvxy_price)
        alerts.append(Alert(
            symbol='UVXY',
            action=action,
            reason=f"Volatility hedge allocation: 75% ({reason})",
            timestamp=dt.datetime.now(),
            price=uvxy_price
        ))
        # BTAL 25%
        btal_price = data_provider.get_current_price('BTAL')
        btal_price = ensure_scalar_price(btal_price)
        alerts.append(Alert(
            symbol='BTAL',
            action=action,
            reason=f"Anti-beta hedge allocation: 25% ({reason})",
            timestamp=dt.datetime.now(),
            price=btal_price
        ))
        return alerts
    elif symbol == 'BEAR_PORTFOLIO' and action == 'BUY':
        portfolio_match = re.findall(r'(\w+) \((\d+\.?\d*)%\)', reason)
        if portfolio_match:
            for stock_symbol, allocation_str in portfolio_match:
                current_price = data_provider.get_current_price(stock_symbol)
                current_price = ensure_scalar_price(current_price)
                bear_reason = f"Bear market allocation: {allocation_str}% (inverse volatility weighted)"
                alerts.append(Alert(
                    symbol=stock_symbol,
                    action=action,
                    reason=bear_reason,
                    timestamp=dt.datetime.now(),
                    price=current_price
                ))
            return alerts
        else:
            current_price = data_provider.get_current_price(symbol)
            current_price = ensure_scalar_price(current_price)
            alerts.append(Alert(
                symbol=symbol,
                action=action,
                reason=reason,
                timestamp=dt.datetime.now(),
                price=current_price
            ))
            return alerts
    else:
        current_price = data_provider.get_current_price(symbol)
        current_price = ensure_scalar_price(current_price)
        alerts.append(Alert(
            symbol=symbol,
            action=action,
            reason=reason,
            timestamp=dt.datetime.now(),
            price=current_price
        ))
        return alerts

def log_alert_to_file(alert, log_file_path=None):
    """Log alert to file - centralized logging logic"""
    if log_file_path is None:
        config = Config()
        log_file_path = config['logging']['nuclear_alerts_json']
    
    alert_data = {
        'timestamp': alert.timestamp.isoformat(),
        'symbol': alert.symbol,
        'action': alert.action,
        'price': alert.price,
        'reason': alert.reason
    }
    
    try:
        with open(log_file_path, 'a') as f:
            f.write(json.dumps(alert_data) + '\n')
    except Exception as e:
        logging.error(f"Failed to log alert: {e}")

def log_alerts_to_file(alerts, log_file_path=None):
    """Log multiple alerts to file"""
    if log_file_path is None:
        config = Config()
        log_file_path = config['logging']['nuclear_alerts_json']
    
    for alert in alerts:
        log_alert_to_file(alert, log_file_path)
