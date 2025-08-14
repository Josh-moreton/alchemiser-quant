#!/usr/bin/env python3
"""Execute coverage for all CLI matrix cases and generate artefacts."""

from __future__ import annotations

import json
import pathlib
import subprocess

MATRIX_PATH = pathlib.Path("reports/cli-coverage/cli_matrix.json")
REPORT_DIR = pathlib.Path("reports/cli-coverage")
FLOWS_DIR = REPORT_DIR / "flows"


def run_case(case_id: str, args: list[str]) -> None:
    cmd = [
        "coverage",
        "run",
        "-p",
        "tools/call_flow.py",
        case_id,
        *args,
    ]
    subprocess.run(cmd, check=True)


def main() -> None:
    cases = json.loads(MATRIX_PATH.read_text())
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    FLOWS_DIR.mkdir(parents=True, exist_ok=True)

    subprocess.run(["coverage", "erase"], check=True)

    for case in cases:
        run_case(case["id"], case["args"])

    subprocess.run(["coverage", "combine"], check=True)
    subprocess.run(["coverage", "html", "-d", str(REPORT_DIR / "html")], check=True)
    subprocess.run(["coverage", "xml", "-o", str(REPORT_DIR / "coverage.xml")], check=True)
    subprocess.run(["coverage", "json", "-o", str(REPORT_DIR / "coverage.json")], check=True)
    with open(REPORT_DIR / "coverage_summary.txt", "w", encoding="utf-8") as f:
        subprocess.run(["coverage", "report"], check=True, text=True, stdout=f)

    print("Coverage run complete")


if __name__ == "__main__":
    main()
