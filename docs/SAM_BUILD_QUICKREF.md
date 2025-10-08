# SAM Build Configuration - Quick Reference

## At a Glance

### Current Configuration (v2.16.5)

```yaml
# template.yaml
TradingSystemFunction:
  CodeUri: the_alchemiser/          # ← Application directory only
  Handler: lambda_handler.lambda_handler  # ← Relative to CodeUri
```

### What Gets Included

✅ **All Python code** in `the_alchemiser/` (automatically)
✅ **Strategy files**: `strategy_v2/strategies/*.clj` (explicit include)
✅ **Config files**: `config/*.json` (explicit include)

### What Gets Excluded

❌ **Cache files**: `__pycache__/`, `*.pyc`, `*.pyo`
❌ **Build artifacts**: `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
❌ **IDE files**: `.vscode/`, `.editorconfig`
❌ **Documentation**: `*.md` files

### Root Level (Ignored by Default)

🚫 Never scanned (CodeUri = `the_alchemiser/`):
- `tests/` - Test files
- `docs/` - Documentation
- `scripts/` - Deployment scripts
- `README.md`, `CHANGELOG.md` - Project docs
- `pyproject.toml`, `poetry.lock` - Build config
- `logo.png` - Media files

## Common Commands

### Build
```bash
# Clean build
rm -rf .aws-sam
sam build --use-container --parallel

# Validate template
sam validate --region us-east-1 --lint

# Check package size
du -sh .aws-sam/build/TradingSystemFunction
du -sh .aws-sam/build/DependenciesLayer
```

### Verify
```bash
# Check handler file location
ls -la .aws-sam/build/TradingSystemFunction/lambda_handler.py

# Verify includes
ls -la .aws-sam/build/TradingSystemFunction/config/
ls -la .aws-sam/build/TradingSystemFunction/strategy_v2/strategies/

# Check exclusions (should be empty)
find .aws-sam/build/TradingSystemFunction -name "*.md"
find .aws-sam/build/TradingSystemFunction -name "test_*.py"
find .aws-sam/build/TradingSystemFunction -name "*.pyc"
```

### Deploy
```bash
# Dev environment
./scripts/deploy.sh dev

# Production environment
./scripts/deploy.sh prod
```

## Package Structure

```
/var/task/ (Lambda runtime)
├── lambda_handler.py           # Entry point
├── __init__.py
├── __main__.py
├── main.py
├── config/
│   ├── strategy.dev.json       # ✅ Included (explicit)
│   └── strategy.prod.json      # ✅ Included (explicit)
├── strategy_v2/
│   └── strategies/
│       ├── 1-KMLM.clj          # ✅ Included (explicit)
│       ├── 2-Nuclear.clj       # ✅ Included (explicit)
│       ├── 5-Coin.clj          # ✅ Included (explicit)
│       └── ...                 # ✅ All .clj files
├── portfolio_v2/               # ✅ Included (Python)
├── execution_v2/               # ✅ Included (Python)
├── orchestration/              # ✅ Included (Python)
├── notifications_v2/           # ✅ Included (Python)
└── shared/                     # ✅ Included (Python)
```

## Troubleshooting

| Problem | Check | Fix |
|---------|-------|-----|
| Import error | Handler path in template | Should be `lambda_handler.lambda_handler` |
| Missing .clj files | Include patterns | Add `**/*.clj` to Include |
| Missing .json files | Include patterns | Add `config/*.json` to Include |
| Package too large | Exclusions working | Check for unexpected files in build |
| Build fails | Docker running | Run `docker info` |

## File Locations

| File | Purpose | Primary Control |
|------|---------|-----------------|
| `template.yaml` | SAM template | CodeUri, Handler, BuildProperties |
| `.samignore` | Security exclusions | .env, .aws/, .git/ |
| `scripts/deploy.sh` | Deployment script | Build & deploy automation |
| `dependencies/requirements.txt` | Lambda Layer | Production dependencies |

## Quick Checks

### Is my file included?

1. **Is it in `the_alchemiser/`?**
   - No → Never included (outside CodeUri)
   - Yes → Continue to step 2

2. **Is it Python code (`.py`)?**
   - Yes → Included (unless in Exclude list)
   - No → Continue to step 3

3. **Is it in Include list?**
   - `**/*.clj` → Yes, included
   - `config/*.json` → Yes, included
   - Other → Not included

4. **Is it in Exclude list?**
   - Cache/build artifacts → Excluded
   - IDE files → Excluded
   - `*.md` → Excluded

### Common Pitfalls

❌ **DON'T**: Put CodeUri as `./` (scans entire repo)
✅ **DO**: Use `the_alchemiser/` (scans app only)

❌ **DON'T**: Duplicate exclusions in .samignore and template
✅ **DO**: Use template.yaml BuildProperties as primary

❌ **DON'T**: Forget to include non-Python files
✅ **DO**: Add explicit Include patterns for .clj, .json

❌ **DON'T**: Include dev dependencies in layer
✅ **DO**: Use `poetry export --only=main`

## More Info

- 📖 [SAM Build Architecture](./SAM_BUILD_ARCHITECTURE.md)
- 🧪 [Testing Guide](./SAM_BUILD_TESTING_GUIDE.md)
- 🔄 [Before/After Comparison](./SAM_BUILD_BEFORE_AFTER.md)
- ✅ [Issue Resolution](./ISSUE_RESOLUTION_SAM_BUILD.md)

## Version

**Current**: 2.16.5  
**Last Updated**: 2025-10-08  
**Status**: ✅ Production-ready
