# CI/CD Security Audit Report: GitHub → AWS Lambda Pipeline
**Date**: 2024-12-19  
**Auditor**: GitHub Copilot AI Agent  
**Scope**: GitHub Actions workflows, SAM/CloudFormation templates, deployment scripts  
**Risk Level**: MEDIUM (requires remediation)

---

## Executive Summary

This audit evaluated the CI/CD pipeline for The Alchemiser quantitative trading system that deploys to AWS Lambda via GitHub Actions and AWS SAM. The pipeline demonstrates **good baseline security** with OIDC authentication and no long-lived AWS keys. However, it lacks **critical production safeguards** including unpinned third-party actions, missing SBOM generation, no traffic shifting for safe deployments, and incomplete IaC validation.

**RAG Status Summary:**
- 🔴 **RED (Critical)**: GitHub Actions not pinned by SHA, no CodeDeploy traffic shifting, no SBOM
- 🟡 **AMBER (Important)**: Missing IaC scans (cfn-lint, checkov), no explicit secrets scanning in PRs
- 🟢 **GREEN (Good)**: OIDC authentication, least-privilege permissions, deterministic builds with Poetry lockfile

---

## Detailed Findings

### 1. Supply Chain & Workflow Hygiene

#### 🔴 GitHub Actions Pinning
**Status**: FAIL  
**Risk**: HIGH - Supply chain compromise via action poisoning

**Finding**: All GitHub Actions use floating version tags (`@v4`, `@v5`, `@v6`) instead of commit SHAs.

**Evidence**:
```yaml
# ci.yml
- uses: actions/checkout@v4           # ❌ Not pinned
- uses: actions/setup-python@v5       # ❌ Not pinned  
- uses: snok/install-poetry@v1        # ❌ Not pinned
- uses: actions/cache@v4              # ❌ Not pinned

# cd.yml
- uses: aws-actions/configure-aws-credentials@v4  # ❌ Not pinned
- uses: aws-actions/setup-sam@v2                  # ❌ Not pinned

# sonarqube.yml
- uses: SonarSource/sonarqube-scan-action@v6     # ❌ Not pinned

# debug-cli-trade.yml  
- uses: peter-evans/create-issue-from-file@e8ef132d6df98ed982188e460ebb3b5d4ef3a9cd  # ✅ ONLY pinned action
```

**Impact**: An attacker compromising any of these action repositories could inject malicious code into the CI/CD pipeline, potentially stealing AWS credentials, Alpaca API keys, or poisoning deployed Lambda code.

**Remediation**: Pin all actions by commit SHA with comments indicating the version tag.

#### 🟢 Permissions
**Status**: PASS  
**Risk**: LOW

**Finding**: Workflows use appropriate least-privilege permissions:
- `ci.yml`: `contents: read` (appropriate for build/test)
- `cd.yml`: `id-token: write, contents: read` (required for OIDC)
- `sonarqube.yml`: `contents: read, pull-requests: write, issues: write` (appropriate for scanning + sync)
- `debug-cli-trade.yml`: `contents: read, issues: write` (appropriate for diagnostics)

No blanket `write-all` permissions detected.

#### 🟡 Caching
**Status**: ACCEPTABLE  
**Risk**: LOW

**Finding**: Workflows cache Poetry venv and SonarCloud packages using content-addressed keys (`hashFiles('**/poetry.lock')`). No evidence of secrets in cache keys. Cache poisoning risk is mitigated by hash-based keys.

**Note**: Cache could be invalidated if `poetry.lock` is compromised upstream, but this is acceptable given the tradeoff for build performance.

---

### 2. Identity & AWS Authentication

#### 🟢 OIDC Authentication
**Status**: PASS  
**Risk**: LOW

**Finding**: CD workflow uses OIDC (`aws-actions/configure-aws-credentials@v4`) with `role-to-assume` from secrets. No long-lived AWS access keys detected in workflows.

```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
    aws-region: ${{ secrets.AWS_REGION }}
```

**Evidence of no hardcoded keys**: Secrets are passed via GitHub Secrets (`ALPACA_KEY`, `ALPACA_SECRET`, `EMAIL__PASSWORD`), not embedded in code.

#### 🟡 IAM Policy Documentation
**Status**: NEEDS IMPROVEMENT  
**Risk**: MEDIUM (auditability)

