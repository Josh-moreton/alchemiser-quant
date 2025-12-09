#!/usr/bin/env python3
"""Trace where alpaca is being imported from in the import chain."""

import sys

# Store the import chain
import_chain: list[str] = []
original_import = __builtins__.__import__


def tracing_import(name: str, *args, **kwargs):
    """Intercept imports and trace alpaca imports."""
    import_chain.append(name)
    
    if 'alpaca' in name.lower() and not name.startswith('_'):
        print(f"\n{'='*60}")
        print(f"ALPACA IMPORT DETECTED: {name}")
        print(f"Import chain (last 15):")
        for i, mod in enumerate(import_chain[-15:]):
            print(f"  {i+1}. {mod}")
        print(f"{'='*60}\n")
        
        # Print a proper traceback
        import traceback
        traceback.print_stack(limit=20)
        
        raise ImportError(f"BLOCKED: {name}")
    
    try:
        result = original_import(name, *args, **kwargs)
        return result
    finally:
        if import_chain and import_chain[-1] == name:
            import_chain.pop()


__builtins__.__import__ = tracing_import

import os
os.environ['MARKET_DATA_BUCKET'] = 'test-bucket'

try:
    print("Importing lambda_handler...")
    from the_alchemiser.strategy_v2.lambda_handler import lambda_handler
    print("\nSUCCESS: lambda_handler imported without alpaca!")
except ImportError as e:
    print(f"\nFAILED: {e}")
except Exception as e:
    print(f"\nUNEXPECTED ERROR: {type(e).__name__}: {e}")
