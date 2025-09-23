#!/usr/bin/env python3
"""Minimal DSL tests to verify core functionality before refactoring."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

# Test that we can import the core modules
try:
    # Test sexpr_parser functionality
    from the_alchemiser.strategy_v2.engines.dsl.sexpr_parser import SexprParser
    parser = SexprParser()
    
    # Test basic tokenization
    tokens = parser.tokenize("(asset \"TEST\")")
    print(f"✓ Tokenization works: {tokens}")
    
    # Test basic parsing
    ast = parser.parse("(asset \"TEST\")")
    print(f"✓ Parsing works: {ast.node_type}")
    
    print("All basic functionality tests passed!")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()