# Refactor Plan for `cli_formatter.py`

## Current Issues
- ~430 lines of console-rendering code using the Rich library.
- Many functions build tables manually; some share similar patterns.
- File mixes low-level formatting logic with small data transformations.

## Goals
- Provide reusable Rich components for other modules.
- Reduce duplication in table construction.
- Improve naming and grouping of utilities.

## Proposed Modules & Files
- `ui/components.py` – library of reusable Rich table/panel constructors.
- `ui/formatters/portfolio.py` – functions specific to portfolio allocation and execution plans.
- `ui/formatters/common.py` – header/footer and generic helpers.

## Step-by-Step Refactor
1. **Identify Repeated Table Patterns**
   - Create helper functions like `make_table(columns: List[str]) -> Table` in `ui/components.py`.
   - Replace manual `Table(...)` creation in each formatter with these helpers.

2. **Split File by Domain**
   - Move `render_technical_indicators` and `render_strategy_signals` into `ui/formatters/technical.py`.
   - Move portfolio-related functions (`render_portfolio_allocation`, `render_target_vs_current_allocations`, `render_execution_plan`) into `ui/formatters/portfolio.py`.
   - Keep simple wrappers `render_header` and `render_footer` in `ui/formatters/common.py`.

3. **Provide Public API via `ui/__init__.py`**
   - Re-export commonly used functions so callers can `from the_alchemiser.core.ui import render_header`.

4. **Add Unit Tests**
   - Use Rich's `Console` recording feature to assert rendered output contains expected text.

## Rationale
- Modular formatters ease future updates to the console output style.
- Helper functions reduce repeated code for constructing tables.
- Smaller files with clear naming improve discoverability for developers.

