"""Pre-commit check for structured logging usage."""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Iterable

LOG_METHODS = {"debug", "info", "warning", "error", "exception", "critical"}


def _check_file(path: Path) -> list[str]:
    errors: list[str] = []
    tree = ast.parse(path.read_text(), filename=str(path))

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
            if isinstance(node.func, ast.Attribute):
                name = node.func.attr
                if name in LOG_METHODS:
                    extra_arg = next((k for k in node.keywords if k.arg == "extra"), None)
                    if not extra_arg or not isinstance(extra_arg.value, ast.Dict):
                        errors.append(f"{path}:{node.lineno} missing extra with event")
                    else:
                        keys = [k.s for k in extra_arg.value.keys if isinstance(k, ast.Constant)]
                        if "event" not in keys:
                            errors.append(f"{path}:{node.lineno} extra missing event key")
            if (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "logging"
                and node.func.attr == "basicConfig"
                and "logging/setup.py" not in str(path)
            ):
                errors.append(f"{path}:{node.lineno} basicConfig prohibited")
            self.generic_visit(node)

    Visitor().visit(tree)
    return errors


def main(paths: Iterable[str]) -> int:
    problems: list[str] = []
    for p in paths:
        problems.extend(_check_file(Path(p)))
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