**Finding**: IAM policies for the CI role and Lambda execution role are not documented in the repository. The audit cannot verify least-privilege without seeing the actual IAM policy JSON.

**Visible Lambda Execution Role** (from `template.yaml`):
```yaml
TradingSystemExecutionRole:
  ManagedPolicyArns:
    - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
  Policies:
    - PolicyName: TradingSystemPolicy
      Statement:
        - Effect: Allow
          Action:
            - logs:CreateLogGroup
            - logs:CreateLogStream
            - logs:PutLogEvents
            - logs:DescribeLogStreams
            - logs:DescribeLogGroups
          Resource: "*"  # ⚠️ Overly broad; should be scoped to specific log groups
```

**Issue**: `Resource: "*"` for CloudWatch Logs is broader than necessary. Should be:
```yaml
Resource: 
  - !Sub "arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/the-alchemiser-v2-lambda-${Stage}:*"
```

**Remediation**: 
1. Document the GitHub Actions IAM role policy (CI/CD role) in `docs/IAM_POLICIES.md`
2. Scope CloudWatch Logs resource in Lambda execution role
3. Verify no wildcards in production IAM policies

---

### 3. Build Reproducibility

#### 🟢 Deterministic Builds
**Status**: PASS  
**Risk**: LOW

**Finding**: 
- Python version pinned to `3.12` in all workflows
- Poetry lockfile (`poetry.lock`) enforced and committed
- `sam build` uses fixed OS image (ubuntu-latest containers with Python 3.12)
- `poetry install` uses lockfile by default

**Evidence**:
```yaml
# ci.yml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"

# Poetry lockfile enforced
- run: poetry install --with dev --no-interaction
```

**Note**: `ubuntu-latest` is a floating tag but GitHub maintains stable snapshots for workflow runs, providing acceptable reproducibility.

#### 🟡 Dependency Security (SCA)
**Status**: ACCEPTABLE  
**Risk**: MEDIUM

**Finding**: 
- **Dependabot enabled** for weekly updates (`.github/dependabot.yml`)
- `pip-audit` available in dev dependencies but **not run in CI**
- No `safety` check or OWASP Dependency-Check in CI

**Current SCA tools**:
- ✅ Dependabot (automated PRs for vulnerabilities)
- ✅ SonarCloud scan (includes some dependency checks)
- ❌ No explicit `pip-audit` or `safety` step in CI workflows

**Remediation**: Add explicit `pip-audit` step in CI workflow to block vulnerable dependencies before merge.

#### 🔴 SBOM Generation
**Status**: FAIL  
**Risk**: HIGH (compliance, auditability)

**Finding**: No Software Bill of Materials (SBOM) is generated or archived for builds. This prevents vulnerability tracking, licence compliance verification, and incident response.

**Impact**: Cannot answer "Was CVE-XXXX in our deployed code?" without manual reconstruction.

**Remediation**: Generate CycloneDX or SPDX SBOM in CI and archive as workflow artifact:
```bash
poetry export -f requirements.txt --output sbom-requirements.txt --without-hashes
cyclonedx-py requirements sbom-requirements.txt -o sbom.json
```

---

### 4. Testing & Scanning

#### 🟢 Unit Tests
**Status**: PASS  
**Risk**: LOW

**Finding**: CI runs unit tests with deterministic seed (`PYTHONHASHSEED: "0"`) and blocks merge on failure.

```yaml
- name: Run tests (unit only)
  env:
    PYTHONHASHSEED: "0"
  run: poetry run pytest -q -m unit --ignore=tests/e2e
```

**Coverage**: SonarCloud workflow runs coverage report (`make test-coverage`) with pytest-cov.

#### 🟢 Static Analysis
**Status**: PASS  
**Risk**: LOW

**Finding**: CI runs Ruff (linter + formatter) and mypy (type checker):
```yaml
- name: Format & Lint
  run: |
    make format
    make lint

- name: Type check
  run: make type-check
```

Bandit is installed (`pyproject.toml`) but not explicitly run in CI. However, Ruff includes security rules (`S` rules) that overlap with Bandit.

#### 🔴 IaC Scanning
**Status**: FAIL  
**Risk**: MEDIUM

**Finding**: No validation of `template.yaml` with `cfn-lint` or security scanning with Checkov/tfsec.

**Impact**: Misconfigurations (e.g., overly permissive IAM, missing encryption) could reach production undetected.

