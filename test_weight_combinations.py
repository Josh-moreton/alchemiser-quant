#!/usr/bin/env python3
"""
Quick test to verify the weight combination generation logic.
"""

def generate_weight_combinations():
    """
    Generate all weight combinations where:
    - Ticker 1 (LQQ3.L): 50%, 60%, 70%
    - Tickers 2 & 3: All 10% increment combinations that sum to remaining weight
    """
    combinations = []
    ticker1_weights = [0.50, 0.60, 0.70]
    
    for w1 in ticker1_weights:
        remaining = 1.0 - w1  # Weight left for tickers 2 and 3
        
        # Generate all 10% increment combinations for tickers 2 and 3
        steps = int(remaining / 0.10)  # Number of 10% steps in remaining weight
        
        for i in range(steps + 1):
            w2 = i * 0.10
            w3 = remaining - w2
            
            # Only include if w3 is non-negative and is a multiple of 0.10
            if w3 >= 0 and abs(w3 - round(w3 / 0.10) * 0.10) < 0.001:
                w3 = round(w3 / 0.10) * 0.10  # Round to nearest 0.10
                if w3 >= 0:  # Final check
                    combinations.append((round(w1, 2), round(w2, 2), round(w3, 2)))
    
    return combinations

if __name__ == "__main__":
    combinations = generate_weight_combinations()
    print(f"Generated {len(combinations)} weight combinations:")
    print("\nSample combinations:")
    for i, (w1, w2, w3) in enumerate(combinations[:20]):  # Show first 20
        print(f"{i+1:2d}. LQQ3: {w1:.0%}, SGLN: {w2:.0%}, Third: {w3:.0%} (Sum: {w1+w2+w3:.1%})")
    
    if len(combinations) > 20:
        print(f"... and {len(combinations) - 20} more combinations")
    
    # Show breakdown by LQQ3 weight
    print(f"\nBreakdown by LQQ3 weight:")
    ticker1_weights = [0.50, 0.60, 0.70]
    for w1 in ticker1_weights:
        count = len([c for c in combinations if c[0] == w1])
        print(f"  LQQ3 {w1:.0%}: {count} combinations")
    
    # Verify all combinations sum to 100%
    invalid = [c for c in combinations if abs(sum(c) - 1.0) > 0.001]
    if invalid:
        print(f"\nWARNING: {len(invalid)} combinations don't sum to 100%!")
        for c in invalid:
            print(f"  {c} = {sum(c):.3f}")
    else:
        print(f"\n✓ All combinations sum to 100%")
