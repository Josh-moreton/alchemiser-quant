"""Debug weight-equal behavior.

Business Unit: debugging | Status: development.
"""
import sys
sys.path.insert(0, "/Users/joshmoreton/GitHub/alchemiser-quant/layers/shared")
sys.path.insert(0, "/Users/joshmoreton/GitHub/alchemiser-quant/functions/strategy_worker")

from decimal import Decimal
from pathlib import Path

from engines.dsl.sexpr_parser import SexprParser


def main() -> None:
    """Debug the weight-equal parsing."""
    # Test simple weight-equal with 3 children
    test_dsl = """
    (weight-equal
      [(asset "A" nil)
       (asset "B" nil)
       (asset "C" nil)])
    """
    
    parser = SexprParser()
    tokens = parser.tokenize(test_dsl)
    print("Tokens:", tokens[:20])
    
    ast = parser.parse(test_dsl)
    print("\n=== AST Structure ===")
    print(f"Root type: {ast.node_type}")
    print(f"Root children count: {len(ast.children) if ast.children else 0}")
    
    if ast.children:
        for i, child in enumerate(ast.children):
            print(f"  Child {i}: type={child.node_type}, value={child.value}")
            if child.children:
                print(f"    Has {len(child.children)} sub-children")
                for j, subchild in enumerate(child.children[:5]):
                    print(f"      Subchild {j}: type={subchild.node_type}, value={subchild.value}")
                    if subchild.children:
                        print(f"        Has {len(subchild.children)} sub-sub-children")
    
    # Now test with the actual DSL structure
    print("\n=== Testing weight-equal argument count ===")
    
    # This is the structure we have:
    # (weight-equal [(filter ...) (filter ...) (filter ...)])
    # vs what Composer might interpret as:
    # (weight-equal (filter ...) (filter ...) (filter ...))
    
    test_1 = "(weight-equal [(asset A nil) (asset B nil)])"
    test_2 = "(weight-equal (asset A nil) (asset B nil))"
    
    ast1 = parser.parse(test_1)
    ast2 = parser.parse(test_2)
    
    # Get the weight-equal function call
    we1_children = ast1.children[1:] if ast1.is_list() else []  # Skip symbol
    we2_children = ast2.children[1:] if ast2.is_list() else []
    
    print(f"\nStructure 1 - (weight-equal [a b]):")
    print(f"  args to weight-equal: {len(we1_children)}")
    for i, c in enumerate(we1_children):
        print(f"    arg {i}: type={c.node_type}, children={len(c.children) if c.children else 0}")
    
    print(f"\nStructure 2 - (weight-equal a b):")
    print(f"  args to weight-equal: {len(we2_children)}")
    for i, c in enumerate(we2_children):
        print(f"    arg {i}: type={c.node_type}, children={len(c.children) if c.children else 0}")


if __name__ == "__main__":
    main()
