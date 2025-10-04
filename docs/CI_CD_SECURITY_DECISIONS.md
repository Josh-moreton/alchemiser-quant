# CI/CD Security Decisions for Solo Developer

## Implemented: Security Scanning ✅

The CI pipeline includes security scanning to identify vulnerabilities:

- **pip-audit** - Scans Python dependencies for known CVE vulnerabilities
- **cfn-lint** - Validates CloudFormation/SAM template syntax and best practices
- **checkov** - Performs infrastructure-as-code (IaC) security scanning

All scans run in **advisory mode** (non-blocking) to provide visibility without disrupting development velocity.

## Not Implemented (and Why)

### 1. Pinned GitHub Actions (SHA Hashes)

**Why not needed for solo dev:**
- Dependabot already monitors GitHub Actions updates
- Solo developer has full control over when to review and accept updates
- Supply chain attack risk is mitigated by: limited attack surface, direct oversight of all changes, and ability to quickly detect and revert malicious updates
- Administrative overhead of managing SHA pins outweighs benefits in a single-developer environment

**When to reconsider:** If project becomes collaborative or requires compliance certifications.

### 2. SBOM (Software Bill of Materials) Generation

**Why not needed for solo dev:**
- Dependency tracking already handled by Poetry's `poetry.lock` file
- pip-audit provides vulnerability scanning without needing separate SBOM artifact
- No regulatory requirements for SBOM in solo projects
- Can be generated on-demand if needed: `poetry export` + `cyclonedx-py`

**When to reconsider:** If project requires compliance reporting, external audits, or customer-facing security posture.

### 3. CodeDeploy Canary Deployments with Auto-Rollback

**Why not needed for solo dev:**
- Trading system runs on schedule (once daily at 9:35 AM), not continuously
- Low deployment frequency reduces rollback urgency
- Solo developer can monitor deployment and manually rollback if needed
- EventBridge schedule can be disabled immediately if issues occur
- Canary deployment adds complexity and AWS costs (multiple Lambda versions)

**Manual rollback procedure:**
```bash
# Quick rollback using Lambda console or CLI
aws lambda update-alias \
  --function-name the-alchemiser-v2-lambda-prod \
  --name live \
  --function-version <PREVIOUS_VERSION>

# Or disable schedule immediately
aws scheduler update-schedule \
  --name the-alchemiser-daily-trading-prod \
  --state DISABLED
```

**When to reconsider:** If deployment frequency increases, multiple users depend on uptime, or financial risk per deployment increases significantly.

### 4. CloudWatch Alarms

**Why not needed for solo dev:**
- Solo developer receives Lambda execution logs via email (already configured)
- Dead Letter Queue (DLQ) captures failed invocations
- Scheduled execution means failures are discrete events, not continuous degradation
- Manual monitoring is sufficient for daily execution schedule

**When to reconsider:** If execution frequency increases, multiple environments need monitoring, or on-call rotation is required.

### 5. Extensive IAM Scoping

**Why current IAM is acceptable:**
- Lambda execution role uses AWS managed policy `AWSLambdaBasicExecutionRole` (industry standard)
- Trading logic doesn't interact with other AWS services (only Alpaca API)
- Solo developer account has limited blast radius
- CloudWatch Logs `Resource: "*"` is standard practice for Lambda functions

**When to reconsider:** If Lambda gains access to S3, DynamoDB, or other sensitive AWS resources.

## Security Principles for Solo Development

1. **Visibility over enforcement** - Security scans provide awareness without blocking development
2. **Simplicity over complexity** - Simpler pipelines are easier to understand and maintain
3. **Manual oversight is acceptable** - Solo developer can personally review all changes
4. **Risk-proportionate controls** - Security investments should match threat level and impact

## Future Enhancements (If Needed)

- **Enable blocking on HIGH/CRITICAL vulnerabilities** in pip-audit (change `|| true` to fail on findings)
- **Add deployment notifications** to Slack/email for deployment awareness
- **Implement basic CloudWatch alarm** for Lambda errors if execution frequency increases
- **Pin actions by SHA** if project becomes open source with external contributors

## References

- [GitHub Actions Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [OWASP DevSecOps Maturity Model](https://owasp.org/www-project-devsecops-maturity-model/)

---

**Last Updated:** 2024-12-19  
**Rationale:** Pragmatic security posture for solo developer project balancing security visibility with development velocity.
