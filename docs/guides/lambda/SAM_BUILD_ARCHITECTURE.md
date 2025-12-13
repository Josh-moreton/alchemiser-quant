# SAM Build Architecture

## Overview

This document explains the AWS SAM build configuration for The Alchemiser Quantitative Trading System, following AWS best practices for Lambda packaging.

## Architecture

### CodeUri Strategy

**Current Configuration:**
```yaml
CodeUri: the_alchemiser/
Handler: lambda_handler.lambda_handler
```

**Rationale:**
- SAM build only scans the application directory (`the_alchemiser/`)
- No need to exclude root-level files (tests/, docs/, scripts/, etc.)
- Handler path is relative to CodeUri
- Cleaner, more maintainable configuration

**Previous Configuration (Deprecated):**
```yaml
CodeUri: ./
Handler: the_alchemiser.lambda_handler.lambda_handler
```
This required extensive exclusions and made SAM scan the entire repository.

### Package Structure

After build, the Lambda package structure is:
```
/var/task/
├── lambda_handler.py         # Entry point (Handler: lambda_handler.lambda_handler)
├── __init__.py
├── __main__.py
├── main.py
├── config/
│   ├── strategy.dev.json
│   └── strategy.prod.json
├── strategy_v2/
│   └── strategies/
│       ├── 1-KMLM.clj
│       ├── 2-Nuclear.clj
│       ├── 5-Coin.clj
│       ├── 6-TQQQ-FLT.clj
│       └── ...
├── portfolio_v2/
├── execution_v2/
├── orchestration/
├── notifications_v2/
└── shared/
```

### Dependencies

Dependencies are packaged in per-Lambda Layers (one layer per function):
- **Source:** `layers/<function>/requirements.txt` (manually curated per-function)
- **Location:** `StrategyLayer`, `PortfolioLayer`, `ExecutionLayer`, `NotificationsLayer`, `DataLayer` in template.yaml
- **Exclusions:** boto3, botocore (AWS-managed, provided by Lambda runtime)

**Per-Lambda Layer Benefits:**
- Each function ships only the dependencies it needs
- Reduced cold start times
- Smaller deployment artifacts
- Independent dependency management per function

## Build Configuration

### Include Patterns

Explicitly included files (specified in `template.yaml`):
```yaml
Include:
  - '**/*.clj'          # DSL strategy files
  - 'config/*.json'     # Configuration files
```

### Exclude Patterns

Files excluded from the build (specified in `template.yaml`):
```yaml
Exclude:
  - '**/__pycache__/**'  # Python cache
  - '**/*.pyc'           # Compiled Python
  - '**/*.pyo'           # Optimized Python
  - '**/*.egg-info/**'   # Package metadata
  - .pytest_cache/**     # Test cache
  - .mypy_cache/**       # Type checker cache
  - .ruff_cache/**       # Linter cache
  - .vscode/**           # IDE files
  - .editorconfig        # Editor config
  - '**/*.md'            # Documentation
  - '.env*'              # Environment files (security)
  - .aws/**              # AWS credentials (security)
```

**Note:** All exclusion logic is in `template.yaml` BuildProperties. AWS SAM does not support `.samignore` files.

## Build Process

### Local Build (Development)

```bash
# Clean previous builds
rm -rf .aws-sam

# Build with container for Lambda compatibility
sam build --use-container --parallel
```

### Deployment Script

The `scripts/deploy.sh` script:
1. Exports dependencies using Poetry: `poetry export --only=main`
2. Strips AWS-managed packages (boto3, botocore)
3. Builds SAM application with `--use-container` flag
4. Deploys with appropriate environment parameters

## Best Practices

### 1. CodeUri Scope
- ✅ **DO:** Point CodeUri to your application directory (`the_alchemiser/`)
- ❌ **DON'T:** Use root directory (`./`) requiring extensive exclusions

### 2. Exclusion Strategy
- ✅ **DO:** Use `template.yaml` BuildProperties for all exclusions
- ✅ **DO:** Include security exclusions (`.env*`, `.aws/`) in template.yaml
- ❌ **DON'T:** Use `.samignore` (not supported by AWS SAM)
- ❌ **DON'T:** Duplicate exclusion logic across files

### 3. Include Patterns
- ✅ **DO:** Explicitly include non-Python files needed at runtime (`.clj`, `.json`)
- ✅ **DO:** Document why each file type is included
- ❌ **DON'T:** Include test data, documentation, or development tools

### 4. Handler Path
- ✅ **DO:** Make handler path relative to CodeUri
- ✅ **DO:** Keep entry point at root of CodeUri directory
- ❌ **DON'T:** Use deeply nested handler paths

### 5. Dependencies
- ✅ **DO:** Use Lambda Layer for dependencies
- ✅ **DO:** Exclude AWS-managed packages (boto3, botocore)
- ✅ **DO:** Export production dependencies only (`--only=main`)
- ❌ **DON'T:** Include dev dependencies (pytest, mypy, ruff, etc.)

## Troubleshooting

### Build Size Issues

If Lambda package is too large:

1. **Check built package size:**
   ```bash
   du -sh .aws-sam/build/TradingSystemFunction
   du -sh .aws-sam/build/DependenciesLayer
   ```

2. **Verify exclusions are working:**
   ```bash
   find .aws-sam/build/TradingSystemFunction -type f -name "*.md"  # Should be empty
   find .aws-sam/build/TradingSystemFunction -type f -name "*.pyc" # Should be empty
   ```

3. **Check for unexpected files:**
   ```bash
   du -sh .aws-sam/build/TradingSystemFunction/* | sort -hr | head -10
   ```

### Import Errors After Deployment

If Lambda fails with import errors:

1. **Verify handler path in template.yaml:**
   - Handler: `lambda_handler.lambda_handler`
   - File must be at: `the_alchemiser/lambda_handler.py`

2. **Check that required files are included:**
   ```bash
   ls -la .aws-sam/build/TradingSystemFunction/config/
   ls -la .aws-sam/build/TradingSystemFunction/strategy_v2/strategies/
   ```

3. **Verify Lambda Layer is attached:**
   - Check CloudFormation stack resources
   - Verify Layer ARN in Lambda function configuration

### Container Build Issues

If `sam build --use-container` fails:

1. **Ensure Docker is running:**
   ```bash
   docker info
   ```

2. **Check Docker permissions:**
   ```bash
   docker run hello-world
   ```

3. **Clear Docker cache if builds are slow:**
   ```bash
   docker system prune -af
   ```

## References

- [AWS SAM Build Command Reference](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-build.html)
- [AWS Lambda Deployment Package](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-package.html)
- [SAM BuildProperties Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-resource-function.html#sam-function-buildproperties)

## Change History

### 2.16.5 - 2025-10-08
- Changed CodeUri from `./` to `the_alchemiser/`
- Simplified exclusion patterns
- Added explicit includes for `.clj` and `.json` files
- Updated Handler path to be relative to new CodeUri
- Moved all exclusions to template.yaml BuildProperties (AWS SAM best practice)
- Created this documentation

### 2.16.1 - 2025-10-07
- Added `--use-container` flag to ensure Lambda-compatible builds
- Moved pyarrow to dev dependencies (saves ~100MB)
- Enhanced template.yaml exclusions
- Reduced layer size from ~287MB to ~149MB
