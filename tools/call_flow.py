#!/usr/bin/env python3
"""Run a CLI command, capture call flow and touched modules."""

from __future__ import annotations

import inspect
import json
import os
import random
import sys
import time
from pathlib import Path
from types import FrameType
from typing import Any, Dict, List, Set
from unittest.mock import MagicMock

from typer.testing import CliRunner

# Repo root
ROOT = Path(__file__).resolve().parents[1]
FLOW_DIR = ROOT / "reports/cli-coverage/flows"

# Ensure root on sys.path for package imports
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Safety patches
# ---------------------------------------------------------------------------

def apply_patches() -> None:
    """Monkeypatch external side effects to safe stubs."""
    # Stub main entry to avoid trading/network
    try:
        import the_alchemiser.main as main_mod

        def fake_main(argv: list[str] | None = None) -> bool:
            return True

        main_mod.main = fake_main  # type: ignore[attr-defined]
    except Exception:
        pass

    # Stub TradingEngine for status command
    try:
        from the_alchemiser.application import trading_engine

        class DummyTE:
            def __init__(self, *a: Any, **k: Any) -> None:
                pass

            def get_account_info(self) -> Dict[str, Any]:
                return {"equity": 0.0}

        trading_engine.TradingEngine = DummyTE  # type: ignore
    except Exception:
        pass

    # Stub indicator validation components
    try:
        from the_alchemiser.infrastructure.validation import indicator_validator

        class DummyValidator:
            def __init__(self, *a: Any, **k: Any) -> None:
                self.strategy_symbols = {"core": ["SPY", "QQQ"]}

            def run_validation_suite(self, symbols: List[str], mode: str) -> Dict[str, int]:
                return {"failed_tests": 0}

            def generate_report(self, summary: Dict[str, int]) -> None:
                pass

            def save_results(self, path: str) -> None:
                pass

        indicator_validator.IndicatorValidationSuite = DummyValidator  # type: ignore
    except Exception:
        pass

    try:
        from the_alchemiser.infrastructure.secrets import secrets_manager as sm

        sm.secrets_manager.get_twelvedata_api_key = lambda: "DUMMY"  # type: ignore
    except Exception:
        pass

    # Patch subprocess.run to avoid external scripts
    import subprocess

    def dummy_run(*a: Any, **k: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(a, 0, stdout="", stderr="")

    subprocess.run = dummy_run  # type: ignore

    # Patch network libraries
    try:
        import requests

        def dummy_request(self, *a: Any, **k: Any):  # type: ignore[override]
            response = requests.Response()
            response.status_code = 200
            response._content = b"{}"
            return response

        requests.sessions.Session.request = dummy_request  # type: ignore
    except Exception:
        pass

    try:
        import boto3

        boto3.client = lambda *a, **k: MagicMock()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Call tree profiler
# ---------------------------------------------------------------------------

class CallTree:
    def __init__(self) -> None:
        self.tree: Dict[str, Set[str]] = {}
        self.docs: Dict[str, str] = {}
        self.modules: Set[str] = set()
        self.stack: List[str] = []

    def tracer(self, frame: FrameType, event: str, arg: Any) -> Any:
        if event == "call":
            filename = Path(frame.f_code.co_filename)
            try:
                rel = filename.relative_to(ROOT)
            except ValueError:
                return self.tracer
            if "the_alchemiser" not in rel.parts:
                return self.tracer
            module = str(rel)
            func = frame.f_code.co_name
            node = f"{module}:{func}"
            self.modules.add(module)
            if self.stack:
                parent = self.stack[-1]
                self.tree.setdefault(parent, set()).add(node)
            self.stack.append(node)
            # Docstring first line
            mod = inspect.getmodule(frame)
            obj = getattr(mod, func, None) if mod else None
            if obj:
                doc = inspect.getdoc(obj)
                if doc:
                    self.docs[node] = doc.splitlines()[0]
        elif event == "return":
            if self.stack:
                self.stack.pop()
        return self.tracer

    def render(self, root: str) -> str:
        lines: List[str] = [f"# Call flow for {root.split(':')[0]}"]

        def walk(node: str, depth: int = 0) -> None:
            doc = self.docs.get(node, "")
            prefix = "  " * depth + f"- {node}"
            if doc:
                prefix += f" - {doc}"
            lines.append(prefix)
            for child in sorted(self.tree.get(node, [])):
                walk(child, depth + 1)

        walk(root)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: call_flow.py <case_id> [args...]")
    case_id = sys.argv[1]
    cli_args = sys.argv[2:]

    FLOW_DIR.mkdir(parents=True, exist_ok=True)
    flow_file = FLOW_DIR / f"{case_id}.md"
    modules_file = FLOW_DIR / f"{case_id}_modules.json"

    # Deterministic behaviour
    random.seed(0)
    time.time = lambda: 0.0  # type: ignore

    apply_patches()

    ct = CallTree()
    sys.setprofile(ct.tracer)
    from the_alchemiser.interface.cli.cli import app

    result = CliRunner().invoke(app, cli_args)
    sys.setprofile(None)

    if ct.stack:
        root_node = ct.stack[0]
    else:
        root_node = "root"

    flow_file.write_text(ct.render(root_node))
    modules_file.write_text(json.dumps(sorted(ct.modules)))

    if result.exit_code != 0:
        # Print output to help debugging but exit gracefully
        sys.stderr.write(result.output)
    sys.exit(0)


if __name__ == "__main__":
    main()
