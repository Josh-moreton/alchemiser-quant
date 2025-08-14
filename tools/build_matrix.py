#!/usr/bin/env python3
"""Build a reduced execution matrix for CLI coverage runs."""

from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List

MATRIX_PATH = pathlib.Path("reports/cli-coverage/cli_matrix.json")
INVENTORY_PATH = pathlib.Path("reports/cli-coverage/cli_inventory.json")

SKIP_BOOL_NAMES = {
    "verbose",
    "no-header",
    "quiet",
    "force",
    "verbose_validation",
    "verbose-validation",
}


def bool_case_id(base: str, flag: str) -> str:
    return f"{base}_{flag.replace('-', '_')}"


def build_matrix() -> List[Dict[str, Any]]:
    inventory = json.loads(INVENTORY_PATH.read_text())
    cases: List[Dict[str, Any]] = []

    for entrypoint, info in inventory.items():
        for cmd_name, cmd in info["commands"].items():
            base_args = [cmd_name]
            cases.append(
                {
                    "id": f"{cmd_name}_default",
                    "entrypoint": entrypoint,
                    "args": base_args,
                    "reason": "Baseline run with default options",
                }
            )

            for opt in cmd.get("options", []):
                opt_name = opt["name"].replace("_", "-")
                if opt_name in SKIP_BOOL_NAMES:
                    continue
                flags = opt["flags"]
                if opt["type"] in {"bool", "boolean"}:
                    flag = flags[0]
                    extra_args = base_args + [flag]
                    # Special handling for trade --live which requires --force to bypass prompt
                    if cmd_name == "trade" and opt_name == "live":
                        extra_args.append("--force")
                    cases.append(
                        {
                            "id": bool_case_id(cmd_name, opt_name),
                            "entrypoint": entrypoint,
                            "args": extra_args,
                            "reason": f"Exercise boolean flag {flag}",
                        }
                    )
                elif opt.get("choices"):
                    for choice in opt["choices"]:
                        extra_args = base_args + [flags[0], str(choice)]
                        cases.append(
                            {
                                "id": f"{cmd_name}_{opt_name}_{choice}",
                                "entrypoint": entrypoint,
                                "args": extra_args,
                                "reason": f"Test option {flags[0]}={choice}",
                            }
                        )
            # Manual cases for validate-indicators --mode
            if cmd_name == "validate-indicators":
                for mode in ["quick", "full"]:
                    cases.append(
                        {
                            "id": f"validate-indicators_mode_{mode}",
                            "entrypoint": entrypoint,
                            "args": [cmd_name, "--mode", mode],
                            "reason": f"Test mode {mode}",
                        }
                    )
    return cases


def main() -> None:
    cases = build_matrix()
    MATRIX_PATH.parent.mkdir(parents=True, exist_ok=True)
    MATRIX_PATH.write_text(json.dumps(cases, indent=2))
    print(f"Wrote execution matrix to {MATRIX_PATH}")


if __name__ == "__main__":
    main()
