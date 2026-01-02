#!/usr/bin/env python3
"""Parse ftl_starburst to find groups in the filter.

Business Unit: Scripts | Status: current.
"""


def find_matching_bracket(content: str, start_pos: int) -> int:
    """Find the position of the matching closing bracket."""
    depth = 0
    i = start_pos
    while i < len(content):
        if content[i] == "[":
            depth += 1
        elif content[i] == "]":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def main() -> None:
    """Parse the strategy to find groups in the filter."""
    strategy_path = (
        "/Users/joshua.moreton/Documents/GitHub/alchemiser-quant/"
        "layers/shared/the_alchemiser/shared/strategies/ftl_starburst.clj"
    )
    with open(strategy_path) as f:
        content = f.read()

    # Find the filter on line 8
    filter_start = content.find("(filter")
    print(f"Filter starts at char pos: {filter_start}")

    # Find the opening bracket of the filter's portfolio list
    select_pos = content.find("(select-bottom 1)", filter_start)
    list_start = content.find("[", select_pos)
    print(f"Filter list starts at char pos: {list_start}")

    # Find the matching ]
    list_end = find_matching_bracket(content, list_start)
    print(f"Filter list ends at char pos: {list_end}")
    print(f"Filter list is {list_end - list_start} chars")

    # Extract the list content and find top-level groups
    list_content = content[list_start : list_end + 1]

    # Count top-level (group directives
    print("\nScanning for top-level groups in filter list...")
    depth = 0
    group_starts = []
    i = 0
    while i < len(list_content):
        if list_content[i] == "[":
            depth += 1
        elif list_content[i] == "]":
            depth -= 1
        elif list_content[i : i + 6] == "(group" and depth == 1:
            # Find the group name
            name_start = list_content.find('"', i)
            name_end = list_content.find('"', name_start + 1)
            group_name = list_content[name_start + 1 : name_end]
            short_name = group_name[:60] + "..." if len(group_name) > 60 else group_name
            group_starts.append((i, short_name))
        i += 1

    print(f"\nFound {len(group_starts)} top-level groups in the filter:")
    for idx, (pos, name) in enumerate(group_starts):
        line_num = content[: list_start + pos].count("\n") + 1
        print(f"  {idx + 1}. Line {line_num}: {name}")


if __name__ == "__main__":
    main()