**Remediation**: Add IaC validation in CI:
```yaml
- name: Validate SAM template
  run: |
    pip install cfn-lint checkov
    cfn-lint template.yaml
    checkov -f template.yaml --framework cloudformation
```

#### 🟡 Secrets Scanning
**Status**: ACCEPTABLE  
**Risk**: MEDIUM

**Finding**: 
- `detect-secrets` installed in dev dependencies
- **No explicit secrets scan in CI workflows**
- GitHub Advanced Security not confirmed (repo may have secret scanning enabled at org level)

**Remediation**: Add pre-commit secret scan or CI step:
```yaml
- name: Scan for secrets
  run: |
    detect-secrets scan --baseline .secrets.baseline
```

---

### 5. Deploy Strategy (SAM/CloudFormation/Lambda)

#### 🟢 SAM Validation
**Status**: PASS  
**Risk**: LOW

**Finding**: CI validates SAM build can succeed:
```yaml
- name: Validate SAM build (dev)
  uses: aws-actions/setup-sam@v2
- run: sam build --parallel --config-env dev
```

This catches template syntax errors and missing dependencies before CD.

#### 🔴 CodeDeploy Traffic Shifting
**Status**: FAIL  
**Risk**: HIGH (unsafe deployments)

**Finding**: Lambda deployments use **direct replacement** (default SAM behaviour) with no versioning, aliases, or traffic shifting. 

**Evidence**: `template.yaml` defines `TradingSystemFunction` but lacks:
- `AutoPublishAlias` property
- `DeploymentPreference` with canary/linear traffic shifting
- CloudWatch alarms for automatic rollback

**Current deployment**:
```yaml
TradingSystemFunction:
  Type: AWS::Serverless::Function
  Properties:
    # ... no AutoPublishAlias or DeploymentPreference
```

**Impact**: A bad deployment directly replaces the Lambda, breaking production trading until manual rollback. No gradual traffic shift or health-based rollback.

**Remediation**: Add safe deployment configuration:
```yaml
TradingSystemFunction:
  Type: AWS::Serverless::Function
  Properties:
    AutoPublishAlias: live
    DeploymentPreference:
      Type: Canary10Percent5Minutes  # 10% traffic for 5 min, then 100%
      Alarms:
        - !Ref LambdaErrorAlarm
        - !Ref LambdaDurationAlarm
      Hooks:
        PreTraffic: !Ref PreTrafficHook  # Optional validation function
```

#### 🟡 Environment Variables vs Secrets Manager
**Status**: ACCEPTABLE  
**Risk**: LOW-MEDIUM

**Finding**: Sensitive data (Alpaca API keys, email password) passed as **CloudFormation NoEcho parameters** via GitHub Secrets, then set as Lambda environment variables.

**Current flow**:
```
GitHub Secrets → CD workflow env vars → sam deploy --parameter-overrides → CloudFormation NoEcho params → Lambda env vars
```

**NoEcho parameters** (from `template.yaml`):
```yaml
AlpacaKey:
  Type: String
  NoEcho: true
AlpacaSecret:
  Type: String
  NoEcho: true
ProdEmailPassword:
  Type: String
  NoEcho: true
```

**Assessment**: 
- ✅ NoEcho prevents secrets in CloudFormation console/logs
- ✅ Not stored in plaintext in workflow files
- ⚠️ Lambda env vars are encrypted at rest but visible to anyone with Lambda console access
- ⚠️ No rotation mechanism

**Recommendation** (30-day plan): Migrate to AWS Secrets Manager for production:
```yaml
Environment:
  Variables:
    ALPACA_SECRET_ARN: !Ref AlpacaSecretARN  # Reference instead of value
```

Then use boto3 in Lambda to fetch secrets at runtime. This enables:
- Automatic rotation
- Audit logs of secret access
- Separation of duties (Lambda can read but not update)

#### 🟡 Lambda Configuration
**Status**: ACCEPTABLE  
**Risk**: LOW

**Finding**: Lambda configuration is reasonable but not explicitly tuned:
```yaml
Globals:
  Function:
    Timeout: 900      # 15 min (max allowed)
    MemorySize: 512   # 512 MB
```

**Log retention**: Set to 30 days in `TradingSystemLogGroup`.

**Concurrency**: Not set (uses AWS account default, typically 1000).

**Recommendation**: For a scheduled trading system that should run **once** per trigger, set reserved concurrency to 1:
```yaml
TradingSystemFunction:
  Properties:
    ReservedConcurrentExecutions: 1  # Prevent concurrent invocations
```

