# Version Injection into Lambda Metadata

This document explains how application version information from `pyproject.toml` is injected into the Lambda function at build time.

## Overview

When deploying to AWS Lambda, the version from `pyproject.toml` is:
1. Extracted during the build process
2. Passed as a CloudFormation parameter
3. Injected as an environment variable into the Lambda function
4. Included in all Lambda responses and logs

## Components

### 1. Version Extraction Script

`scripts/get_version.py` - Reads the version from `pyproject.toml` using Python's built-in `tomllib` module (Python 3.11+).

```bash
# Test version extraction
python3 scripts/get_version.py
# Output: 2.2.4
```

### 2. Deployment Script Integration

`scripts/deploy.sh` - Extracts version and passes it as a parameter to SAM deploy:

```bash
# Extract version
APP_VERSION=$(python3 scripts/get_version.py)

# Pass to SAM deploy
sam deploy --parameter-overrides AppVersion="$APP_VERSION" ...
```

### 3. CloudFormation Template

`template.yaml` - Defines the `AppVersion` parameter and injects it as an environment variable:

```yaml
Parameters:
  AppVersion:
    Type: String
    Default: "unknown"
    Description: Application version from pyproject.toml (injected at build time)

Globals:
  Function:
    Environment:
      Variables:
        APP__VERSION: !Ref AppVersion
```

### 4. Lambda Handler

`the_alchemiser/lambda_handler.py` - Reads version from environment and includes in responses:

```python
def _get_app_version() -> str:
    """Get application version from environment variable."""
    return os.environ.get("APP__VERSION", "unknown")
```

## Lambda Response Format

All Lambda responses now include a `version` field:

```json
{
  "status": "success",
  "mode": "trade",
  "trading_mode": "live",
  "message": "Live trading completed successfully",
  "request_id": "12345-abcde",
  "version": "2.2.4"
}
```

## CloudFormation Outputs

The deployed version is also available as a CloudFormation output:

```bash
# View deployed version
aws cloudformation describe-stacks \
  --stack-name the-alchemiser-v2 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApplicationVersion`].OutputValue' \
  --output text
```

## Logs

The version is logged when Lambda is invoked:

```json
{
  "message": "Lambda invoked",
  "version": "2.2.4",
  "request_id": "abc123..."
}
```

## Benefits

1. **Release Tracking**: Easily identify which version of the code is deployed
2. **Debugging**: Version information in logs helps correlate issues with releases
3. **Auditability**: CloudFormation outputs provide deployment history
4. **Monitoring**: Version appears in Lambda responses for downstream consumers

## Version Management

Follow the project's version management guidelines:

- `make bump-patch` - Bug fixes and minor changes (2.2.4 → 2.2.5)
- `make bump-minor` - New features (2.2.4 → 2.3.0)
- `make bump-major` - Breaking changes (2.2.4 → 3.0.0)

Always bump version before deployment using:
```bash
make bump-patch  # or bump-minor, bump-major
make deploy
```

## Testing

Test version extraction locally:

```bash
# Extract version
python3 scripts/get_version.py

# Test environment variable injection
export APP__VERSION="2.2.4"
python3 -c "import os; print(os.environ.get('APP__VERSION', 'unknown'))"
```
