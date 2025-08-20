# Contributing

Thank you for considering a contribution to this project.

## Floating-point comparisons

Floating-point values must never be compared with `==` or `!=`.
Use tolerant helpers instead:

```python
from tests.utils.float_checks import assert_close

assert_close(actual, expected, rtol=1e-6, atol=0.0)
```

For arrays, prefer `numpy.testing.assert_allclose` or the `assert_array_close`
helper from `tests.utils.float_checks`.

A pre-commit hook enforces this rule. Run `pre-commit install` after
setting up the repository.