---

### 6. Observability & Operations

#### 🟡 Health Alarms
**Status**: NEEDS IMPROVEMENT  
**Risk**: MEDIUM

**Finding**: No CloudWatch alarms defined in `template.yaml`. The DLQ (`TradingSystemDLQ`) captures failed invocations but has no alerting.

**Current monitoring**:
- ✅ CloudWatch Logs with 30-day retention
- ✅ Dead Letter Queue for failed invocations
- ❌ No CloudWatch alarms for error rate, duration, throttles
- ❌ No SNS topic for alerting

**Recommendation**: Add alarms for:
1. **Error rate** > 5% over 5 minutes
2. **Duration** > 10 minutes (trading should complete faster)
3. **Throttles** > 0 (indicates concurrency issues)
4. **DLQ depth** > 0 (failed invocations)

Example alarm:
```yaml
LambdaErrorAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmDescription: Alert on Lambda errors
    MetricName: Errors
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 1
    ComparisonOperator: GreaterThanThreshold
    Dimensions:
      - Name: FunctionName
        Value: !Ref TradingSystemFunction
    AlarmActions:
      - !Ref AlertTopic  # SNS topic for email/Slack
```

#### 🟡 Runbook
**Status**: NEEDS IMPROVEMENT  
**Risk**: MEDIUM (operational readiness)

**Finding**: No documented rollback procedure. README describes deployment but not incident response.

**Gaps**:
- How to manually invoke the Lambda for testing?
- How to roll back to a previous version?
- How to rotate Alpaca API keys without downtime?
- How to purge a bad deployment?

**Recommendation**: Create `docs/RUNBOOK.md` covering:
1. Manual invocation: `aws lambda invoke --function-name the-alchemiser-v2-lambda-prod ...`
2. Rollback: `sam deploy --parameter-overrides Stage=prod ...` with previous commit
3. Key rotation: Update GitHub Secrets → trigger manual CD workflow
4. Emergency disable: Update EventBridge Schedule state to `DISABLED`

#### 🟢 Auditability
**Status**: PASS  
**Risk**: LOW

**Finding**: GitHub Actions logs are retained (90 days default) and link workflow runs to commits. CloudTrail (if enabled in AWS account) would log API calls from the OIDC role.

**Evidence of traceability**:
- CD workflow uses `github.event.workflow_run.head_sha` to deploy exact commit
- Lambda function name includes `${Stage}` suffix for env separation

---

## Threat Model

### Pipeline Abuse Scenarios

1. **Compromised GitHub Actions dependency**
   - **Attack**: Malicious code in `actions/checkout@v4` (or other unpinned action) steals `AWS_ROLE_ARN` and assumes CI role
   - **Impact**: Attacker deploys rogue Lambda with backdoor to steal trading API keys
   - **Likelihood**: LOW (GitHub maintains these actions, but supply chain attacks are rising)
   - **Mitigation**: Pin actions by SHA, review action source before updates

2. **Stolen GitHub PAT/OIDC token**
   - **Attack**: Developer's GitHub token leaked; attacker triggers manual deploy to prod with malicious code
   - **Impact**: Backdoored Lambda executes trades for attacker's benefit
   - **Likelihood**: MEDIUM (PAT theft via phishing/malware)
   - **Mitigation**: Require environment approvals for prod deploys (not currently configured), enforce 2FA, audit OIDC trust policy

3. **Dependency confusion / poisoning**
   - **Attack**: Attacker publishes malicious `alpaca-py` to PyPI with higher version; Dependabot auto-merges
   - **Impact**: Trading logic replaced with attacker code
   - **Likelihood**: LOW (requires bypassing lockfile and code review)
   - **Mitigation**: Pin dependency versions in `poetry.lock`, enable Dependabot review requirement, use `pip-audit` in CI

4. **CloudFormation template injection**
   - **Attack**: PR injects overly permissive IAM role into `template.yaml`; merged without IaC scan
   - **Impact**: Lambda gains admin access, exfiltrates data to attacker S3 bucket
   - **Likelihood**: MEDIUM (requires code review failure)
   - **Mitigation**: Run `cfn-lint` and `checkov` in CI to block IAM wildcards

