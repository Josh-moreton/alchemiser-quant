#!/usr/bin/env python3
"""
Test the Hourly Execution Engine with Real Hourly Data
Analyze which hour of the day provides the best execution for nuclear strategy
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import pandas as pd

# Add the current directory to path
sys.path.append('/Users/joshua.moreton/Documents/GitHub/LQQ3')

from nuclear_backtest_framework import BacktestDataProvider
from nuclear_trading_bot import NuclearTradingBot
from hourly_execution_engine import HourlyExecutionEngine

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/Users/joshua.moreton/Documents/GitHub/LQQ3/hourly_test.log'),
            logging.StreamHandler()
        ]
    )

def test_hourly_execution():
    """Test the hourly execution engine"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Hourly Execution Engine Test")
    
    try:
        # Set up test parameters
        start_date = "2024-07-01"
        end_date = "2024-09-30"
        initial_capital = 100000
        
        logger.info(f"Test period: {start_date} to {end_date}")
        logger.info(f"Initial capital: ${initial_capital:,.2f}")
        
        # Initialize hourly engine
        hourly_engine = HourlyExecutionEngine(start_date, end_date, initial_capital)
        
        # Run hourly analysis
        logger.info("Running hourly execution analysis...")
        results = hourly_engine.test_all_execution_hours()
        
        # Display results
        logger.info("\n" + "="*60)
        logger.info("HOURLY EXECUTION ANALYSIS RESULTS")
        logger.info("="*60)
        
        hourly_results = results['results']
        for hour_type, result in hourly_results.items():
            if 'performance_metrics' in result:
                metrics = result['performance_metrics']
                total_return = metrics['total_return']
                final_value = metrics['current_value']
                logger.info(f"{hour_type:15s}: {total_return:+7.2%} (${final_value:,.2f})")
        
        # Best hour info
        best_hour = results['best_hour']
        best_return = results['best_return']
        
        logger.info(f"\nBest execution hour: {best_hour} with {best_return:+.2%} return")
        
        # Save detailed results
        results_file = f'/Users/joshua.moreton/Documents/GitHub/LQQ3/data/backtest_results/hourly_execution_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        import json
        # Convert results to JSON-serializable format
        serializable_results = {}
        for hour, result in hourly_results.items():
            if 'performance_metrics' in result:
                serializable_results[hour] = {
                    'final_value': result['performance_metrics']['current_value'],
                    'total_return': result['performance_metrics']['total_return'],
                    'num_trades': result['performance_metrics']['number_of_trades'],
                    'total_costs': result['performance_metrics']['total_costs'],
                    'used_hourly_data': result.get('used_hourly_data', False)
                }
        
        with open(results_file, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)
        
        logger.info(f"Detailed results saved to: {results_file}")
        
        return results
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

if __name__ == "__main__":
    results = test_hourly_execution()
    print("\nHourly execution test completed!")
    if results:
        print(f"Found {len(results['results'])} hour configurations tested")
        best_hour = results['best_hour']
        print(f"Best execution hour: {best_hour}")
