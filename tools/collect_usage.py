#!/usr/bin/env python3
"""Generate module usage CSVs and final README for CLI coverage."""

from __future__ import annotations

import csv
import json
import pathlib
from typing import Dict, List, Set

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "reports/cli-coverage"
COVERAGE_JSON = REPORT_DIR / "coverage.json"
INVENTORY_JSON = REPORT_DIR / "cli_inventory.json"
MATRIX_JSON = REPORT_DIR / "cli_matrix.json"
USED_CSV = REPORT_DIR / "used_modules.csv"
UNUSED_CSV = REPORT_DIR / "unused_modules.csv"
README_MD = REPORT_DIR / "README.md"


def load_case_modules() -> Dict[str, Set[str]]:
    flows = REPORT_DIR / "flows"
    mapping: Dict[str, Set[str]] = {}
    for file in flows.glob("*_modules.json"):
        case_id = file.stem.replace("_modules", "")
        mods = set(json.loads(file.read_text()))
        mapping[case_id] = mods
    return mapping


def collect_used_unused() -> tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    coverage = json.loads(COVERAGE_JSON.read_text())
    file_data = coverage.get("files", {})
    case_modules = load_case_modules()

    all_py = [p for p in (REPO_ROOT / "the_alchemiser").rglob("*.py")]
    used_rows: List[Dict[str, str]] = []
    unused_rows: List[Dict[str, str]] = []

    for path in all_py:
        rel = path.relative_to(REPO_ROOT)
        stats = file_data.get(str(rel)) or file_data.get(str(path))
        commands = [case for case, mods in case_modules.items() if str(rel) in mods]
        if stats and stats["summary"]["covered_lines"] > 0:
            row = {
                "file": str(rel),
                "lines_covered": str(stats["summary"]["covered_lines"]),
                "lines_total": str(stats["summary"]["num_statements"]),
                "pct": f"{stats['summary']['percent_covered']:.1f}",
                "commands": ",".join(commands),
            }
            used_rows.append(row)
        else:
            reason = ""
            rel_str = str(rel)
            if "test" in rel_str:
                reason = "test-only"
            elif "docs" in rel_str or "example" in rel_str:
                reason = "documentation"
            else:
                reason = "production-unused"
            unused_rows.append({"file": rel_str, "rationale": reason})
    return used_rows, unused_rows


def write_csv(path: pathlib.Path, rows: List[Dict[str, str]], headers: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def build_readme(used: List[Dict[str, str]], unused: List[Dict[str, str]]) -> None:
    inventory = json.loads(INVENTORY_JSON.read_text())
    matrix = json.loads(MATRIX_JSON.read_text())
    coverage = json.loads(COVERAGE_JSON.read_text())
    total_pct = coverage["totals"]["percent_covered"]

    lines = ["# CLI Coverage Report", ""]
    lines.append("## Entry Points")
    for name, info in inventory.items():
        lines.append(f"- `{name}` → `{info['entrypoint']}`")
    lines.append("")

    lines.append("## Execution Matrix")
    for case in matrix:
        cmd = " ".join([inventory[case["entrypoint"]]["entrypoint"].split(":")[0].split(".")[-1], *case["args"]])
        lines.append(f"- **{case['id']}**: `{cmd}` – {case['reason']}")
    lines.append("")

    lines.append("## Coverage Summary")
    lines.append(f"Overall coverage: {total_pct:.1f}%")
    lines.append("See `coverage_summary.txt` for full details.")
    lines.append("")

    lines.append("## Module Usage")
    lines.append(f"- [Used modules]({USED_CSV.name})")
    lines.append(f"- [Unused modules]({UNUSED_CSV.name})")
    lines.append("")

    risky = [row["file"] for row in unused if row["rationale"] == "production-unused"]
    if risky:
        lines.append("## Risky gaps")
        for path in risky:
            lines.append(f"- {path}")
        lines.append("")

    lines.append("## Next actions")
    lines.append("- Review unused production modules for relevance or removal.")
    lines.append("- Expand tests to cover critical paths.")
    lines.append("")

    README_MD.write_text("\n".join(lines))


def main() -> None:
    used, unused = collect_used_unused()
    write_csv(USED_CSV, used, ["file", "lines_covered", "lines_total", "pct", "commands"])
    write_csv(UNUSED_CSV, unused, ["file", "rationale"])
    build_readme(used, unused)
    print("Module usage and README generated")


if __name__ == "__main__":
    main()
