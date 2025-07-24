# Refactoring Plan: Organize `/core` by Function

### 1. Identify Functional Areas

Group files by their primary responsibility. Suggested categories:

- **data**: Data access, providers, and related utilities
- **indicators**: Technical indicator calculations
- **secrets**: Secrets and credentials management
- **logging**: Logging and log utilities
- **trading**: Trading logic, bots, and strategy engines
- **ui**: User interface formatting (CLI, Telegram, etc.)
- **utils**: General utilities (S3, common helpers, etc.)
- **alerts**: Alerting and notification services

### 2. Create Subfolders

For each category above, create a subfolder in `/core`:

```
the_alchemiser/core/
    data/
    indicators/
    secrets/
    logging/
    trading/
    ui/
    utils/
    alerts/
```

### 3. Move Files to Subfolders

Move each file into the appropriate subfolder. Example mapping:

- `data_provider.py` → `data/data_provider.py`
- `indicators.py` → `indicators/indicators.py`
- `secrets_manager.py` → `secrets/secrets_manager.py`
- `logging_utils.py` → `logging/logging_utils.py`
- `nuclear_trading_bot.py`, `tecl_trading_bot.py`, `strategy_engine.py`, `strategy_manager.py` → `trading/`
- `cli_formatter.py`, `telegram_formatter.py` → `ui/`
- `s3_utils.py`, `common.py` → `utils/`
- `alert_service.py` → `alerts/alert_service.py`

### 4. Update Imports

Update all import statements throughout the codebase to reflect the new structure. For example:

```python
from the_alchemiser.core.data.data_provider import UnifiedDataProvider
from the_alchemiser.core.indicators.indicators import TechnicalIndicators
from the_alchemiser.core.secrets.secrets_manager import SecretsManager
```

### 5. Add `__init__.py` Files

Add (or update) `__init__.py` in each new subfolder to ensure they are recognized as packages.

### 6. Test the Refactored Structure

- Run all tests to ensure imports and functionality work as expected.
- Fix any broken imports or relative path issues.

### 7. Update Documentation

- Update the README and any developer docs to reflect the new structure and import paths.

---

**Optional:**  

- If some files are very small or closely related, consider combining them into a single module within the subfolder.
- For large or complex modules, further subdivide as needed (e.g., `trading/engines/`, `trading/bots/`).

Let me know if you want a file-by-file mapping or want to proceed with the first steps!
