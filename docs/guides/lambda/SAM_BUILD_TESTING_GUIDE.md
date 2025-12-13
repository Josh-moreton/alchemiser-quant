# SAM Build Improvement - Testing Guide

## Summary of Changes

This PR implements AWS SAM best practices for Lambda packaging by restructuring the build configuration to use a more focused CodeUri.

### Key Changes

1. **CodeUri Migration**: `./` → `the_alchemiser/`
   - SAM now only scans the application directory
   - Eliminates need to exclude root-level files (tests/, docs/, scripts/, etc.)

2. **Handler Path Update**: `the_alchemiser.lambda_handler.lambda_handler` → `lambda_handler.lambda_handler`
   - Handler path is now relative to CodeUri
   - Cleaner, more conventional Lambda handler specification

3. **Simplified Exclusions**: 40+ patterns → 12 patterns
   - Removed all root-level exclusions (no longer needed)
   - Kept only build artifact exclusions within the_alchemiser/
   - All exclusion logic in template.yaml BuildProperties (AWS SAM standard)
   - Added security exclusions (.env*, .aws/) to BuildProperties

4. **Explicit Includes**: Added for non-Python runtime files
   - `**/*.clj` - DSL strategy files (10 files)
   - `config/*.json` - Configuration files (2 files)

## Testing Instructions

### 1. Pre-deployment Validation

```bash
# Clean any previous builds
rm -rf .aws-sam

# Validate template syntax
export SAM_CLI_TELEMETRY=0
sam validate --region us-east-1 --lint

# Expected: Template is valid
```

### 2. Local Build Test

```bash
# Ensure Docker is running
docker info

# Build with container (Lambda-compatible)
sam build --use-container --parallel

# Check build succeeded
ls -la .aws-sam/build/StrategyFunction/
ls -la .aws-sam/build/StrategyLayer/
ls -la .aws-sam/build/PortfolioLayer/
ls -la .aws-sam/build/ExecutionLayer/
```

### 3. Verify Package Structure

```bash
# Check handler file is at root of CodeUri
ls -la .aws-sam/build/TradingSystemFunction/lambda_handler.py

# Verify config files are included
ls -la .aws-sam/build/TradingSystemFunction/config/
# Expected: strategy.dev.json, strategy.prod.json

# Verify strategy files are included
ls -la .aws-sam/build/TradingSystemFunction/strategy_v2/strategies/
# Expected: *.clj files (1-KMLM.clj, 2-Nuclear.clj, etc.)

# Check all Python modules are present
ls -la .aws-sam/build/TradingSystemFunction/
# Expected: strategy_v2/, portfolio_v2/, execution_v2/, orchestration/, shared/, notifications_v2/
```

### 4. Verify Exclusions

```bash
# Should NOT find markdown files
find .aws-sam/build/TradingSystemFunction -name "*.md"
# Expected: No output

# Should NOT find test files
find .aws-sam/build/TradingSystemFunction -name "test_*.py"
# Expected: No output

# Should NOT find cache files
find .aws-sam/build/TradingSystemFunction -name "*.pyc"
find .aws-sam/build/TradingSystemFunction -name "__pycache__"
# Expected: No output

# Should NOT find IDE files
find .aws-sam/build/TradingSystemFunction -name ".vscode"
# Expected: No output
```

### 5. Check Package Size

```bash
# Check function package sizes
du -sh .aws-sam/build/StrategyFunction
du -sh .aws-sam/build/PortfolioFunction
du -sh .aws-sam/build/ExecutionFunction
# Expected: <50MB each

# Check per-function layer sizes
du -sh .aws-sam/build/StrategyLayer
du -sh .aws-sam/build/PortfolioLayer
du -sh .aws-sam/build/ExecutionLayer
du -sh .aws-sam/build/NotificationsLayer
du -sh .aws-sam/build/DataLayer
# Expected: Smaller than shared layer (function-specific deps only)
```

### 6. Test Local Invocation (Optional)

