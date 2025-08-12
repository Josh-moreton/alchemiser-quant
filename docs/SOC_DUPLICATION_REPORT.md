# Exec Summary
1. **Monolithic modules dominate** – `trading_engine.py` (1178 lines), `data_provider.py` (1120), and `error_handler.py` (972) violate the “single responsibility” principle and hide cross‑layer concerns
2. **HTTP and AWS calls buried in domain services** (`AccountService` pulls `requests`; `S3Handler` instantiates `boto3` clients) coupling core logic to infrastructure
3. **Randomness and time leaked** – retry logic seeds `random.random()` and `datetime.now()` inside domain code, making behaviour non‑deterministic and hard to test
4. **Duplicate P&L logic** – closed‑position calculation repeated in two providers, risking drift
5. **Near‑identical strategy variants** – KLM worker variants copy/paste evaluation logic with minor tweaks
6. **Bloated email templates** duplicate HTML snippets, inflating maintenance cost
7. **Multiple order representations** (TypedDict, dataclass, Pydantic model) cause mapping churn and type conflicts
8. **Vulture flags dead code** – unused CLI commands and config accessors clutter public API
9. **Mypy catches 177 type errors** – missing stubs and unchecked decorators undermine static guarantees
10. **Tests duplicate setup** – repeated blocks in `test_refactored_services.py` and `test_portfolio.py` reduce confidence in fixture reuse

**Quick wins (≤2h)**  
- Extract shared closed‑position P&L helper and reuse in both data providers.  
- Move `random.random`/`datetime.now` to injectable utilities.  
- Delete vulture‑reported dead CLI commands.

**Medium (≤2d)**  
- Introduce `HttpClient` and `S3Port` interfaces; inject into services.  
- Consolidate order models into single `OrderModel` (Pydantic) and update mappers/tests.  
- Factor common KLM variant logic into `BaseKLMVariant`.

**Heavy (≤2w)**  
- Split `trading_engine.py`, `data_provider.py`, and `error_handler.py` into focused modules.  
- Rebuild email templates with Jinja partials.  
- Establish typed settings module and remove scattered `open()`/path logic.

---

# Layering & Imports
### Package tree (top 10 by LOC)
```
4286 utils
3939 execution
3205 core
3059 core/trading
2610 core/data
2603 core/trading/klm_workers
2132 core/ui/email/templates
1747 core/services
1030 tracking
660  core/models
```


### Import cycles
`pydeps --show-cycles` reported **no cycles** (empty output)

### Unstable dependencies
- **CLI** imports almost everything but is only imported by `__main__`, giving high efferent but near‑zero afferent coupling.  
- **utils** package (4.2k LOC) is imported broadly, making downstream modules depend on volatile helpers.

### 4-layer map & violations
| Layer | Modules |
| --- | --- |
| **Domain** | `core/models`, `core/types`, `core/trading/*` |
| **Application / Services** | `execution/*`, `core/services/*`, `tracking/*` |
| **Infrastructure / Adapters** | `core/data/*`, `core/utils/*`, `core/logging`, `core/secrets`, `utils/*` |
| **Interface / CLI** | `cli.py`, `main.py`, `lambda_handler.py`, `core/ui/*` |

**Violations**
- `core/services/account_service` (domain/services) imports `requests` → **move HTTP calls behind adapter**
- `core/utils/s3_utils` used directly by `core/alerts/alert_service` (domain) → **extract S3Port and inject**
- `tracking/strategy_order_tracker` writes timestamps (`datetime.now`) → **inject Clock**

**One-line fixes**
- `core/services/account_service.py:11 → requests` – *extract port* (`HttpClient`), inject into service.
- `core/alerts/alert_service.py:222 → core/utils/s3_utils` – *invert dependency* via `AlertLogger` interface.
- `tracking/strategy_order_tracker.py:67 → datetime.now` – *inject clock*.

---

# Duplications
| Canonical name | Duplicates (file:line) | Similarity | Proposed location | Safe replacement steps |
| --- | --- | --- | --- | --- |
| `calculate_closed_positions` | `core/data/data_provider.py:1041` ↔ `core/data/unified_data_provider_v2.py:443` | ~90% | `core/data/pnl_utils.py` | Extract function, import in both providers. |
| `evaluate_single_popped_kmlm` | KLM variants `830_21.py:33` ↔ `variant_nova.py:35` ↔ `520_22.py` | ~85% | `core/trading/klm_workers/base_klm_variant.py` | Implement once, let variants override deltas. |
| `render_orders_table` | `core/ui/email/templates/performance.py:21` x4 blocks | ~80% | `core/ui/email/partials.py` | Replace inline HTML with function call. |
| `StrategyOrder.from_data` timestamp logic | `tracking/strategy_order_tracker.py:60` ↔ other factory methods | ~80% | `tracking/factories.py` | Create shared builder. |
| Test setup blocks | `tests/unit/test_refactored_services.py:174` ↔ `264` etc. | ~80% | `tests/conftest.py` | Factor repeated fixtures.

**Top‑5 diff-ready replacements**

