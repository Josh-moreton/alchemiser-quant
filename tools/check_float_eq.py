import ast
import pathlib
import sys

FLOAT_CONSTS = (ast.Constant,)


class FloatEqVisitor(ast.NodeVisitor):
    def __init__(self):
        self.bad = []

    def _has_float_literal(self, node):
        if isinstance(node, FLOAT_CONSTS) and isinstance(getattr(node, "value", None), float):
            return True
        return False

    def visit_Compare(self, node):
        comps = [node.left] + node.comparators
        if any(self._has_float_literal(c) for c in comps):
            if any(isinstance(op, ast.Eq | ast.NotEq) for op in node.ops):
                self.bad.append((node.lineno, node.col_offset))
        self.generic_visit(node)


def main(paths):
    ok = True
    for path in map(pathlib.Path, paths):
        if path.suffix != ".py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        v = FloatEqVisitor()
        v.visit(tree)
        for ln, col in v.bad:
            print(f"{path}:{ln}:{col}  avoid float equality; use pytest.approx/assert_allclose")
            ok = False
    sys.exit(1 if not ok else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