```bash
# Test with sample event
echo '{"mode": "trade"}' | sam local invoke TradingSystemFunction

# Or use existing test events
sam local invoke TradingSystemFunction --event events/trade-event.json
```

### 7. Deploy to Dev Environment

```bash
# Deploy to dev (requires credentials)
./scripts/deploy.sh dev

# Or manually
sam deploy --config-env dev --no-fail-on-empty-changeset
```

### 8. Post-Deployment Verification

```bash
# Check Lambda function configuration
aws lambda get-function --function-name the-alchemiser-v2-lambda-dev --query 'Configuration.Handler'
# Expected: "lambda_handler.lambda_handler"

aws lambda get-function --function-name the-alchemiser-v2-lambda-dev --query 'Configuration.CodeSize'
# Expected: Similar to previous deployments

# Test invocation
aws lambda invoke --function-name the-alchemiser-v2-lambda-dev \
  --payload '{"mode": "test"}' \
  response.json

cat response.json
# Expected: Successful response or appropriate error (not import error)

# Check CloudWatch logs
sam logs -n TradingSystemFunction --tail
# Expected: No import errors, application starts correctly
```

## Expected Outcomes

### ✅ Success Criteria

1. **Build completes without errors**
2. **Handler file is at package root**: `lambda_handler.py` at `/var/task/lambda_handler.py`
3. **Config files are included**: `config/strategy.dev.json`, `config/strategy.prod.json`
4. **Strategy files are included**: All `.clj` files in `strategy_v2/strategies/`
5. **Exclusions work**: No `.md`, `test_*.py`, `*.pyc`, or `.vscode` files in package
6. **Package size is reasonable**: Function <50MB, Layer ~149MB
7. **Lambda invocation succeeds**: No import errors, application starts normally

### ❌ Failure Scenarios & Fixes

#### Import Error: "No module named 'lambda_handler'"

**Cause**: Handler path or CodeUri misconfigured

**Fix**: Verify template.yaml has:
```yaml
CodeUri: the_alchemiser/
Handler: lambda_handler.lambda_handler
```

#### Missing Strategy Files

**Cause**: Include patterns not working

**Fix**: Verify template.yaml BuildProperties has:
```yaml
Include:
  - '**/*.clj'
```

#### Missing Config Files

**Cause**: Config files not in expected location

**Fix**: Verify `the_alchemiser/config/*.json` exists and is included:
```yaml
Include:
  - 'config/*.json'
```

#### Package Too Large

**Cause**: Exclusions not working, unexpected files included

**Fix**: 
1. Check for large files: `du -sh .aws-sam/build/TradingSystemFunction/* | sort -hr | head -10`
2. Verify exclusions in template.yaml BuildProperties
3. Ensure security files (.env*, .aws/) are excluded in BuildProperties

## Rollback Plan

If issues are discovered post-deployment:

1. **Immediate**: Revert to previous Lambda version
   ```bash
   aws lambda update-function-code \
     --function-name the-alchemiser-v2-lambda-dev \
     --s3-bucket <previous-bucket> \
     --s3-key <previous-key>
   ```

2. **Git revert**: Restore previous configuration
   ```bash
   git revert HEAD
   git push origin copilot/improve-sam-build-structure
   ```

3. **Redeploy**: Previous working version
   ```bash
   ./scripts/deploy.sh dev
   ```

## Additional Resources

- [docs/SAM_BUILD_ARCHITECTURE.md](./SAM_BUILD_ARCHITECTURE.md) - Comprehensive architecture documentation
- [AWS SAM Build Command Reference](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-build.html)
- [SAM BuildProperties Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-resource-function.html#sam-function-buildproperties)

## Questions?

If you encounter any issues during testing:

1. Check the troubleshooting section in `docs/SAM_BUILD_ARCHITECTURE.md`
2. Verify all prerequisites are met (Docker running, SAM CLI installed, AWS credentials configured)
3. Review CloudWatch logs for specific error messages
4. Compare build output with previous successful builds

---

**Version**: 2.16.5  
**Date**: 2025-10-08  
**Author**: Copilot AI Agent
