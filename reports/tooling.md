# Tooling Updates

## pyproject.toml
```toml
[tool.poetry.dependencies]
pydantic = ">=2.0.0"

[tool.mypy]
python_version = "3.12"
disallow_any_generics = true
no_implicit_optional = true
warn_unused_ignores = true
strict_equality = true

[tool.ruff.per-file-ignores]
"the_alchemiser/domain/**" = ["F401", "I001", "TCH003", "PD"]  # forbid pydantic in domain
"the_alchemiser/infrastructure/**" = []

[tool.ruff.lint.select]
select = ["E", "F", "I", "UP", "B"]
```

## Architecture Tests
```python
# tests/test_architecture.py
import importlib
import pkgutil

import pytest

DOMAIN_PREFIX = "the_alchemiser.domain"

@pytest.mark.parametrize("mod", [m.name for m in pkgutil.walk_packages(["the_alchemiser/domain"])])
def test_domain_has_no_pydantic(mod):
    module = importlib.import_module(f"{DOMAIN_PREFIX}.{mod}")
    for attr in dir(module):
        obj = getattr(module, attr)
        assert "pydantic" not in getattr(obj, "__module__", ""), "Domain code should not depend on pydantic"
```
