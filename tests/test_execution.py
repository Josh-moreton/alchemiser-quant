#!/usr/bin/env python3
from execution_engine import BacktestRunner
import logging

logging.basicConfig(level=logging.WARNING)
runner = BacktestRunner('2024-11-01', '2024-11-15', 100000)
results = runner.run_backtest('market_close')
metrics = results['performance_metrics']

print('Execution Engine Test Results:')
print(f'Return: {metrics["total_return"]:.2%}')
print(f'Trades: {metrics["number_of_trades"]}')
print(f'Value: ${metrics["current_value"]:,.0f}')
print(f'Costs: ${metrics["total_costs"]:.2f}')
