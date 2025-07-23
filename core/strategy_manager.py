#!/usr/bin/env python3
"""
Multi-Strategy Portfolio Manager

This module manages multiple trading strategies running in parallel with portfolio allocation.
It tracks positions for each strategy separately to prevent confusion and enables proper
portfolio management across multiple strategy signals.

Key Features:
- Portfolio allocation between strategies (e.g., 50% Nuclear, 50% TECL)
- Position tracking per strategy
- Strategy execution coordination
- Consolidated reporting
"""

import json
import logging
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum

from .config import Config
from .nuclear_trading_bot import NuclearStrategyEngine, ActionType
from .tecl_strategy_engine import TECLStrategyEngine
# Centralized logging setup
from .logging_utils import setup_logging
setup_logging()


class StrategyType(Enum):
    NUCLEAR = "NUCLEAR"
    TECL = "TECL"


class StrategyPosition:
    """Represents a position held by a specific strategy"""
    def __init__(self, strategy_type: StrategyType, symbol: str, allocation: float, 
                 reason: str, timestamp: datetime):
        self.strategy_type = strategy_type
        self.symbol = symbol
        self.allocation = allocation  # Percentage of strategy's allocation
        self.reason = reason
        self.timestamp = timestamp
    
    def to_dict(self) -> Dict:
        return {
            'strategy_type': self.strategy_type.value,
            'symbol': self.symbol,
            'allocation': self.allocation,
            'reason': self.reason,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StrategyPosition':
        return cls(
            strategy_type=StrategyType(data['strategy_type']),
            symbol=data['symbol'],
            allocation=data['allocation'],
            reason=data['reason'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


class MultiStrategyManager:
    """Manages multiple trading strategies with portfolio allocation"""
    
    def __init__(self, strategy_allocations: Optional[Dict[StrategyType, float]] = None):
        """
        Initialize multi-strategy manager
        
        Args:
            strategy_allocations: Dict mapping strategy types to portfolio percentages
                                Example: {StrategyType.NUCLEAR: 0.5, StrategyType.TECL: 0.5}
        """
        self.config = Config()
        
        # Default 50/50 allocation if not specified
        self.strategy_allocations = strategy_allocations or {
            StrategyType.NUCLEAR: 0.5,
            StrategyType.TECL: 0.5
        }
        
        # Validate allocations sum to 1.0
        total_allocation = sum(self.strategy_allocations.values())
        if abs(total_allocation - 1.0) > 0.01:
            raise ValueError(f"Strategy allocations must sum to 1.0, got {total_allocation}")
        
        # Create shared unified data provider to avoid redundant AWS/Alpaca initialization
        from .data_provider import UnifiedDataProvider
        shared_data_provider = UnifiedDataProvider(paper_trading=True)
        
        # Initialize strategy engines with shared data provider
        self.nuclear_engine = NuclearStrategyEngine(data_provider=shared_data_provider)
        self.tecl_engine = TECLStrategyEngine(data_provider=shared_data_provider)
        
        # Position tracking file
        self.positions_file = self.config['logging'].get('strategy_positions', 
                                                        'data/logs/strategy_positions.json')
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.positions_file), exist_ok=True)
        
        logging.info(f"MultiStrategyManager initialized with allocations: {self.strategy_allocations}")
    
    def get_current_positions(self) -> Dict[StrategyType, List[StrategyPosition]]:
        """Load current strategy positions from file"""
        try:
            if not os.path.exists(self.positions_file):
                return {strategy: [] for strategy in StrategyType}
            
            with open(self.positions_file, 'r') as f:
                data = json.load(f)
            
            positions = {strategy: [] for strategy in StrategyType}
            for strategy_name, position_list in data.get('positions', {}).items():
                strategy_type = StrategyType(strategy_name)
                positions[strategy_type] = [
                    StrategyPosition.from_dict(pos) for pos in position_list
                ]
            
            return positions
        except Exception as e:
            logging.error(f"Error loading strategy positions: {e}")
            return {strategy: [] for strategy in StrategyType}
    
    def save_positions(self, positions: Dict[StrategyType, List[StrategyPosition]]):
        """Save strategy positions to file"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'positions': {
                    strategy.value: [pos.to_dict() for pos in pos_list]
                    for strategy, pos_list in positions.items()
                }
            }
            
            with open(self.positions_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logging.info(f"Strategy positions saved to {self.positions_file}")
        except Exception as e:
            logging.error(f"Error saving strategy positions: {e}")
    
    def run_all_strategies(self) -> Tuple[Dict[StrategyType, Any], Dict[str, float]]:
        """
        Run all strategies and return their signals plus consolidated portfolio allocation
        
        Returns:
            Tuple of (strategy_signals, consolidated_portfolio)
            - strategy_signals: Dict mapping strategy types to their signals/results
            - consolidated_portfolio: Dict of symbol -> total_portfolio_weight
        """
        logging.info("Running all strategies...")
        
        strategy_signals = {}
        consolidated_portfolio = {}
        
        # Get market data (combined from all strategies using shared data provider)
        all_symbols = set(self.nuclear_engine.all_symbols + self.tecl_engine.all_symbols)
        market_data = {}
        
        # Fetch data for all required symbols using the shared data provider
        shared_data_provider = self.nuclear_engine.data_provider  # Both engines share the same instance
        for symbol in all_symbols:
            data = shared_data_provider.get_data(symbol)
            if not data.empty:
                market_data[symbol] = data
            else:
                logging.warning(f"Could not fetch data for {symbol}")
        
        logging.info(f"Fetched market data for {len(market_data)} symbols using shared data provider")
        
        # Run Nuclear Strategy
        try:
            nuclear_indicators = self.nuclear_engine.calculate_indicators(market_data)
            nuclear_result = self.nuclear_engine.evaluate_nuclear_strategy(nuclear_indicators, market_data)
            strategy_signals[StrategyType.NUCLEAR] = {
                'symbol': nuclear_result[0],
                'action': nuclear_result[1],
                'reason': nuclear_result[2],
                'indicators': nuclear_indicators,
                'market_data': market_data
            }
            logging.info(f"Nuclear strategy: {nuclear_result[1]} {nuclear_result[0]} - {nuclear_result[2]}")
        except Exception as e:
            logging.error(f"Error running Nuclear strategy: {e}")
            strategy_signals[StrategyType.NUCLEAR] = {
                'symbol': 'SPY',
                'action': ActionType.HOLD.value,
                'reason': f"Nuclear strategy error: {e}",
                'indicators': {},
                'market_data': {}
            }
        
        # Run TECL Strategy
        try:
            tecl_indicators = self.tecl_engine.calculate_indicators(market_data)
            tecl_result = self.tecl_engine.evaluate_tecl_strategy(tecl_indicators, market_data)
            strategy_signals[StrategyType.TECL] = {
                'symbol': tecl_result[0],
                'action': tecl_result[1],
                'reason': tecl_result[2],
                'indicators': tecl_indicators,
                'market_data': market_data
            }
            logging.info(f"TECL strategy: {tecl_result[1]} {tecl_result[0]} - {tecl_result[2]}")
        except Exception as e:
            logging.error(f"Error running TECL strategy: {e}")
            strategy_signals[StrategyType.TECL] = {
                'symbol': 'BIL',
                'action': ActionType.HOLD.value,
                'reason': f"TECL strategy error: {e}",
                'indicators': {},
                'market_data': {}
            }
        
        # Create consolidated portfolio allocation
        for strategy_type, signal_data in strategy_signals.items():
            if signal_data['action'] == ActionType.BUY.value:
                strategy_allocation = self.strategy_allocations[strategy_type]
                
                # Handle portfolio vs single symbol signals
                if signal_data['symbol'] in ['NUCLEAR_PORTFOLIO', 'BEAR_PORTFOLIO', 'UVXY_BTAL_PORTFOLIO']:
                    # Multi-asset portfolio signal - get actual allocations
                    if strategy_type == StrategyType.NUCLEAR:
                        portfolio = self._get_nuclear_portfolio_allocation(signal_data)
                    else:
                        portfolio = self._get_strategy_portfolio_allocation(signal_data, strategy_type)
                    
                    for symbol, weight in portfolio.items():
                        total_weight = strategy_allocation * weight
                        if symbol in consolidated_portfolio:
                            consolidated_portfolio[symbol] += total_weight
                        else:
                            consolidated_portfolio[symbol] = total_weight
                else:
                    # Single symbol signal
                    symbol = signal_data['symbol']
                    if symbol in consolidated_portfolio:
                        consolidated_portfolio[symbol] += strategy_allocation
                    else:
                        consolidated_portfolio[symbol] = strategy_allocation
        
        # Update position tracking
        self._update_position_tracking(strategy_signals, consolidated_portfolio)
        
        logging.info(f"Consolidated portfolio: {consolidated_portfolio}")
        return strategy_signals, consolidated_portfolio
    
    def _get_nuclear_portfolio_allocation(self, signal_data: Dict) -> Dict[str, float]:
        """Extract portfolio allocation from Nuclear strategy signal"""
        indicators = signal_data.get('indicators', {})
        market_data = signal_data.get('market_data', {})
        
        if signal_data['symbol'] == 'NUCLEAR_PORTFOLIO':
            # Bull market nuclear portfolio
            portfolio = self.nuclear_engine.get_nuclear_portfolio(indicators, market_data)
            return {symbol: data['weight'] for symbol, data in portfolio.items()}
        
        elif signal_data['symbol'] == 'BEAR_PORTFOLIO':
            # Bear market portfolio - need to extract from the combination logic
            # This is more complex as it involves two subgroups combined with inverse volatility
            # For now, return equal weights - this could be enhanced
            return {'SQQQ': 0.6, 'TQQQ': 0.4}  # Default bear allocation
        
        elif signal_data['symbol'] == 'UVXY_BTAL_PORTFOLIO':
            # Volatility hedge portfolio
            return {'UVXY': 0.75, 'BTAL': 0.25}
        
        return {}
    
    def _get_strategy_portfolio_allocation(self, signal_data: Dict, strategy_type: StrategyType) -> Dict[str, float]:
        """Extract portfolio allocation from any strategy signal"""
        if strategy_type == StrategyType.TECL:
            # TECL strategy returns single symbols, so return 100% allocation
            return {signal_data['symbol']: 1.0}
        
        return {}
    
    def _update_position_tracking(self, strategy_signals: Dict[StrategyType, Any], 
                                consolidated_portfolio: Dict[str, float]):
        """Update position tracking with current strategy positions"""
        try:
            new_positions = {strategy: [] for strategy in StrategyType}
            
            for strategy_type, signal_data in strategy_signals.items():
                if signal_data['action'] == ActionType.BUY.value:
                    strategy_allocation = self.strategy_allocations[strategy_type]
                    
                    # Create position record for each symbol this strategy wants to hold
                    for symbol, total_weight in consolidated_portfolio.items():
                        # Calculate this strategy's contribution to this symbol
                        strategy_weight = total_weight / strategy_allocation if strategy_allocation > 0 else 0
                        
                        # Only record if this strategy actually contributed to this position
                        if strategy_weight > 0.001:  # Minimum threshold
                            position = StrategyPosition(
                                strategy_type=strategy_type,
                                symbol=symbol,
                                allocation=strategy_weight,
                                reason=signal_data['reason'],
                                timestamp=datetime.now()
                            )
                            new_positions[strategy_type].append(position)
            
            # Save updated positions
            self.save_positions(new_positions)
            
        except Exception as e:
            logging.error(f"Error updating position tracking: {e}")
    
    def get_strategy_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of each strategy's recent performance and current positions"""
        positions = self.get_current_positions()
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'strategy_allocations': {k.value: v for k, v in self.strategy_allocations.items()},
            'strategies': {}
        }
        
        for strategy_type, position_list in positions.items():
            strategy_summary = {
                'allocation': self.strategy_allocations[strategy_type],
                'current_positions': len(position_list),
                'positions': [
                    {
                        'symbol': pos.symbol,
                        'allocation': pos.allocation,
                        'reason': pos.reason,
                        'age_hours': (datetime.now() - pos.timestamp).total_seconds() / 3600
                    }
                    for pos in position_list
                ]
            }
            summary['strategies'][strategy_type.value] = strategy_summary
        
        return summary


def main():
    """Test the multi-strategy manager"""
    import pprint
    
    logging.basicConfig(level=logging.INFO)
    
    # Create manager with 50/50 allocation
    manager = MultiStrategyManager({
        StrategyType.NUCLEAR: 0.5,
        StrategyType.TECL: 0.5
    })
    
    print("🚀 Running Multi-Strategy Analysis")
    print("=" * 50)
    
    # Run all strategies
    strategy_signals, consolidated_portfolio = manager.run_all_strategies()
    
    print("\n📊 Strategy Signals:")
    for strategy, signal in strategy_signals.items():
        print(f"  {strategy.value}: {signal['action']} {signal['symbol']} - {signal['reason']}")
    
    print("\n🎯 Consolidated Portfolio:")
    for symbol, weight in consolidated_portfolio.items():
        print(f"  {symbol}: {weight:.1%}")
    
    print("\n📈 Strategy Performance Summary:")
    summary = manager.get_strategy_performance_summary()
    pprint.pprint(summary)


if __name__ == "__main__":
    main()