1. **Closed P&L**  
   ```diff
- # repeated loop...
+ from the_alchemiser.core.data.pnl_utils import calculate_closed_positions
+ closed_positions = calculate_closed_positions(trades_by_symbol)
   ```
2. **KLM variant single-pop**  
   ```diff
- def _evaluate_single_popped_kmlm(...):
-     # duplicate body
+ from .common import evaluate_single_popped_kmlm
+ def _evaluate_single_popped_kmlm(...):
+     return evaluate_single_popped_kmlm(indicators)
   ```
3. **Email orders table**  
   ```diff
- orders_rows = ""
- for order in orders[:10]:
-     ...
-     orders_rows += f"""<tr>...</tr>"""
+ from ..partials import render_orders_table
+ orders_rows = render_orders_table(orders[:10])
   ```
4. **Timestamp factory**  
   ```diff
- timestamp=datetime.now(UTC).isoformat(),
+ timestamp=clock.now_iso(),
   ```
5. **Test fixtures**  
   ```diff
- sample_portfolio = {...}
- svc = Service(sample_portfolio)
+ @pytest.fixture
+ def sample_portfolio(): ...
+ def test_service(sample_portfolio): svc = Service(sample_portfolio)
   ```

---

# Cross-cutting Leaks
- **HTTP** – direct `requests.get` inside `AccountService`
- **AWS/S3** – `S3Handler` instantiated in core alert logging
- **File I/O** – `open("alert_config.json")` in `utils/config_utils`
- **Time** – `datetime.now()` scattered in tracking and dashboard utilities
- **Randomness** – jitter in `ErrorRecoveryManager` retry loop

*Ports/adapters*: introduce `HttpClient`, `S3Port`, `Clock`, and `Randomizer` interfaces; inject via constructor.

---

# Data Models
- **TypedDicts** – `OrderDetails`, `StrategySignal`, etc. in `core/types.py`
- **Dataclasses** – e.g., `StrategyOrder`, `StrategyPosition` in tracker
- **Pydantic models** – `ValidatedOrder` with strict fields
- **Conflicts** – multiple order representations (TypedDict ↔ dataclass ↔ Pydantic) lead to conversion churn.

*Recommendation*: centralise in `core/models/order.py` as a single Pydantic `OrderModel`; deprecate `OrderDetails` TypedDict and dataclass forms.

---

# Complexity & God Modules
| file:line | smell | extraction suggestion |
| --- | --- | --- |
| `execution/portfolio_rebalancer.py:122` | **F (69)** complexity | split into `fetch_positions`, `sell_phase`, `buy_phase` pure functions
| `core/data/data_provider.py:1041` | >100 lines loop | move closed‑position calc to helper
| `trading_engine.py` (1178 LOC) | god module | separate strategy orchestration, risk checks, and order routing
| `error_handler.py:300` | D (29) cyclomatic | extract `ErrorSummaryBuilder` class

---

# Config & Constants
- `.env` loading centralised in `core/config.py` but other modules read JSON files or hardcode paths (`utils/config_utils`, `alert_service`).  
- **Action**: create `settings.py` based on Pydantic settings; expose `load_settings()` and prohibit direct `open()`/S3 in domain code.

---

# Test Suite Changes
- Duplicated blocks in `test_refactored_services.py` and `test_portfolio.py`  
- **Move** repeated portfolio/account fixtures into `tests/conftest.py`.  
- **Add** adapter/port tests: `HttpClient`, `S3Port`, `Clock`, order mappers.

---

# Refactor Plan (3 phases)
### Phase 1 – Stabilise utilities (≤1w)
1. Extract `calculate_closed_positions`, `evaluate_single_popped_kmlm`, `render_orders_table`, `Clock`, `Randomizer`.  
2. Run `pytest tests/unit` and `mypy the_alchemiser`.  
**Metric**: duplicated tokens ↓ (jscpd report), mypy errors unchanged.  
**Back-out**: revert helper extractions.

### Phase 2 – Introduce ports/adapters (≤1w)
1. Define `HttpClient`, `S3Port`, `Clock` interfaces; inject into services/tracker.  
2. Add unit tests for adapters; update existing services.  
3. Run `pytest tests/integration` + `mypy`.  
**Metric**: no direct `requests`/`boto3`/`datetime.now` in domain packages.  
**Back-out**: restore direct calls.

### Phase 3 – Decompose god modules (≤2w)
1. Split `trading_engine`, `data_provider`, `error_handler` into submodules.  
2. Replace order representations with unified `OrderModel`.  
3. Run full `pytest`, `vulture`, `radon cc`, and import graph check (`pydeps --show-cycles`).  
**Metric**: modules >400 LOC ↓50%; radon complexity grade ≥C; cycles remain 0.  
**Back-out**: keep prior modules and mappings.

---

# Back-out & Metrics
- **Back-out**: revert git commit for each phase; configuration untouched.
- **Metrics to track**:  
  - `jscpd-report.json` duplicated lines and tokens.  
  - `pydeps` cycle count (expect 0).  
  - `radon cc -s -a the_alchemiser` average complexity.  
  - `mypy --strict` error count.  
  - `pytest` pass rate.

---

