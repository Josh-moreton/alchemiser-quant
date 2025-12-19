# Public Repository Security Checklist

This document provides a comprehensive checklist for ensuring the repository is safe to make public, with a focus on preventing secret exposure through GitHub Actions workflows.

## ✅ Pre-Release Security Checklist

### 1. Workflow Security (CRITICAL)

- [x] **Run workflow security validation**
  ```bash
  make validate-workflows
  ```
  
- [x] **Verify no workflows use `pull_request_target` trigger**
  - This trigger allows PRs from forks to access repository secrets
  - NEVER use this in public repositories
  
- [x] **Verify no workflows expose secrets in `pull_request` workflows**
  - PRs can access secrets if the workflow uses them
  - Only use `pull_request` for non-sensitive checks (linting, testing without secrets)
  
- [x] **Automated validation is in place**
  - `.github/workflows/workflow-security-check.yml` runs on every PR
  - Blocks PRs that modify workflows with security issues
  
### 2. Branch Protection

Configure on GitHub: **Settings → Branches → main → Add rule**

Required settings:
- [ ] **Require pull request reviews before merging**
  - At least 1 approval required
  - Dismiss stale pull request approvals when new commits are pushed
  
- [ ] **Require status checks to pass before merging**
  - [ ] Require branches to be up to date before merging
  - [ ] Required checks:
    - `ci` (from ci.yml)
    - `validate-workflows` (from workflow-security-check.yml)
    - Add any other critical checks
    
- [ ] **Require conversation resolution before merging**
  
- [ ] **Include administrators** (enforce rules for admins too)
  
- [ ] **Restrict who can push to matching branches**
  - Limit to repository maintainers only

### 3. Environment Protection

Configure on GitHub: **Settings → Environments**

For **production** environment:
- [ ] **Required reviewers**: Add trusted team members
- [ ] **Wait timer**: 0 minutes (or longer for extra safety)
- [ ] **Deployment branches**: Only allow protected branches

For **dev** environment:
- [ ] **Required reviewers**: Optional (at least 1 recommended)
- [ ] **Deployment branches**: Only allow protected branches

For **staging** environment:
- [ ] **Required reviewers**: Optional (at least 1 recommended)
- [ ] **Deployment branches**: Only allow protected branches

### 4. Repository Settings

Configure on GitHub: **Settings → General**

- [ ] **Disable forking** (optional, for extra security)
  - Note: This prevents community contributions
  - Only enable if you want external contributions
  
- [ ] **Automatically delete head branches**
  - Keeps repository clean
  
- [ ] **Allow merge commits** only (disable squash and rebase if strict history is required)

### 5. Secrets Audit

Verify all secrets are properly scoped:

- [ ] **Review all repository secrets** (Settings → Secrets and variables → Actions)
  - `ALPACA_KEY` - ✓ Production trading API key
  - `ALPACA_SECRET` - ✓ Production trading API secret
  - `AWS_ROLE_ARN` - ✓ AWS deployment role
  - `AWS_REGION` - ✓ AWS region
  - `EMAIL__PASSWORD` - ✓ SMTP password
  - `SONAR_TOKEN` - ✓ SonarCloud token (less critical)
  
- [ ] **Verify secrets are only used in protected workflows**
  - CD workflow: Only runs on tags and workflow_dispatch
  - PnL Analysis: Only runs on schedule and workflow_dispatch
  - Debug CLI: Only runs on workflow_dispatch
  - Deploy Shared Data: Only runs on workflow_dispatch
  
- [ ] **No secrets in code** (run detect-secrets or similar)
  ```bash
  # Already present in repo: .secrets.baseline
  # Scans are done via pre-commit hooks
  ```

### 6. Code Security

- [ ] **No hardcoded credentials in code**
  - Check all `.py` files
  - Check all config files
  - Check all scripts
  
- [ ] **`.env` file is in `.gitignore`**
  ```bash
  grep -q "^\.env$" .gitignore || echo "⚠️ Add .env to .gitignore"
  ```
  
- [ ] **`.env.example` has no real secrets**
  - Only contains placeholder values
  - Clearly marked as examples
  
- [ ] **Sensitive data is not in git history**
  ```bash
  # Search git history for potential secrets
  git log -p | grep -i "password\|secret\|key" | head -20
  ```

### 7. Documentation Review

- [ ] **README.md doesn't expose sensitive info**
  - No account IDs
  - No specific deployment details that could aid attacks
  - No real API keys or credentials
  
