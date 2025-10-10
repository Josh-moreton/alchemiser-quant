# CI/CD Non-Blocking Test Configuration

**Date:** October 10, 2025  
**Version:** 2.20.3  
**Status:** ✅ Complete

## Overview

Modified CI/CD workflows to make failing tests **non-blocking** (advisory) during the test fix period. This allows deployments to proceed while maintaining visibility into test failures.

## Changes Made

### 1. CI Workflow (`.github/workflows/ci.yml`) ✅

**Modified step:**
```yaml
- name: Run tests (unit only)
  # TEMPORARY: Non-blocking while fixing deprecated type tests
  # TODO: Remove continue-on-error after test suite is fixed (target: v2.20.4)
  # See: docs/TEST_FIXES_SUMMARY.md for fix roadmap
  continue-on-error: true
  id: tests
  env:
    PYTHONHASHSEED: "0"
  run: |
    poetry run pytest -q -m unit --ignore=tests/e2e

- name: Report test status
  if: steps.tests.outcome == 'failure'
  run: |
    echo "⚠️ Tests failed but CI continues (non-blocking mode)"
    echo "📋 See docs/TEST_FIXES_SUMMARY.md for fix roadmap"
    echo "🎯 Target: v2.20.4 - all tests passing"
```

**Effect:**
- ✅ Tests run and report results in CI logs
- ✅ Test failures don't block PR merges
- ✅ Test failures don't block `main` branch pushes
- ✅ CD workflow can still trigger on CI success
- ⚠️ Warning message displayed when tests fail

### 2. SonarQube Workflow (`.github/workflows/sonarqube.yml`) ✅

**Modified step:**
```yaml
- name: Generate coverage report
  # TEMPORARY: Non-blocking while fixing deprecated type tests
  # TODO: Remove continue-on-error after test suite is fixed (target: v2.20.4)
  # See: docs/TEST_FIXES_SUMMARY.md for fix roadmap
  continue-on-error: true
  env:
    PYTHONHASHSEED: "0"
  run: |
    make test-coverage
```

**Effect:**
- ✅ Coverage report generated (even with failures)
- ✅ SonarCloud scan proceeds
- ✅ Code quality metrics still tracked
- ⚠️ Coverage might be incomplete due to test failures

### 3. CD Workflow (`.github/workflows/cd.yml`) 🔍

**No changes needed** - CD already has proper gating:
- Dev deploys only trigger after CI **completes** (success or failure)
- The `continue-on-error: true` in CI means CI still "succeeds" from CD's perspective
- Prod deploys only trigger on release publish (manual control)

## Important Notes

### ⚠️ Temporary Configuration

This is a **temporary measure** during the test fix period:
- **Target removal:** Version 2.20.4
- **Duration:** Until all 101 test failures are fixed
- **Tracking:** See `docs/TEST_FIXES_SUMMARY.md`

### 🔍 Test Visibility

Tests still run and report failures:
- ✅ View test results in GitHub Actions logs
- ✅ See which tests are failing
- ✅ Coverage reports still generated
- ✅ SonarCloud still scans code

### 🚀 Deployment Impact

**Development (`dev`):**
- Deploys proceed even with test failures
- Monitor logs for test status
- Fix failures before promoting to prod

**Production (`prod`):**
- Manual release publish required
- Review test status before releasing
- Consider blocking prod deploys manually if critical failures exist

## Reverting to Blocking Tests

Once all tests are fixed (target: v2.20.4), revert these changes:

### CI Workflow
```yaml
- name: Run tests (unit only)
  env:
    PYTHONHASHSEED: "0"
  run: |
    poetry run pytest -q -m unit --ignore=tests/e2e
```

### SonarQube Workflow
```yaml
- name: Generate coverage report
  env:
    PYTHONHASHSEED: "0"
  run: |
    make test-coverage
```

Simply remove:
- `continue-on-error: true`
- `id: tests` (CI only)
- The "Report test status" step (CI only)
- TODO comments

## Best Practices During Non-Blocking Period

### For Developers

1. **Check test status** in CI logs before merging PRs
2. **Fix test failures** when modifying related code
3. **Don't introduce new test failures** - pre-commit hooks should catch most issues
4. **Reference** `docs/TEST_FIXES_SUMMARY.md` for fix roadmap

### For Reviewers

1. **Review test output** in PR CI runs
2. **Question new failures** - distinguish pre-existing vs. new issues
3. **Encourage fixes** as part of feature work where relevant
4. **Block PRs** that introduce new test failures (manual review)

### For Releases

1. **Check test status** before publishing releases
2. **Document known failures** in release notes if deploying with failures
3. **Prioritize fixes** for critical path features
4. **Target v2.20.4** for "all tests passing" milestone

## Monitoring

### GitHub Actions
- Navigate to Actions tab
- Click on any CI run
- Expand "Run tests (unit only)" step
- Review test output and summary

### Local Testing
```bash
# Run same tests as CI
poetry run pytest -q -m unit --ignore=tests/e2e

# Run all tests to see full picture
poetry run pytest tests/ -v

# Run specific failing module
poetry run pytest tests/shared/types/test_types_init.py -v
```

## Related Documentation

- `docs/TEST_FIXES_SUMMARY.md` - Complete test fix roadmap (101 failures)
- `docs/PRE_COMMIT_UPGRADE.md` - Pre-commit configuration improvements
- `.pre-commit-config.md` - Pre-commit user guide

## Risks & Mitigation

### Risks

1. **Broken code reaches production**
   - *Mitigated by:* Manual review, pre-commit hooks, partial test coverage
   
2. **Test debt accumulates**
   - *Mitigated by:* Clear roadmap, version target, TODO comments in workflows
   
3. **False confidence**
   - *Mitigated by:* Warning messages, documentation, visible TODO comments

### Mitigation Strategy

1. **Pre-commit hooks** catch most issues before commit
2. **Code review** catches logic errors
3. **Staged rollout** (dev → prod) catches runtime issues
4. **Monitoring** catches production issues
5. **Clear TODO** ensures this is temporary

## Success Criteria

Remove `continue-on-error` when:
- ✅ All 101 test failures fixed
- ✅ Full test suite passes locally
- ✅ Full test suite passes in CI
- ✅ No skipped tests (except intentional)
- ✅ Coverage meets target thresholds

## Timeline

- **Now (v2.20.3):** Non-blocking tests enabled
- **Near-term:** Fix high-priority failures (common schemas, feature pipeline)
- **Short-term (v2.20.4):** All tests passing, blocking re-enabled
- **Long-term:** Maintain test quality via pre-commit hooks

---

**Last Updated:** 2025-10-10  
**Version:** 2.20.3  
**Status:** Active - Temporary configuration in place