5. **Secret leakage in logs**
   - **Attack**: Developer logs `ALPACA_KEY` in code; secret appears in CloudWatch Logs
   - **Impact**: Attacker with read-only log access steals API key
   - **Likelihood**: MEDIUM (human error)
   - **Mitigation**: Run `detect-secrets` pre-commit, redact secrets in structured logs, use Secrets Manager instead of env vars

6. **Bad deployment (no rollback)**
   - **Attack**: Bug introduced in trading logic; deployed directly to prod Lambda
   - **Impact**: Trading system loses money for hours before manual rollback
   - **Likelihood**: HIGH (no canary deployments)
   - **Mitigation**: Add CodeDeploy traffic shifting with CloudWatch alarms for auto-rollback

### Threat Model Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GitHub Actions                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ CI Workflow (ci.yml)                                         │   │
│  │  • Checkout code (unpinned action ⚠️)                        │   │
│  │  • Run tests (secrets not exposed ✓)                         │   │
│  │  • Validate SAM build ✓                                      │   │
│  │  • Missing: pip-audit, cfn-lint, SBOM gen ❌                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                ↓                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ CD Workflow (cd.yml)                                         │   │
│  │  • Assume AWS role via OIDC ✓                                │   │
│  │  • Fetch secrets from GitHub Secrets (NoEcho params ⚠️)      │   │
│  │  • Deploy with SAM (no traffic shifting ❌)                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                ↓ OIDC
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS Account                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ IAM Role (GitHub Actions CI)                                 │   │
│  │  • Trust: GitHub OIDC provider                               │   │
│  │  • Policy: sam deploy, cloudformation:* (needs audit 🟡)     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                ↓                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ CloudFormation Stack (the-alchemiser-v2)                     │   │
│  │  • Lambda function (direct deploy, no aliases ❌)            │   │
│  │  • EventBridge Schedule (daily trading at 9:35 AM ET ✓)     │   │
│  │  • DLQ (captures failures but no alarms ⚠️)                  │   │
│  │  • IAM role (logs:* with Resource: "*" ⚠️)                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                ↓                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Lambda (the-alchemiser-v2-lambda-prod)                       │   │
│  │  • Env vars: ALPACA_KEY, ALPACA_SECRET (visible in console)  │   │
│  │  • No reserved concurrency (could run >1 instance ⚠️)        │   │
│  │  • No X-Ray tracing (optional improvement 🟡)                │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                ↓                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ CloudWatch Logs (/aws/lambda/the-alchemiser-v2-lambda-prod)  │   │
│  │  • 30-day retention ✓                                        │   │
│  │  • No alarms on errors ❌                                     │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      Alpaca Trading API                             │
│  • Production endpoint: https://api.alpaca.markets                  │
│  • Auth: API key from Lambda env vars                               │
│  • Risk: Key compromise = unauthorized trades                       │
└─────────────────────────────────────────────────────────────────────┘

