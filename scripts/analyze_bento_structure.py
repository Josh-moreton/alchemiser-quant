#!/usr/bin/env python3
"""Analyze the structure of bento_collection.clj."""

import re

with open('layers/shared/the_alchemiser/shared/strategies/bento_collection.clj') as f:
    content = f.read()

# Count opening and closing parens/brackets to find depth
depth = 0
groups_by_depth = {}
for i, c in enumerate(content):
    if c in '([':
        depth += 1
    elif c in ')]':
        depth -= 1
    
    # Print groups at various depths
    if content[i:i+6] == '(group':
        # Extract the group name
        name_match = re.search(r'"([^"]+)"', content[i:i+200])
        if name_match:
            name = name_match.group(1)[:50]
            if depth not in groups_by_depth:
                groups_by_depth[depth] = []
            groups_by_depth[depth].append(name)

print("Groups by depth:")
for d in sorted(groups_by_depth.keys()):
    print(f"\nDepth {d}: {len(groups_by_depth[d])} groups")
    for name in groups_by_depth[d][:5]:
        print(f"  - {name}")
    if len(groups_by_depth[d]) > 5:
        print(f"  ... and {len(groups_by_depth[d]) - 5} more")
