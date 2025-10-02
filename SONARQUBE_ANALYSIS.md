# SonarQube Issue Analysis: schemas.py String Literal Duplication

## Issue Details
- **Issue ID**: AZmaUT-X-d0BvnYSZL6-
- **Severity**: CRITICAL
- **Rule**: python:S1192
- **Description**: Define a constant instead of duplicating this literal "Optional recipient email override" 3 times
- **File**: the_alchemiser/shared/events/schemas.py:303

## Analysis Results

### Current Implementation (Correct)

The code **already implements the correct solution** that SonarQube is requesting:

1. **Constant Definition** (in `the_alchemiser/shared/constants.py:35`):
   ```python
   RECIPIENT_OVERRIDE_DESCRIPTION = "Optional recipient email override"
   ```

2. **Import Statement** (in `the_alchemiser/shared/events/schemas.py:20`):
   ```python
   from ..constants import EVENT_TYPE_DESCRIPTION, RECIPIENT_OVERRIDE_DESCRIPTION
   ```

3. **Usage Locations** (all using the constant):
   - Line 302: `ErrorNotificationRequested.recipient_override`
   - Line 325: `TradingNotificationRequested.recipient_override`
   - Line 344: `SystemNotificationRequested.recipient_override`

### Verification Steps

1. **Grep Search**:
   ```bash
   grep -rn "Optional recipient email override" the_alchemiser/ --include="*.py"
   ```
   Result: Only found in `constants.py` where it's defined

2. **Python AST Analysis**:
   ```python
   # Parsed the AST and searched for the literal string
   # Result: String NOT found in AST (using constant instead)
   ```

3. **Linting (Ruff)**:
   ```bash
   poetry run ruff check the_alchemiser/shared/events/schemas.py
   ```
   Result: All checks passed!

4. **Type Checking (MyPy)**:
   ```bash
   poetry run mypy the_alchemiser/shared/events/schemas.py --config-file=pyproject.toml
   ```
   Result: Success: no issues found

### Conclusion

The SonarQube finding appears to be **outdated or a false positive**. The code already follows best practices by:
- Defining the string literal once as a constant
- Importing the constant where needed
- Using the constant in all locations (not the literal string)

**No code changes are required.** The implementation is already correct and follows the recommended pattern that SonarQube is suggesting.

### Recommendation

The SonarQube analysis should be re-run against the current codebase (commit a64f8718 or later) to update the findings. The issue was likely fixed in a previous commit and the analysis results need to be refreshed.