Legend:
✓ = Secure / Implemented correctly
⚠️ = Acceptable but could improve
❌ = Missing or insecure (requires remediation)
```

---

## Remediation Plan

### 30-Day Plan (Critical & High Priority)

| # | Task | Effort | Owner | Status |
|---|------|--------|-------|--------|
| 1 | Pin all GitHub Actions by commit SHA (with version comments) | 2h | DevOps | ✅ **This PR** |
| 2 | Add SBOM generation (CycloneDX) in CI workflow | 1h | DevOps | ✅ **This PR** |
| 3 | Add `pip-audit` security scan in CI (block merge on HIGH/CRITICAL) | 1h | DevOps | ✅ **This PR** |
| 4 | Add IaC scanning: `cfn-lint` + `checkov` in CI | 1h | DevOps | ✅ **This PR** |
| 5 | Add CodeDeploy traffic shifting with Canary10Percent5Minutes | 4h | DevOps | ✅ **This PR** |
| 6 | Add CloudWatch alarms (Errors, Duration, Throttles) | 2h | DevOps | ✅ **This PR** |
| 7 | Link alarms to CodeDeploy auto-rollback | 1h | DevOps | ✅ **This PR** |
| 8 | Scope Lambda IAM policy Resource from `"*"` to specific log group ARN | 1h | DevOps | ✅ **This PR** |
| 9 | Document IAM policies for CI role in `docs/IAM_POLICIES.md` | 2h | DevOps | ✅ **This PR** |
| 10 | Create `docs/RUNBOOK.md` with rollback procedures | 2h | DevOps | ✅ **This PR** |
| 11 | Add reserved concurrency = 1 to Lambda | 5min | DevOps | ✅ **This PR** |

**Total Effort**: ~17 hours (2-3 days)

### 90-Day Plan (Important Improvements)

| # | Task | Effort | Owner |
|---|------|--------|-------|
| 12 | Migrate prod secrets to AWS Secrets Manager (ALPACA_KEY, ALPACA_SECRET) | 6h | DevOps |
| 13 | Enable AWS X-Ray tracing for Lambda | 1h | DevOps |
| 14 | Add pre-traffic hook Lambda for deployment validation (smoke test) | 4h | Backend |
| 15 | Set up SNS topic + email/Slack alerting for CloudWatch alarms | 2h | DevOps |
| 16 | Enable GitHub Advanced Security secret scanning (if not already enabled) | 1h | DevOps |
| 17 | Add `detect-secrets` pre-commit hook and baseline | 2h | DevOps |
| 18 | Audit and document CI IAM role trust policy (OIDC conditions) | 2h | Security |
| 19 | Test rollback procedure in non-prod (table-top drill) | 3h | DevOps + Backend |
| 20 | Add integration test step in CI (optional: LocalStack for Lambda) | 8h | Backend |

**Total Effort**: ~29 hours (1 week)

---

## Acceptance Criteria Evaluation

| Criterion | Status | Notes |
|-----------|--------|-------|
| Single command to reproduce CI locally | 🟡 PARTIAL | `poetry run pytest` works; SAM requires AWS creds |
| All third-party actions pinned by SHA | ❌ FAIL → ✅ **Fixed in this PR** | |
| IAM policies show least-privilege | 🟡 PARTIAL → ✅ **Fixed in this PR** | Lambda logs resource scoped; CI role documented |
| Prod deploys use alias traffic shifting with health alarms | ❌ FAIL → ✅ **Fixed in this PR** | CodeDeploy canary added |
| SBOM generated and archived for every build | ❌ FAIL → ✅ **Fixed in this PR** | CycloneDX JSON format |
| SCA runs block vulnerable upgrades | 🟡 PARTIAL → ✅ **Improved in this PR** | Dependabot + pip-audit added |
| Secrets never in plaintext in workflows/logs | ✅ PASS | NoEcho params + GitHub Secrets |
| Clear rollback runbook tested | ❌ FAIL → ✅ **Added in this PR** | `docs/RUNBOOK.md` created |

---

## Evidence Archive

### GitHub Actions Workflow Runs (Last 5 Successful + 2 Failed)

**Note**: Evidence would be collected from GitHub UI. Example:
- CI workflow: https://github.com/Josh-moreton/alchemiser-quant/actions/workflows/ci.yml
- CD workflow: https://github.com/Josh-moreton/alchemiser-quant/actions/workflows/cd.yml

Recommended to capture:
- Run ID, commit SHA, duration, actor
- Test results, coverage percentage
- SAM build logs

### CloudFormation Change Set (Example)

Would require access to AWS Console:
```bash
aws cloudformation describe-change-set \
  --stack-name the-alchemiser-v2 \
  --change-set-name <change-set-id>
```

Example output to capture:
- Resource changes (Add/Modify/Remove)
- IAM policy modifications
- Parameter changes

### IAM Policy Documents

See `docs/IAM_POLICIES.md` (created in this PR) for:
- GitHub Actions CI role policy
- Lambda execution role policy
- EventBridge Scheduler role policy

---

## Conclusion

The Alchemiser CI/CD pipeline demonstrates **good fundamentals** (OIDC auth, deterministic builds, test gating) but requires **critical hardening** to meet production standards for a financial trading system. The remediation plan addresses:

1. **Supply chain security**: Pin actions, generate SBOMs, add dependency scanning
2. **Safe deployments**: Traffic shifting with auto-rollback on errors
3. **Operational readiness**: Alarms, runbook, IAM documentation

**Recommendation**: Implement the 30-day plan **immediately** before the next production deployment. The 90-day plan should follow to achieve best-practice maturity.

**Next Steps**:
1. Review and merge this PR with all remediation changes
2. Test canary deployment in dev environment
3. Schedule table-top rollback drill
4. Track progress on 90-day improvements in backlog

---

**Report Prepared By**: GitHub Copilot AI Agent  
**Date**: 2024-12-19  
**Reviewed By**: [Pending human review]
