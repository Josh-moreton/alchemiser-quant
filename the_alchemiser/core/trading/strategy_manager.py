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

from the_alchemiser.core.config import Config
from the_alchemiser.core.trading.nuclear_signals import NuclearStrategyEngine, ActionType
from the_alchemiser.core.trading.tecl_signals import TECLStrategyEngine
from the_alchemiser.core.trading.klm_ensemble_engine import KLMStrategyEnsemble


class StrategyType(Enum):
    NUCLEAR = "NUCLEAR"
    TECL = "TECL"
    KLM = "KLM"


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
    
    def __init__(self, strategy_allocations: Optional[Dict[StrategyType, float]] = None, shared_data_provider=None, config=None):
        """
        Initialize multi-strategy manager
        
        Args:
            strategy_allocations: Dict mapping strategy types to portfolio percentages
                                Example: {StrategyType.NUCLEAR: 0.5, StrategyType.TECL: 0.5}
            shared_data_provider: Shared UnifiedDataProvider instance (optional)
            config: Configuration object. If None, will load from global config.
        """
        # Use provided config or load global config
        if config is None:
            from the_alchemiser.core.config import get_config
            config = get_config()
        self.config = config
        
        # Default allocation from config if not specified
        if strategy_allocations is None:
            default_allocations = self.config['strategy'].get('default_strategy_allocations', {
                'nuclear': 0.4,
                'tecl': 0.6,
                'klm': 0.0
            })
            self.strategy_allocations = {
                StrategyType.NUCLEAR: default_allocations.get('nuclear', 0.4),
                StrategyType.TECL: default_allocations.get('tecl', 0.6)
            }
            
            # Add KLM allocation if specified in config
            klm_allocation = default_allocations.get('klm', 0.0)
            if klm_allocation > 0:
                self.strategy_allocations[StrategyType.KLM] = klm_allocation
        else:
            self.strategy_allocations = strategy_allocations
        
        # Validate allocations sum to 1.0
        total_allocation = sum(self.strategy_allocations.values())
        if abs(total_allocation - 1.0) > 0.01:
            raise ValueError(f"Strategy allocations must sum to 1.0, got {total_allocation}")
        
        # Use provided shared_data_provider, or create one if not given
        if shared_data_provider is None:
            from the_alchemiser.core.data.data_provider import UnifiedDataProvider
            shared_data_provider = UnifiedDataProvider(paper_trading=True)
        
        # Initialize strategy orchestration engines with shared data provider
        self.nuclear_engine = NuclearStrategyEngine(data_provider=shared_data_provider)
        self.tecl_engine = TECLStrategyEngine(data_provider=shared_data_provider)
        
        # Initialize KLM ensemble if allocated
        self.klm_ensemble = None
        if StrategyType.KLM in self.strategy_allocations:
            self.klm_ensemble = KLMStrategyEnsemble(data_provider=shared_data_provider)
        
        logging.debug(f"MultiStrategyManager initialized with allocations: {self.strategy_allocations}")
    
    def run_all_strategies(self) -> Tuple[Dict[StrategyType, Any], Dict[str, float]]:
        """
        Run all strategies and return their signals plus consolidated portfolio allocation
        
        Returns:
            Tuple of (strategy_signals, consolidated_portfolio)
            - strategy_signals: Dict mapping strategy types to their signals/results
            - consolidated_portfolio: Dict of symbol -> total_portfolio_weight
        """
        logging.debug("Running all strategies...")
        
        strategy_signals = {}
        consolidated_portfolio = {}
        
        # Get market data (combined from all strategies using shared data provider)
        all_symbols = set(self.nuclear_engine.all_symbols + self.tecl_engine.all_symbols)
        
        # Add KLM symbols if KLM ensemble is enabled
        if self.klm_ensemble is not None:
            all_symbols.update(self.klm_ensemble.all_symbols)
            
        market_data = {}
        
        # Fetch data for all required symbols using the shared data provider
        shared_data_provider = self.nuclear_engine.data_provider  # Both engines share the same instance
        for symbol in all_symbols:
            data = shared_data_provider.get_data(symbol)
            if not data.empty:
                market_data[symbol] = data
            else:
                logging.warning(f"Could not fetch data for {symbol}")
        
        # Market data fetched successfully
        logging.debug(f"Fetched market data for {len(market_data)} symbols using shared data provider")
        
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
            logging.debug(f"Nuclear strategy: {nuclear_result[1]} {nuclear_result[0]} - {nuclear_result[2]}")
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
            logging.debug(f"TECL strategy: {tecl_result[1]} {tecl_result[0]} - {tecl_result[2]}")
        except Exception as e:
            logging.error(f"Error running TECL strategy: {e}")
            strategy_signals[StrategyType.TECL] = {
                'symbol': 'BIL',
                'action': ActionType.HOLD.value,
                'reason': f"TECL strategy error: {e}",
                'indicators': {},
                'market_data': {}
            }
        
        # Run KLM Strategy Ensemble (if enabled)
        if self.klm_ensemble is not None:
            try:
                klm_indicators = self.klm_ensemble.calculate_indicators(market_data)
                klm_result = self.klm_ensemble.evaluate_ensemble(klm_indicators, market_data)
                strategy_signals[StrategyType.KLM] = {
                    'symbol': klm_result[0],  # symbol_or_allocation
                    'action': klm_result[1],  # action
                    'reason': klm_result[2],  # enhanced_reason
                    'variant_name': klm_result[3],  # selected_variant_name
                    'indicators': klm_indicators,
                    'market_data': market_data
                }
                logging.debug(f"KLM ensemble: {klm_result[1]} {klm_result[0]} - {klm_result[2]} [{klm_result[3]}]")
            except Exception as e:
                logging.error(f"Error running KLM ensemble: {e}")
                strategy_signals[StrategyType.KLM] = {
                    'symbol': 'BIL',
                    'action': ActionType.HOLD.value,
                    'reason': f"KLM ensemble error: {e}",
                    'variant_name': 'ERROR',
                    'indicators': {},
                    'market_data': {}
                }
        
        # Create consolidated portfolio allocation
        for strategy_type, signal_data in strategy_signals.items():
            if signal_data['action'] == ActionType.BUY.value:
                # Skip strategies not in our allocation (e.g., KLM-only portfolio)
                if strategy_type not in self.strategy_allocations:
                    continue
                strategy_allocation = self.strategy_allocations[strategy_type]
                
                # Handle portfolio vs single symbol signals
                symbol_or_allocation = signal_data['symbol']
                
                if isinstance(symbol_or_allocation, dict):
                    # Multi-asset allocation (e.g., from TECL strategy {'UVXY': 0.25, 'BIL': 0.75})
                    for symbol, weight in symbol_or_allocation.items():
                        total_weight = strategy_allocation * weight
                        if symbol in consolidated_portfolio:
                            consolidated_portfolio[symbol] += total_weight
                        else:
                            consolidated_portfolio[symbol] = total_weight
                elif symbol_or_allocation in ['NUCLEAR_PORTFOLIO', 'BEAR_PORTFOLIO', 'UVXY_BTAL_PORTFOLIO']:
                    # Named multi-asset portfolio signal - get actual allocations
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
                    symbol = symbol_or_allocation
                    if symbol in consolidated_portfolio:
                        consolidated_portfolio[symbol] += strategy_allocation
                    else:
                        consolidated_portfolio[symbol] = strategy_allocation
        
        # Note: Position tracking should only happen when trades are actually executed
        # Signal generation should not create position records
        
        logging.debug(f"Consolidated portfolio: {consolidated_portfolio}")
        return strategy_signals, consolidated_portfolio
    
    def _get_nuclear_portfolio_allocation(self, signal_data: Dict) -> Dict[str, float]:
        """Extract portfolio allocation from Nuclear strategy signal"""
        indicators = signal_data.get('indicators', {})
        market_data = signal_data.get('market_data', {})
        
        if signal_data['symbol'] == 'NUCLEAR_PORTFOLIO':
            # Bull market nuclear portfolio - extract actual weights from strategy engine
            portfolio = self.nuclear_engine.strategy.get_nuclear_portfolio(indicators, market_data)
            return {symbol: data['weight'] for symbol, data in portfolio.items()}
        
        elif signal_data['symbol'] == 'BEAR_PORTFOLIO':
            # Bear market portfolio - extract from the combination logic using inverse volatility
            try:
                # Get the two bear subgroup signals
                bear1_signal = self.nuclear_engine.strategy.bear_subgroup_1(indicators)
                bear2_signal = self.nuclear_engine.strategy.bear_subgroup_2(indicators)
                bear1_symbol = bear1_signal[0]
                bear2_symbol = bear2_signal[0]
                
                # If both strategies recommend the same symbol, use 100% allocation
                if bear1_symbol == bear2_symbol:
                    return {bear1_symbol: 1.0}
                
                # Otherwise, use inverse volatility weighting to combine them  
                bear_portfolio = self.nuclear_engine.strategy.combine_bear_strategies_with_inverse_volatility(
                    bear1_symbol, bear2_symbol, indicators
                )
                
                if bear_portfolio:
                    return {symbol: data['weight'] for symbol, data in bear_portfolio.items()}
                
                # Fallback to equal weights if calculation fails
                logging.warning("Bear portfolio calculation failed, using fallback allocation")
                return {bear1_symbol: 0.6, bear2_symbol: 0.4}
                
            except Exception as e:
                logging.error(f"Error calculating bear portfolio allocation: {e}")
                # Safe fallback - single defensive position
                return {'SQQQ': 1.0}
        
        elif signal_data['symbol'] == 'UVXY_BTAL_PORTFOLIO':
            # Volatility hedge portfolio - these are the standard weights used by the strategy
            # This could be enhanced to be dynamic based on market conditions if needed
            return {'UVXY': 0.75, 'BTAL': 0.25}
        
        return {}
    
    def _get_strategy_portfolio_allocation(self, signal_data: Dict, strategy_type: StrategyType) -> Dict[str, float]:
        """Extract portfolio allocation from any strategy signal"""
        if strategy_type == StrategyType.TECL:
            # Handle both single symbol and multi-asset allocations from TECL strategy
            symbol_or_allocation = signal_data['symbol']
            
            if isinstance(symbol_or_allocation, dict):
                # Multi-asset allocation (e.g., {'UVXY': 0.25, 'BIL': 0.75})
                return symbol_or_allocation
            else:
                # Single symbol allocation
                return {symbol_or_allocation: 1.0}
        
        return {}
    
    def _update_position_tracking(self, strategy_signals: Dict[StrategyType, Any], 
                                consolidated_portfolio: Dict[str, float]):
        """
        Update position tracking with current strategy positions
        
        WARNING: This method should ONLY be called when trades are actually executed,
        not during signal generation. Signal generation should not create position records.
        Position tracking should be handled by the StrategyOrderTracker in the execution layer.
        """
        logging.warning("_update_position_tracking called - this should only happen during trade execution")
        try:
            new_positions = {strategy: [] for strategy in StrategyType}
            
            for strategy_type, signal_data in strategy_signals.items():
                if signal_data['action'] == ActionType.BUY.value:
                    strategy_allocation = self.strategy_allocations[strategy_type]
                    
                    # Create position record for each symbol this strategy wants to hold
                    for symbol, total_weight in consolidated_portfolio.items():
                        # Calculate this strategy's contribution to this position
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
            
            # Position tracking between runs is disabled
            logging.debug("Position tracking disabled - not saving positions")
            
        except Exception as e:
            logging.error(f"Error updating position tracking: {e}")
    
    def get_strategy_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of each strategy's recent performance and current positions"""
        # Position tracking between runs is disabled
        positions = {strategy: [] for strategy in StrategyType}
        
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
