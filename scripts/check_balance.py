#!/usr/bin/env python3
"""Check bracket balance in a file."""
import sys

def check_balance(filename: str) -> bool:
    with open(filename, 'r') as f:
        content = f.read()
    
    stack: list[tuple[str, int]] = []
    pairs = {'(': ')', '[': ']', '{': '}'}
    closes = {')': '(', ']': '[', '}': '{'}
    
    for i, c in enumerate(content):
        if c in pairs:
            stack.append((c, i))
        elif c in closes:
            if not stack or stack[-1][0] != closes[c]:
                line = content[:i].count('\n') + 1
                col = i - content.rfind('\n', 0, i)
                print(f'Unmatched {c} at line {line}, col {col}')
                return False
            stack.pop()
    
    if stack:
        for c, i in stack:
            line = content[:i].count('\n') + 1
            col = i - content.rfind('\n', 0, i)
            print(f'Unclosed {c} at line {line}, col {col}')
        return False
    
    print('Balanced!')
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: check_balance.py <file>')
        sys.exit(1)
    sys.exit(0 if check_balance(sys.argv[1]) else 1)
