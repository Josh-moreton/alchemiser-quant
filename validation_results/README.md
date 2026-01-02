# Signal Validation Results

This directory stores CSV files from daily signal validation sessions against Composer.trade.

## Directory Contents

- `signal_validation_YYYY-MM-DD.csv` - Daily validation records
- `.gitignore` - Excludes CSV files from version control (they contain manual validation data)

## CSV Format

Each CSV file contains the following columns:

| Column | Description |
|--------|-------------|
| `validation_date` | Date of the trading session being validated (YYYY-MM-DD) |
| `session_id` | DynamoDB aggregation session ID |
| `strategy_name` | Strategy name (without .clj extension) |
| `dsl_file` | Strategy filename (with .clj extension) |
| `matches` | Validation result: `yes`, `no`, or `skip` |
| `notes` | Optional notes from validator |
| `validated_at` | ISO timestamp when validation was performed |

## Example Record

```csv
validation_date,session_id,strategy_name,dsl_file,matches,notes,validated_at
2026-01-02,workflow-abc123,nuclear_feaver,nuclear_feaver.clj,yes,Perfect match,2026-01-02T15:30:00Z
2026-01-02,workflow-abc123,beam_chain,beam_chain.clj,no,Small allocation difference,2026-01-02T15:32:00Z
```

## Usage

See [scripts/validate_signals.py](../scripts/validate_signals.py) for the validation tool.

Quick start:
```bash
# Validate today's dev run
python scripts/validate_signals.py

# Validate specific date
python scripts/validate_signals.py --date 2026-01-02

# Resume interrupted validation
python scripts/validate_signals.py  # Will skip already-validated strategies
```
