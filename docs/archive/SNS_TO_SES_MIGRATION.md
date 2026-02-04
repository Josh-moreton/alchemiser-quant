# SNS to SES Migration - Implementation Summary

## Overview
This document summarizes the comprehensive migration from AWS SNS to AWS SES for email notifications in The Alchemiser trading system.

## What Was Implemented

### 1. Infrastructure (template.yaml)
- ✅ Added `NotificationDedupTable` DynamoDB table for failure deduplication and recovery tracking
- ✅ Added SES environment variables to NotificationsFunction:
  - `SES_FROM_ADDRESS`, `SES_REPLY_TO_ADDRESS`, `SES_REGION`
  - `NOTIFICATIONS_TO_PROD`, `NOTIFICATIONS_TO_NONPROD`
  - `ALLOW_REAL_EMAILS` (environment-safe flag)
  - `NOTIFICATION_DEDUP_TABLE_NAME`
  - `DEDUP_QUIET_PERIOD_MINUTES` (default: 120)
- ✅ Updated IAM role with SES permissions (`ses:SendEmail`, `ses:SendRawEmail`)
- ✅ Added DynamoDB permissions for dedup table access
- ✅ Added CloudFormation output for NotificationDedupTable

### 2. Core Modules (layers/shared/the_alchemiser/shared/notifications/)

#### ses_publisher.py (SESEmailPublisher)
- ✅ Send HTML + plain text emails via Amazon SES
- ✅ Environment-safe routing (non-prod recipient override)
- ✅ Safety banners for non-prod emails
- ✅ Structured logging with SES message IDs
- ✅ Comprehensive error handling with retry via Lambda
- ✅ Module-level singleton pattern for efficiency

**Key Features**:
- Validates required env vars on initialization
- Applies recipient overrides based on stage
- Adds visual warning banner to non-prod emails
- Returns detailed result dict with message_id or error

#### dedup.py (NotificationDedupManager)
- ✅ Error normalization and hashing for stable dedup keys
- ✅ DynamoDB-backed state persistence
- ✅ Quiet period enforcement (default 120 minutes)
- ✅ Recovery detection and tracking
- ✅ Automatic TTL (90 days) for cleanup

**Key Features**:
- Strips timestamps, UUIDs, request IDs from error messages
- Generates stable SHA256 hash for error signature
- Dedup key format: `component#env#failed_step#error_hash`
- Scan-based recovery check (acceptable for low volume)
- Fail-open on errors (always send email if check fails)

#### templates.py
- ✅ Strict subject format: `Alchemiser <Component> — <STATUS> — <YYYY-MM-DD> — <env> — run_id=<run_id>`
- ✅ HTML + plain text rendering for all templates
- ✅ Shared branding (header with gradient, logo, footer)
- ✅ Color-coded status bars (green/yellow/red/blue)
- ✅ Daily Run SUCCESS template
- ✅ Daily Run FAILURE template
- ✅ Responsive email design (max-width 800px, inline CSS)

**Templates Implemented**:
1. `render_daily_run_success_html/text` - Rich success email with metrics
2. `render_daily_run_failure_html/text` - Actionable failure email
3. Recovery email (simple template in service.py)

### 3. Service Layer (functions/notifications/service.py)

**Complete Rewrite**:
- ✅ Migrated from SNS to SES
- ✅ Integrated deduplication for error notifications
- ✅ Integrated recovery detection for success notifications
- ✅ Template-based rendering for all emails
- ✅ Environment-aware recipient selection

**Handlers**:
1. `_handle_error_notification` - With dedup check before sending
2. `_handle_trading_notification` - With recovery check on success
3. `_handle_system_notification` - Simple HTML wrapper for text
4. `_send_recovery_email` - Dedicated recovery notification

**Features**:
- Dedup suppression prevents spam within quiet period
- Recovery emails sent when failures clear
- Rich context building for templates
- Fallback to simple failure template for trading errors
- CloudWatch Logs URL generation

### 4. Documentation

