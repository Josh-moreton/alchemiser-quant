"""Automated migration of print/logging calls to structured logging."""
from __future__ import annotations

import argparse
from pathlib import Path

import libcst as cst


class PrintTransformer(cst.CSTTransformer):
    def leave_Call(self, original: cst.Call, updated: cst.Call) -> cst.BaseExpression:
        if isinstance(updated.func, cst.Name) and updated.func.value == "print":
            args = updated.args
            msg = args[0].value if args else cst.SimpleString('""')
            extras = []
            for arg in args[1:]:
                key = "arg"
                if isinstance(arg.value, cst.Name):
                    key = arg.value.value
                extras.append(
                    cst.DictElement(cst.SimpleString(f'"{key}"'), arg.value)
                )
            extras.append(
                cst.DictElement(cst.SimpleString('"event"'), cst.SimpleString('"auto.migrated"'))
            )
            extra_dict = cst.Dict(extras)
            return cst.Call(
                func=cst.Attribute(cst.Name("logger"), cst.Name("info")),
                args=[cst.Arg(msg), cst.Arg(value=extra_dict, keyword=cst.Name("extra"))],
            )
        if (
            isinstance(updated.func, cst.Attribute)
            and isinstance(updated.func.value, cst.Name)
            and updated.func.value.value == "logging"
            and updated.func.attr.value in {"debug", "info", "warning", "error", "exception", "critical"}
        ):
            level = updated.func.attr.value
            args = updated.args
            msg = args[0].value if args else cst.SimpleString('""')
            extras = []
            for arg in args[1:]:
                if arg.keyword is None:
                    if isinstance(arg.value, cst.Name):
                        key = arg.value.value
                    else:
                        key = "arg"
                    extras.append(cst.DictElement(cst.SimpleString(f'"{key}"'), arg.value))
            extras.append(
                cst.DictElement(cst.SimpleString('"event"'), cst.SimpleString('"auto.migrated"'))
            )
            extra_dict = cst.Dict(extras)
            return cst.Call(
                func=cst.Attribute(cst.Name("logger"), cst.Name(level)),
                args=[cst.Arg(msg), cst.Arg(value=extra_dict, keyword=cst.Name("extra"))],
            )
        return updated


def migrate_file(path: Path) -> None:
    module = cst.parse_module(path.read_text())
    module = module.visit(PrintTransformer())
    path.write_text(module.code)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    for file in args.files:
        migrate_file(Path(file))
