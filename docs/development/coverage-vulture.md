# Coverage & Vulture Plan

This guide explains how to measure test coverage with **coverage.py** and how to detect unreachable code with **vulture**.

## 1. Install the tools

Add the packages to the development dependencies:

```bash
pip install coverage pytest-cov vulture
```

You can also include them in `pyproject.toml` under `[project.optional-dependencies.dev]` for consistent development environments.

## 2. Running Coverage

Run the test suite with coverage enabled:

```bash
pytest --cov=the_alchemiser --cov-report=term-missing --cov-report=html
```

This produces an HTML report in `htmlcov/` and prints a summary of untested lines in the terminal. Open `htmlcov/index.html` in your browser to inspect detailed results.

## 3. Running Vulture

Use vulture to locate unused code:

```bash
vulture the_alchemiser tests
```

Review the output and remove or refactor dead code. You can exclude files or directories with the `--exclude` option and adjust sensitivity with `--min-confidence`.

## 4. Makefile shortcuts

Add convenient commands to the Makefile:

```Makefile
coverage:
pytest --cov=the_alchemiser --cov-report=term-missing --cov-report=html

vulture:
vulture the_alchemiser tests
```

## 5. Continuous Integration

Extend the GitHub Actions workflow to generate coverage reports and optionally run vulture. Failing the build on vulture warnings helps keep the codebase clean.

## 6. Ongoing maintenance

- Aim for at least 90% coverage in critical modules.
- Run vulture regularly or as a pre-commit hook to catch unused code early.
- Revisit ignored warnings whenever functionality changes.