#### docs/SES_SETUP.md (10KB)
- ✅ Complete setup guide from scratch
- ✅ Domain vs email verification comparison
- ✅ DNS configuration (DKIM, SPF, DMARC) with examples
- ✅ Production access request process
- ✅ Per-environment configuration strategy
- ✅ Configuration set setup (optional)
- ✅ Testing procedures
- ✅ Monitoring and troubleshooting
- ✅ Deployment checklist
- ✅ Cost estimates
- ✅ Security notes

#### docs/TEMPLATE_CUSTOMIZATION.md (11KB)
- ✅ Template structure and components
- ✅ Creating new templates (step-by-step)
- ✅ HTML email best practices
- ✅ Styling guide (colors, typography, spacing)
- ✅ Testing strategies (manual + automated)
- ✅ Common customizations
- ✅ Troubleshooting guide

## What Still Needs to Be Done

### High Priority
1. **Data Lake Update Templates** - Create templates for data job notifications
2. **Enhanced Metrics** - Collect richer metrics for email content:
   - Start/end times, duration
   - Data freshness details
   - Gate statuses (DATA_FRESHNESS_GATE, RISK_GATE)
   - Top positions, portfolio snapshot
3. **Status Enums** - Formalize SUCCESS_WITH_WARNINGS status
4. **Unit Tests** - Add comprehensive test coverage:
   - SES sender tests
   - Template rendering tests
   - Dedup logic tests
   - Environment safety tests

### Medium Priority
5. **Integration Testing** - Full end-to-end test in dev environment
6. **DNS Configuration** - Set up DKIM, SPF, DMARC records for production domain
7. **Production Access** - Request SES production access (if in sandbox)
8. **SNS Cleanup** - Remove TradingNotificationsTopic (keep DLQ alerts only)

### Low Priority
9. **Configuration Set** - Create SES configuration set for event tracking
10. **Advanced Templates** - Add more sophisticated layouts and sections
11. **Runbook Update** - Add SES-specific troubleshooting to runbook

## Key Design Decisions

### 1. Code-Based Templates (Not SES Stored Templates)
**Rationale**: 
- Version control and code review
- Easy snapshot testing
- No separate provisioning workflow
- Shared partials (header/footer)

### 2. Environment-Safe Routing
**Rationale**:
- Prevent accidental prod emails in dev/staging
- Default to safe recipient override in non-prod
- Explicit opt-in required via `ALLOW_REAL_EMAILS=true`

### 3. Dedup on Errors Only (Not Successes)
**Rationale**:
- Success emails should always be sent (users want confirmation)
- Only errors cause spam when repeated
- Recovery emails close the loop after failures

### 4. Quiet Period (120 minutes)
**Rationale**:
- Long enough to avoid spam during repeated failures
- Short enough to still notify on sustained issues
- Configurable via env var

### 5. DynamoDB for Dedup State
**Rationale**:
- Simple, consistent storage
- TTL for automatic cleanup
- Low cost for low volume
- No need for complex querying (scan is acceptable)

### 6. HTML + Plain Text
**Rationale**:
- HTML for rich formatting and branding
- Plain text fallback for text-only clients
- Better deliverability with both versions
- Plain text can be read in CloudWatch Logs

## Migration Path

### Phase 1: Infrastructure (Complete ✅)
- Add DynamoDB table
- Configure SES env vars
- Update IAM permissions

### Phase 2: Core Implementation (Complete ✅)
- Implement SES sender
- Implement dedup logic
- Create templates
- Update NotificationService

### Phase 3: Documentation (Complete ✅)
- Write SES setup guide
- Write template customization guide

### Phase 4: Testing (In Progress)
- Add unit tests
- Run integration tests
- Validate in dev environment

### Phase 5: Production Cutover (Pending)
- Complete DNS configuration
- Request production access
- Deploy to dev
- Deploy to staging
- Deploy to prod
- Remove SNS topic

## Testing Strategy

