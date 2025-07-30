#!/usr/bin/env python3
"""
Test script to verify configuration and allocation display.
"""

from the_alchemiser.core.config import Config

def test_allocation_display():
    """Test allocation display matches config."""
    
    print("Testing Allocation Display...")
    
    # Get config 
    config = Config()
    allocations = config['strategy']['default_strategy_allocations']
    nuclear_pct = int(allocations['nuclear'] * 100)
    tecl_pct = int(allocations['tecl'] * 100)
    
    print(f"Config allocations: Nuclear {nuclear_pct}% / TECL {tecl_pct}%")
    
    # Test the display logic from main.py
    nuclear_positions = 1  # Simulate a position
    tecl_positions = 1     # Simulate a position
    
    strategy_summary = f"""NUCLEAR: {nuclear_positions} positions, {nuclear_pct}% allocation
TECL: {tecl_positions} positions, {tecl_pct}% allocation"""
    
    print("Display output:")
    print(strategy_summary)
    
    # Verify correct values
    assert nuclear_pct == 40, f"Expected 40% Nuclear, got {nuclear_pct}%"
    assert tecl_pct == 60, f"Expected 60% TECL, got {tecl_pct}%"
    
    print("\n✅ Allocation display test passed!")

if __name__ == "__main__":
    test_allocation_display()
