"""Business Unit: utilities; Status: current.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path('.').resolve()
PY_FILES = [p for p in ROOT.rglob('*.py') if '.venv' not in p.parts]


def classify(path: str) -> str:
    l = path.lower()
    if 'strategy' in l:
        return 'strategy & signal generation'
    if 'portfolio' in l:
        return 'portfolio assessment & management'
    if any(t in l for t in ['trading', 'order', 'execution']):
        return 'order execution/placement'
    return 'utilities'


def status(path: str) -> str:
    l = path.lower()
    if any(t in l for t in ['example', 'legacy', 'deprecated']):
        return 'legacy'
    return 'current'


report = []

for p in PY_FILES:
    rel = str(p.relative_to(ROOT))
    bu = classify(rel)
    st = status(rel)
    src = p.read_text(encoding='utf-8')
    try:
        mod = ast.parse(src)
        classes = [n.name for n in mod.body if isinstance(n, ast.ClassDef)]
        funcs = [n.name for n in mod.body if isinstance(n, ast.FunctionDef)]
        existing_doc = ast.get_docstring(mod, clean=False) or ''
    except SyntaxError:
        classes, funcs, existing_doc = [], [], ''

    desc_parts = []
    if classes:
        desc_parts.append('Classes: ' + ', '.join(classes))
    if funcs:
        desc_parts.append('Functions: ' + ', '.join(funcs))
    desc = '; '.join(desc_parts)

    lines = src.splitlines()
    insert_idx = 0
    while insert_idx < len(lines) and lines[insert_idx].startswith('#'):
        insert_idx += 1
    start_idx = insert_idx
    end_idx = insert_idx
    if insert_idx < len(lines) and lines[insert_idx].startswith(('"""', "'''")):
        quote = '"""' if lines[insert_idx].startswith('"""') else "'''"
        first_line = lines[insert_idx]
        if first_line.strip().endswith(quote) and first_line.count(quote) >= 2:
            end_idx = insert_idx + 1
        else:
            j = insert_idx + 1
            while j < len(lines) and not lines[j].endswith(quote):
                j += 1
            if j < len(lines):
                end_idx = j + 1
        lines = lines[:start_idx] + lines[end_idx:]
    doc_lines = [f'Business Unit: {bu}; Status: {st}.']
    if existing_doc.strip():
        doc_lines.append('')
        doc_lines.extend(existing_doc.strip().splitlines())
    docstring = '"""' + "\n".join(doc_lines) + '\n"""'
    lines = lines[:start_idx] + [docstring] + lines[start_idx:]
    p.write_text("\n".join(lines) + "\n", encoding='utf-8')

    report.append({'file': rel, 'business_unit': bu, 'status': st, 'description': desc})

Path('BUSINESS_UNITS_REPORT.json').write_text(json.dumps(report, indent=2), encoding='utf-8')

md_lines = ["# Business Units Report", "", "| File | Business Unit | Status | Description |", "| --- | --- | --- | --- |"]
for r in report:
    md_lines.append(f"| {r['file']} | {r['business_unit']} | {r['status']} | {r['description']} |")
Path('BUSINESS_UNITS_REPORT.md').write_text("\n".join(md_lines) + "\n", encoding='utf-8')
print(f'Processed {len(report)} files')