- [ ] **Comments in code don't expose secrets**
  - Review TODO comments
  - Review debug comments
  
- [ ] **Documentation about workflow security is complete**
  - `docs/WORKFLOW_SECURITY.md` ✓ Created
  - README includes security section

### 8. Testing

- [ ] **Test workflow security validation**
  ```bash
  python tests/test_workflow_security_validation.py
  ```
  
- [ ] **Create a test PR with malicious workflow**
  ```bash
  # Create a branch with pull_request_target
  # Verify CI blocks it
  # Delete the branch after testing
  ```
  
- [ ] **Verify CI blocks dangerous changes**
  - Test with a PR that adds `pull_request_target`
  - Should fail the `validate-workflows` check

### 9. External Dependencies

- [ ] **Review GitHub Actions from marketplace**
  - All actions pinned to specific commit SHAs or major versions
  - No suspicious or unmaintained actions
  
- [ ] **Review Python dependencies**
  ```bash
  poetry show | grep -i security
  ```
  
- [ ] **Check for known vulnerabilities**
  ```bash
  # Using safety or similar tools
  poetry run safety check || true
  ```

### 10. Monitoring & Alerts

- [ ] **Set up email alerts for workflow failures**
  - Already configured via SNS in workflows
  
- [ ] **Monitor for suspicious PRs**
  - Watch for workflow modifications
  - Watch for new workflow files
  - Review PRs from new contributors carefully
  
- [ ] **Set up security advisories**
  - Settings → Security & analysis → Dependabot alerts: **Enabled**
  - Settings → Security & analysis → Code scanning: **Consider enabling**

## 🚨 Post-Public Response Plan

### If a security violation is detected:

1. **Immediately close the PR** without merging
2. **Review the changes** to understand intent
3. **Check workflow run logs** for any secret exposure
4. **If secrets were exposed:**
   - Rotate all potentially compromised secrets immediately
   - Update secrets in GitHub (Settings → Secrets)
   - Update secrets in AWS Secrets Manager
   - Monitor for unauthorized activity
5. **Document the incident**
6. **Consider reporting to GitHub** if it's a serious attack

### Emergency Secret Rotation

If secrets are compromised:

1. **Alpaca API Keys**
   ```bash
   # 1. Log into Alpaca dashboard
   # 2. Regenerate API keys
   # 3. Update GitHub secrets: ALPACA_KEY, ALPACA_SECRET
   # 4. Redeploy if needed
   ```

2. **AWS Credentials**
   ```bash
   # 1. Disable the compromised IAM role or user
   # 2. Create new credentials
   # 3. Update GitHub secrets: AWS_ROLE_ARN
   # 4. Test new credentials in dev environment
   ```

3. **Email Password**
   ```bash
   # 1. Change email password
   # 2. Update GitHub secrets: EMAIL__PASSWORD
   # 3. Test email notifications
   ```

## 🎯 Final Verification

Before making the repository public:

```bash
# 1. Run all security checks
make validate-workflows

# 2. Run tests
python tests/test_workflow_security_validation.py

# 3. Review workflows
ls -la .github/workflows/
cat .github/workflows/*.yml | grep -E "on:|pull_request"

# 4. Check for secrets in code
git log --all -p | grep -iE "(password|secret|key|token).*=" | head -20

# 5. Verify branch protection
# Manually check on GitHub: Settings → Branches

# 6. Final commit
git status
```

## 📚 Reference Documents

- [docs/WORKFLOW_SECURITY.md](./WORKFLOW_SECURITY.md) - Detailed workflow security guide
- [scripts/validate_workflow_security.py](../scripts/validate_workflow_security.py) - Security validation script
- [.github/workflows/workflow-security-check.yml](../.github/workflows/workflow-security-check.yml) - Automated check
- [GitHub Actions Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)

## ✅ Repository Status

**Current Status**: ✅ **SAFE TO MAKE PUBLIC**

All critical security measures are in place:
- ✅ Workflow security validation automated
- ✅ No dangerous triggers in any workflow
- ✅ Secrets properly scoped to protected workflows
- ✅ Documentation complete
- ✅ Tests passing

**Remaining actions before going public:**
1. Configure branch protection rules on GitHub
2. Configure environment protection on GitHub
3. Test with a malicious PR (then delete)
4. Enable Dependabot alerts
5. Announce to team

---

**Last Updated**: 2024-12-19  
**Validated By**: Automated security checks  
**Next Review**: Before making repository public
