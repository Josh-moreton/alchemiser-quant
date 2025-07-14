#!/usr/bin/env python3
"""
Signal Analyzer - Phase 2 of Nuclear Backtest Implementation
Analyzes signal patterns and timing for the Nuclear Energy strategy
"""

import pandas as pd
import numpy as np
import datetime as dt
from typing import Dict, List, Tuple, Optional
import logging
from nuclear_backtest_framework import BacktestDataProvider, BacktestNuclearStrategy

class SignalAnalyzer:
    """Analyzes signal patterns and timing"""
    
    def __init__(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date
        self.data_provider = BacktestDataProvider(start_date, end_date)
        self.strategy = BacktestNuclearStrategy(self.data_provider)
        self.logger = logging.getLogger(__name__)
        
        # Download all data once
        self.all_data = self.data_provider.download_all_data(self.strategy.all_symbols)
        self.logger.info(f"Signal analyzer initialized with data for {len(self.all_data)} symbols")
    
    def generate_daily_signals(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """Generate signals for every trading day in the specified range"""
        
        # Use instance dates if not provided
        analysis_start = pd.Timestamp(start_date or self.start_date)
        analysis_end = pd.Timestamp(end_date or self.end_date)
        
        # Get trading days from SPY data
        if 'SPY' not in self.all_data:
            raise ValueError("SPY data not available for trading day calculation")
        
        spy_data = self.all_data['SPY']
        trading_days = spy_data.index[(spy_data.index >= analysis_start) & (spy_data.index <= analysis_end)]
        
        signals = []
        self.logger.info(f"Generating signals for {len(trading_days)} trading days...")
        
        for i, trade_date in enumerate(trading_days):
            try:
                # Evaluate strategy at this date
                signal, action, reason, indicators, market_data = self.strategy.evaluate_strategy_at_time(trade_date)
                
                signal_data = {
                    'date': trade_date,
                    'signal': signal,
                    'action': action,
                    'reason': reason,
                    'num_indicators': len(indicators),
                    'spy_price': indicators.get('SPY', {}).get('current_price', 0),
                    'spy_rsi_10': indicators.get('SPY', {}).get('rsi_10', 50),
                    'spy_ma_200': indicators.get('SPY', {}).get('ma_200', 0)
                }
                
                # Add nuclear portfolio details if applicable
                if signal == 'NUCLEAR_PORTFOLIO':
                    nuclear_portfolio = self.strategy.strategy_engine.get_nuclear_portfolio(indicators, market_data)
                    if nuclear_portfolio:
                        signal_data['nuclear_stocks'] = list(nuclear_portfolio.keys())
                        signal_data['nuclear_weights'] = [nuclear_portfolio[s]['weight'] for s in nuclear_portfolio.keys()]
                
                signals.append(signal_data)
                
                # Progress logging
                if (i + 1) % 20 == 0:
                    self.logger.info(f"Processed {i + 1}/{len(trading_days)} days")
                    
            except Exception as e:
                self.logger.warning(f"Failed to generate signal for {trade_date.date()}: {e}")
                continue
        
        self.logger.info(f"Generated {len(signals)} signals successfully")
        return signals
    
    def find_signal_changes(self, signals: List[Dict]) -> List[Dict]:
        """Identify when strategy changes allocation"""
        if len(signals) < 2:
            return []
        
        changes = []
        prev_signal = signals[0]
        
        for i in range(1, len(signals)):
            curr_signal = signals[i]
            
            # Check if signal actually changed
            signal_changed = (curr_signal['signal'] != prev_signal['signal'] or 
                             curr_signal['action'] != prev_signal['action'])
            
            # For nuclear portfolio, also check if the stocks changed
            if (curr_signal['signal'] == 'NUCLEAR_PORTFOLIO' and 
                prev_signal['signal'] == 'NUCLEAR_PORTFOLIO'):
                
                curr_stocks = set(curr_signal.get('nuclear_stocks', []))
                prev_stocks = set(prev_signal.get('nuclear_stocks', []))
                
                if curr_stocks != prev_stocks:
                    signal_changed = True
            
            if signal_changed:
                change_data = {
                    'date': curr_signal['date'],
                    'from_signal': prev_signal['signal'],
                    'to_signal': curr_signal['signal'],
                    'from_action': prev_signal['action'],
                    'to_action': curr_signal['action'],
                    'from_reason': prev_signal['reason'],
                    'to_reason': curr_signal['reason'],
                    'days_held': (curr_signal['date'] - prev_signal['date']).days,
                    'spy_price': curr_signal['spy_price'],
                    'spy_rsi_10': curr_signal['spy_rsi_10']
                }
                
                # Add portfolio change details
                if curr_signal['signal'] == 'NUCLEAR_PORTFOLIO':
                    change_data['new_nuclear_stocks'] = curr_signal.get('nuclear_stocks', [])
                if prev_signal['signal'] == 'NUCLEAR_PORTFOLIO':
                    change_data['old_nuclear_stocks'] = prev_signal.get('nuclear_stocks', [])
                
                changes.append(change_data)
            
            prev_signal = curr_signal
        
        return changes
    
    def analyze_signal_persistence(self, signals: List[Dict]) -> Dict:
        """Measure how long signals remain stable"""
        
        if not signals:
            return {}
        
        # Group consecutive signals
        signal_runs = []
        current_run = {
            'signal': signals[0]['signal'],
            'action': signals[0]['action'],
            'start_date': signals[0]['date'],
            'count': 1
        }
        
        for i in range(1, len(signals)):
            curr = signals[i]
            
            if (curr['signal'] == current_run['signal'] and 
                curr['action'] == current_run['action']):
                current_run['count'] += 1
            else:
                # End current run
                current_run['end_date'] = signals[i-1]['date']
                current_run['duration_days'] = (current_run['end_date'] - current_run['start_date']).days + 1
                signal_runs.append(current_run.copy())
                
                # Start new run
                current_run = {
                    'signal': curr['signal'],
                    'action': curr['action'],
                    'start_date': curr['date'],
                    'count': 1
                }
        
        # Don't forget the last run
        if signals:
            current_run['end_date'] = signals[-1]['date']
            current_run['duration_days'] = (current_run['end_date'] - current_run['start_date']).days + 1
            signal_runs.append(current_run)
        
        # Calculate statistics
        persistence_stats = {}
        
        for run in signal_runs:
            signal_key = f"{run['action']}_{run['signal']}"
            
            if signal_key not in persistence_stats:
                persistence_stats[signal_key] = {
                    'occurrences': 0,
                    'total_days': 0,
                    'durations': []
                }
            
            persistence_stats[signal_key]['occurrences'] += 1
            persistence_stats[signal_key]['total_days'] += run['duration_days']
            persistence_stats[signal_key]['durations'].append(run['duration_days'])
        
        # Calculate averages
        for signal_key, stats in persistence_stats.items():
            stats['avg_duration'] = stats['total_days'] / stats['occurrences']
            stats['min_duration'] = min(stats['durations'])
            stats['max_duration'] = max(stats['durations'])
            stats['median_duration'] = np.median(stats['durations'])
        
        return {
            'signal_runs': signal_runs,
            'persistence_stats': persistence_stats,
            'total_signals': len(signals),
            'total_changes': len(signal_runs) - 1,
            'avg_change_frequency_days': len(signals) / max(len(signal_runs), 1)
        }
    
    def get_signal_summary(self, signals: List[Dict]) -> Dict:
        """Get summary statistics of all signals"""
        
        if not signals:
            return {}
        
        # Count signal types
        signal_counts = {}
        action_counts = {}
        
        # Market condition tracking
        bull_market_days = 0
        bear_market_days = 0
        nuclear_portfolio_days = 0
        
        for signal in signals:
            # Count signals and actions
            signal_type = signal['signal']
            action_type = signal['action']
            
            signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
            
            # Market condition analysis
            spy_price = signal.get('spy_price', 0)
            spy_ma_200 = signal.get('spy_ma_200', 0)
            
            if spy_price > spy_ma_200:
                bull_market_days += 1
                if signal_type == 'NUCLEAR_PORTFOLIO':
                    nuclear_portfolio_days += 1
            else:
                bear_market_days += 1
        
        return {
            'total_days': len(signals),
            'signal_counts': signal_counts,
            'action_counts': action_counts,
            'bull_market_days': bull_market_days,
            'bear_market_days': bear_market_days,
            'nuclear_portfolio_days': nuclear_portfolio_days,
            'nuclear_portfolio_rate': nuclear_portfolio_days / max(bull_market_days, 1),
            'date_range': {
                'start': signals[0]['date'].strftime('%Y-%m-%d'),
                'end': signals[-1]['date'].strftime('%Y-%m-%d')
            }
        }
    
    def analyze_nuclear_portfolio_evolution(self, signals: List[Dict]) -> Dict:
        """Analyze how the nuclear portfolio allocation changes over time"""
        
        nuclear_signals = [s for s in signals if s['signal'] == 'NUCLEAR_PORTFOLIO']
        
        if not nuclear_signals:
            return {'message': 'No nuclear portfolio signals found'}
        
        # Track stock appearances
        stock_appearances = {}
        weight_evolution = {}
        
        for signal in nuclear_signals:
            nuclear_stocks = signal.get('nuclear_stocks', [])
            nuclear_weights = signal.get('nuclear_weights', [])
            
            for i, stock in enumerate(nuclear_stocks):
                # Count appearances
                if stock not in stock_appearances:
                    stock_appearances[stock] = 0
                    weight_evolution[stock] = []
                
                stock_appearances[stock] += 1
                
                # Track weight if available
                if i < len(nuclear_weights):
                    weight_evolution[stock].append({
                        'date': signal['date'],
                        'weight': nuclear_weights[i]
                    })
        
        # Calculate statistics
        total_nuclear_days = len(nuclear_signals)
        stock_stats = {}
        
        for stock, count in stock_appearances.items():
            stock_stats[stock] = {
                'appearances': count,
                'frequency': count / total_nuclear_days,
                'avg_weight': np.mean([w['weight'] for w in weight_evolution[stock]]) if weight_evolution[stock] else 0,
                'weight_std': np.std([w['weight'] for w in weight_evolution[stock]]) if len(weight_evolution[stock]) > 1 else 0
            }
        
        return {
            'total_nuclear_days': total_nuclear_days,
            'stock_appearances': stock_appearances,
            'stock_stats': stock_stats,
            'weight_evolution': weight_evolution,
            'most_frequent_stocks': sorted(stock_appearances.items(), key=lambda x: x[1], reverse=True)[:5]
        }

def test_signal_analyzer():
    """Test the signal analyzer"""
    
    # Test with October-December 2024 data
    analyzer = SignalAnalyzer('2024-10-01', '2024-12-31')
    
    print("=== NUCLEAR ENERGY SIGNAL ANALYSIS ===")
    print(f"Analysis Period: 2024-10-01 to 2024-12-31")
    print()
    
    # Generate signals for November only (subset for testing)
    print("Generating signals for November 2024...")
    signals = analyzer.generate_daily_signals('2024-11-01', '2024-11-30')
    
    # Basic summary
    summary = analyzer.get_signal_summary(signals)
    print(f"\n=== SIGNAL SUMMARY ===")
    print(f"Total Trading Days: {summary['total_days']}")
    print(f"Bull Market Days: {summary['bull_market_days']}")
    print(f"Bear Market Days: {summary['bear_market_days']}")
    print(f"Nuclear Portfolio Days: {summary['nuclear_portfolio_days']}")
    print(f"Nuclear Portfolio Rate: {summary['nuclear_portfolio_rate']:.1%}")
    
    print(f"\nSignal Distribution:")
    for signal, count in summary['signal_counts'].items():
        percentage = count / summary['total_days'] * 100
        print(f"  {signal}: {count} days ({percentage:.1f}%)")
    
    # Signal changes
    changes = analyzer.find_signal_changes(signals)
    print(f"\n=== SIGNAL CHANGES ===")
    print(f"Total Signal Changes: {len(changes)}")
    
    for i, change in enumerate(changes[:5]):  # Show first 5 changes
        print(f"\n{i+1}. {change['date'].strftime('%Y-%m-%d')}")
        print(f"   From: {change['from_action']} {change['from_signal']}")
        print(f"   To:   {change['to_action']} {change['to_signal']}")
        print(f"   Held: {change['days_held']} days")
        print(f"   SPY:  ${change['spy_price']:.2f} (RSI: {change['spy_rsi_10']:.1f})")
    
    # Persistence analysis
    persistence = analyzer.analyze_signal_persistence(signals)
    print(f"\n=== SIGNAL PERSISTENCE ===")
    print(f"Average Change Frequency: {persistence['avg_change_frequency_days']:.1f} days")
    
    print(f"\nTop Signal Types by Duration:")
    for signal_key, stats in list(persistence['persistence_stats'].items())[:5]:
        print(f"  {signal_key}:")
        print(f"    Occurrences: {stats['occurrences']}")
        print(f"    Avg Duration: {stats['avg_duration']:.1f} days")
        print(f"    Range: {stats['min_duration']}-{stats['max_duration']} days")
    
    # Nuclear portfolio analysis
    nuclear_analysis = analyzer.analyze_nuclear_portfolio_evolution(signals)
    if 'total_nuclear_days' in nuclear_analysis:
        print(f"\n=== NUCLEAR PORTFOLIO ANALYSIS ===")
        print(f"Nuclear Portfolio Active: {nuclear_analysis['total_nuclear_days']} days")
        
        print(f"\nMost Frequent Nuclear Stocks:")
        for stock, count in nuclear_analysis['most_frequent_stocks']:
            frequency = count / nuclear_analysis['total_nuclear_days'] * 100
            avg_weight = nuclear_analysis['stock_stats'][stock]['avg_weight'] * 100
            print(f"  {stock}: {count} days ({frequency:.1f}%), avg weight: {avg_weight:.1f}%")

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run test
    test_signal_analyzer()
