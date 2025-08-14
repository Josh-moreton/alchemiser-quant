#!/usr/bin/env python3
"""Generate an inventory of all CLI entrypoints and their commands/options."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import pathlib
import sys
import types
from typing import Any, Dict, List

import click
import tomllib

# Output path
REPORT_PATH = pathlib.Path("reports/cli-coverage/cli_inventory.json")

# Ensure repository root on sys.path
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def load_entrypoints() -> Dict[str, str]:
    """Discover console entrypoints from pyproject.toml and setup.cfg/setup.py."""
    entrypoints: Dict[str, str] = {}

    pyproject = pathlib.Path("pyproject.toml")
    if pyproject.exists():
        data = tomllib.loads(pyproject.read_text())
        entrypoints.update(
            data.get("tool", {})
            .get("poetry", {})
            .get("scripts", {})
        )
        entrypoints.update(
            data.get("project", {}).get("scripts", {})
        )

    setup_cfg = pathlib.Path("setup.cfg")
    if setup_cfg.exists():
        import configparser

        cfg = configparser.ConfigParser()
        cfg.read(setup_cfg)
        if cfg.has_section("options.entry_points") and cfg.has_option(
            "options.entry_points", "console_scripts"
        ):
            lines = cfg.get("options.entry_points", "console_scripts").splitlines()
            for line in lines:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                name, target = [part.strip() for part in line.split("=")]
                entrypoints[name] = target

    setup_py = pathlib.Path("setup.py")
    if setup_py.exists():
        import re

        text = setup_py.read_text()
        m = re.search(r"entry_points=\{\s*'console_scripts':\s*\[(.*?)\]", text, re.S)
        if m:
            items = [i.strip().strip("'") for i in m.group(1).split(",") if i.strip()]
            for item in items:
                if "=" in item:
                    name, target = [p.strip() for p in item.split("=")]
                    entrypoints[name] = target

    return entrypoints


def parse_click_command(cmd: click.BaseCommand) -> Dict[str, Any]:
    """Recursively parse a Click command into a serialisable structure."""
    command_info: Dict[str, Any] = {
        "help": cmd.help or "",
        "options": [],
        "commands": {},
    }

    # Options
    for param in cmd.params:
        if not isinstance(param, click.Option):
            continue
        opt_info = {
            "name": param.name,
            "flags": list(param.opts) + list(param.secondary_opts),
            "type": getattr(param.type, "name", str(param.type)),
            "choices": getattr(param.type, "choices", None),
            "default": param.default,
            "required": param.required,
            "help": param.help or "",
        }
        command_info["options"].append(opt_info)

    # Subcommands
    if isinstance(cmd, click.Group):
        for name, sub in cmd.commands.items():
            command_info["commands"][name] = parse_click_command(sub)

    return command_info


def build_inventory() -> Dict[str, Any]:
    inventory: Dict[str, Any] = {}
    for name, target in load_entrypoints().items():
        module_name, obj_name = target.split(":")
        module = importlib.import_module(module_name)
        obj = getattr(module, obj_name)

        # Determine CLI type
        if hasattr(obj, "__class__") and obj.__class__.__name__ == "Typer":
            click_cmd = typer_to_click(obj)
        elif isinstance(obj, click.BaseCommand):
            click_cmd = obj
        elif isinstance(obj, argparse.ArgumentParser):
            click_cmd = argparse_to_click(obj)
        else:
            continue  # unsupported

        inventory[name] = {
            "entrypoint": target,
            "commands": {
                cmd_name: parse_click_command(cmd)
                for cmd_name, cmd in click_cmd.commands.items()
            },
        }
    return inventory


def typer_to_click(app: Any) -> click.Group:
    """Convert a Typer app to the underlying Click command."""
    import typer

    return typer.main.get_command(app)


def argparse_to_click(parser: argparse.ArgumentParser) -> click.Group:
    """Wrap an argparse parser in a Click Group for uniform processing."""
    group = click.Group()
    # argparse introspection is limited; treat top-level options only
    for action in parser._actions:  # type: ignore[attr-defined]
        if isinstance(action, argparse._SubParsersAction):
            for name, sub in action.choices.items():
                group.add_command(argparse_to_click(sub), name)
        else:
            # argparse options are not converted for inventory; skip
            pass
    return group


def main() -> None:
    inventory = build_inventory()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(inventory, indent=2))
    print(f"Wrote CLI inventory to {REPORT_PATH}")


if __name__ == "__main__":
    main()
