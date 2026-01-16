#!/usr/bin/env python3
"""Test specific indicator configurations for failing strategies."""

import json
import subprocess
import sys

strategies = ['sisyphus_lowvol', 'blatant_tech', 'rains_concise_em', 'rains_em_dancer']

# Test configurations: (rsi, cumulative_return, moving_average)
configs = [
    ('RSI=T0, cumret=T0, MA=T0', {'rsi': True, 'cumulative_return': True, 'moving_average': True}),
    ('RSI=T1, cumret=T0, MA=T0', {'rsi': False, 'cumulative_return': True, 'moving_average': True}),
    ('RSI=T0, cumret=T1, MA=T0', {'rsi': True, 'cumulative_return': False, 'moving_average': True}),
    ('RSI=T1, cumret=T1, MA=T0', {'rsi': False, 'cumulative_return': False, 'moving_average': True}),
    ('RSI=T1, cumret=T1, MA=T1', {'rsi': False, 'cumulative_return': False, 'moving_average': False}),
]

for strat in strategies:
    print(f'\n===== {strat} =====')
    for label, cfg in configs:
        cmd = [
            'poetry', 'run', 'python', 'scripts/trace_strategy_routes.py',
            strat, '--policy', 'custom', '--indicator-config', json.dumps(cfg)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='/Users/joshmoreton/GitHub/alchemiser-quant')
        try:
            data = json.loads(result.stdout)
            alloc = data.get('allocation', {})
            symbols = sorted([s for s, w in alloc.items() if w > 0.001])
            weights = ' + '.join(f'{s}:{alloc[s]*100:.0f}%' for s in symbols)
            print(f'  {label}: {weights}')
        except Exception as e:
            print(f'  {label}: ERROR - {e}')
            if result.stderr:
                print(f'    stderr: {result.stderr[:200]}')
