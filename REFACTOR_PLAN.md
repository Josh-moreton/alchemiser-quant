# Refactor Plan: Move Project to `the_alchemiser/` Package Structure

This plan describes how to refactor the current codebase into a proper Python package structure under a new folder named `the_alchemiser`. The goal is to make the project pip-installable, improve maintainability, and follow Python best practices.

---

## 1. **Create the Package Directory**

- Create a new folder at the project root:  

  ```
  the_alchemiser/
  ```

- This will contain all source code (excluding tests, scripts, and documentation).

---

## 2. **Move All Core Source Files**

- Move all Python modules and submodules (except tests, scripts, and docs) into `the_alchemiser/`.
- This includes:
  - All `.py` files in the root (e.g., `main.py`, `lambda_handler.py`)
  - All files in `core/` and `execution/` subfolders
- The new structure should look like:

  ```
  the_alchemiser/
      __init__.py
      main.py
      lambda_handler.py
      core/
          __init__.py
          ...
      execution/
          __init__.py
          ...
  ```

- Update all import statements to use absolute imports from `the_alchemiser`.

---

## 3. **Update Imports for Package Structure**

- Change all relative imports (e.g., `from .config import Config`) to absolute imports (e.g., `from the_alchemiser.core.config import Config`).
- For cross-module imports, always use the full package path.
- Update all scripts, modules, and submodules accordingly.

---

## 4. **Move Tests to `tests/` Directory**

- Ensure all test files are in a top-level `tests/` directory (already present).
- Update imports in tests to use `the_alchemiser` as the root package.
- Example:

  ```python
  from the_alchemiser.core.tecl_strategy_engine import TECLStrategyEngine
  ```

---

## 5. **Move Scripts and CLI Tools**

- Move any standalone scripts (e.g., in `scripts/`) to a `scripts/` folder at the project root.
- These should import from `the_alchemiser` and not contain core logic.

---

## 6. **Move Documentation and Config Files**

- Keep documentation (`docs/`, `.md` files) and config files (`config.yaml`, `.env`, etc.) at the project root.
- Do not place documentation inside the package folder.

---

## 7. **Add `__init__.py` Files**

- Ensure every package and subpackage directory (including `the_alchemiser/`, `core/`, `execution/`) contains an `__init__.py` file.

---

## 8. **Update Entry Points**

- If `main.py` is the CLI entry point, ensure it is importable as `the_alchemiser.main`.
- Optionally, add a `console_scripts` entry point in `setup.py` or `pyproject.toml` for CLI usage.

---

## 9. **Update Project Metadata**

- Add or update `setup.py` and/or `pyproject.toml` to define `the_alchemiser` as the main package.
- Set the correct package directory in the configuration.

---

## 10. **Update Dockerfile and CI/CD**

- Update the Dockerfile to copy `the_alchemiser/` instead of loose files.
- Update any CI/CD scripts to use the new package structure.

---

## 11. **Test the Refactored Project**

- Run all tests to ensure imports and functionality work as expected.
- Test CLI and Lambda entry points.

---

## 12. **Remove Old Files**

- After verifying the refactor, remove old source files from the root and any obsolete folders.

---

## 13. **Example Final Structure**

```
/Users/joshmoreton/GitHub/The-Alchemiser/
│
├── the_alchemiser/
│   ├── __init__.py
│   ├── main.py
│   ├── lambda_handler.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── ...
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── ...
│
├── tests/
│   ├── test_config.py
│   ├── ...
│
├── scripts/
│   ├── build_and_push_lambda.sh
│   ├── ...
│
├── docs/
│   ├── ...
│
├── config.yaml
├── requirements.txt
├── Dockerfile
├── README.md
└── ...
```

---

## 14. **Checklist for the AI Agent**

- [ ] Create `the_alchemiser/` and move all source code inside.
- [ ] Update all imports to use absolute package paths.
- [ ] Ensure all `__init__.py` files are present.
- [ ] Move/verify tests in `tests/` and update imports.
- [ ] Move scripts to `scripts/` and update imports.
- [ ] Update Dockerfile, CI/CD, and entry points.
- [ ] Test the refactored project.
- [ ] Remove obsolete files.

---

**Follow this plan step-by-step to refactor the project into a proper Python package structure under `the_alchemiser/`.**