### 1. Unit Tests (To Be Added)
```python
# Test SES sender
- test_send_email_success()
- test_send_email_with_recipient_override()
- test_send_email_failure_handling()
- test_environment_safe_routing()

# Test dedup
- test_dedup_key_generation()
- test_error_normalization()
- test_quiet_period_suppression()
- test_recovery_detection()

# Test templates
- test_subject_format()
- test_daily_run_success_rendering()
- test_daily_run_failure_rendering()
- test_context_defaults()
```

### 2. Integration Tests
- Send test email via SES in dev
- Trigger error notification and verify dedup
- Trigger success after error and verify recovery email
- Verify recipient override in non-prod

### 3. Manual Testing
- Deploy to dev
- Trigger orchestrator run
- Verify email received with correct formatting
- Check CloudWatch Logs for SES message IDs
- Trigger multiple errors and verify suppression
- Trigger success and verify recovery email

## Validation Checklist

Before production deployment:

- [ ] All Python files pass syntax check
- [ ] SAM template validates successfully
- [ ] Unit tests added and passing
- [ ] Integration test successful in dev
- [ ] SES identity verified (domain or email)
- [ ] DKIM records added and verified
- [ ] SPF record added
- [ ] DMARC record added (recommended)
- [ ] Production access granted (if needed)
- [ ] Test email sent successfully in dev
- [ ] Dedup tested (suppress + recover)
- [ ] Environment safety routing tested
- [ ] CloudWatch Logs show SES message IDs
- [ ] No errors in Lambda function logs

## Known Limitations

1. **Data Lake Templates Not Implemented**: Only Daily Run templates exist
2. **Metrics Incomplete**: Some fields show "N/A" or placeholder values
3. **Scan-Based Recovery**: Recovery check uses DynamoDB scan (fine for low volume)
4. **No Retry on SES Errors**: Lambda retries handle most failures, but complex retry logic not implemented
5. **Simple Recovery Email**: Recovery email is basic HTML, not using full template

## Performance Considerations

### DynamoDB
- On-demand billing - suitable for low volume
- TTL for automatic cleanup (90 days)
- Scan for recovery check - acceptable for <1000 records

### Lambda
- NotificationsFunction: 512MB, 60s timeout (sufficient)
- Cold start impact minimal (pydantic + structlog)
- SES calls are fast (~200ms)

### Cost
- **SES**: ~$0.30/month for 100 emails/day
- **DynamoDB**: ~$0.50/month for dedup table
- **Lambda**: Negligible (included in existing costs)
- **Total**: ~$1/month additional cost

## Rollback Plan

If issues arise after deployment:

1. **Revert service.py**: Use git to restore SNS-based version
2. **Keep infrastructure**: NotificationDedupTable can stay (no harm)
3. **Disable SES**: Set `ALLOW_REAL_EMAILS=false` globally
4. **Re-enable SNS**: Ensure TradingNotificationsTopic still exists

**Critical**: Do not remove SNS topic until SES is proven stable in production.

## Success Criteria

✅ **Infrastructure**: DynamoDB table, env vars, IAM permissions added
✅ **Core Modules**: SES publisher, dedup, templates implemented
✅ **Service Migration**: NotificationService uses SES
✅ **Documentation**: Complete setup and customization guides
⏳ **Testing**: Unit tests, integration tests needed
⏳ **Production**: DNS, production access, deployment

## Next Actions

1. **Add unit tests** for SES sender, dedup, templates
2. **Deploy to dev** and test end-to-end
3. **Configure DNS** (DKIM, SPF, DMARC) for production domain
4. **Request production access** if SES is in sandbox
5. **Deploy to staging** for pre-prod validation
6. **Deploy to production** after successful staging test
7. **Monitor** for 1 week, then remove SNS topic

## References

- AWS SES Developer Guide: https://docs.aws.amazon.com/ses/latest/dg/
- SAM CLI: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/
- Email HTML Best Practices: https://www.campaignmonitor.com/css/
- DMARC.org: https://dmarc.org/

---

**Last Updated**: 2026-01-01  
**Status**: Core implementation complete, testing in progress
