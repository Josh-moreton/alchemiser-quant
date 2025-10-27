# Integrate PDF Report Generation for Trading Execution Notifications

**Status:** Proposed  
**Priority:** High  
**Related PR:** #2730  
**Related Issue:** #2726  
**Type:** Feature Enhancement

---

## Overview

PR #2730 introduced simplified trading notification emails with infrastructure to attach PDF reports from S3. However, the actual PDF generation is not yet implemented. This document outlines the integration of the existing reporting Lambda to generate trading execution PDFs that will be attached to notification emails.

## Context

### Current State

- ✅ Email client supports S3 attachments via `s3_attachments` parameter
- ✅ Simplified email template with `pdf_attached=True/False` flag
- ✅ NotificationService scaffolded with TODO comments for PDF generation
- ❌ No invocation of the reporting Lambda
- ❌ No execution data → PDF report conversion
- ❌ No execution report template

### Existing Infrastructure

- Reporting Lambda exists at `the_alchemiser/reporting/` for generating account snapshot PDFs
- Lambda function: `the-alchemiser-report-generator-{stage}`
- Uses Playwright + Jinja2 for PDF rendering
- Stores PDFs in S3 and emits `ReportReady` events

## Architecture

```
TradingNotificationRequested Event
         ↓
NotificationService._handle_trading_notification()
         ↓
    [NEW: _generate_execution_report()]
         ├─→ Prepare execution_data payload
         ├─→ Invoke reporting Lambda (boto3.client('lambda'))
         ├─→ Wait for Lambda response with S3 URI
         └─→ Pass S3 URI to send_email_notification(s3_attachments=[...])
         ↓
EmailClient downloads PDF from S3 and attaches
         ↓
Simple email sent with professional PDF attachment
```

## Implementation Tasks

### 1. Extend Reporting Lambda Handler

**File:** `the_alchemiser/reporting/lambda_handler.py`

**Changes:**
- Add support for `generate_from_execution` flag in event payload
- Add new handler function `_handle_execution_report()`
- Accept `execution_data` and `trading_mode` in event structure

**New Event Structure:**

```json
{
  "generate_from_execution": true,
  "report_type": "trading_execution",
  "execution_data": {
    "strategy_signals": {...},
    "consolidated_portfolio": {...},
    "orders_executed": [...],
    "execution_summary": {...}
  },
  "trading_mode": "PAPER",
  "correlation_id": "corr-123"
}
```

### 2. Create ExecutionReportService

**New File:** `the_alchemiser/reporting/execution_report_service.py`

**Purpose:** Generate PDF reports from trading execution data (not account snapshots)

**Key Methods:**
- `generate_execution_report(execution_data, trading_mode, correlation_id) -> ReportReady`
- `_build_execution_context(execution_data, trading_mode) -> dict`
- `_upload_to_s3(pdf_bytes, s3_key) -> None`

**Responsibilities:**
1. Transform execution_data into template context
2. Invoke ReportRenderer with execution template
3. Upload PDF to S3 with proper naming convention
4. Emit `ReportReady` event with S3 URI

**S3 Key Format:**
```
reports/{account_id}/{YYYY}/{MM}/execution_{YYYYMMDD_HHMMSS}_{report_id}.pdf
```

### 3. Add Lambda Invocation to NotificationService

**File:** `the_alchemiser/notifications_v2/service.py`

**Changes:**
- Add `_generate_execution_report()` method
- Update `_handle_trading_notification()` to invoke Lambda
- Handle Lambda response and extract S3 URI
- Pass S3 URI to `send_email_notification(s3_attachments=...)`
- Graceful degradation: log warning and continue if PDF generation fails

**Lambda Invocation Logic:**

```python
def _generate_execution_report(
    self, execution_data: dict[str, Any], trading_mode: str, correlation_id: str
) -> str:
    """Generate PDF report via reporting Lambda.
    
    Returns:
        S3 URI of the generated PDF report
        
    Raises:
        Exception: If report generation fails
    """
    import json
    import os
    import boto3
    
    stage = os.environ.get("STAGE", "dev")
    lambda_function_name = f"the-alchemiser-report-generator-{stage}"
    
    lambda_event = {
        "report_type": "trading_execution",
        "execution_data": execution_data,
        "trading_mode": trading_mode,
        "correlation_id": correlation_id,
        "generate_from_execution": True,
    }
    
    lambda_client = boto3.client("lambda")
    response = lambda_client.invoke(
        FunctionName=lambda_function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(lambda_event),
    )
    
    response_payload = json.loads(response["Payload"].read())
    
    if response_payload.get("status") != "success":
        error_msg = response_payload.get("message", "Unknown error")
        raise Exception(f"Report generation failed: {error_msg}")
    
    return response_payload.get("s3_uri")
```

**Update _handle_trading_notification:**

```python
# Generate PDF report from execution data
pdf_s3_uri = None
if event.trading_success and event.execution_data:
    try:
        pdf_s3_uri = self._generate_execution_report(
            execution_data=event.execution_data,
            trading_mode=event.trading_mode,
            correlation_id=event.correlation_id,
        )
    except Exception as pdf_error:
        # Log but don't fail the notification
        self.logger.warning(
            f"Failed to generate PDF report: {pdf_error}",
            extra={"correlation_id": event.correlation_id},
        )

# Build S3 attachments list
s3_attachments = None
if pdf_s3_uri:
    s3_attachments = [
        ("Trading_Execution_Report.pdf", pdf_s3_uri, "application/pdf")
    ]

# Use simplified email template
html_content = EmailTemplates.simple_trading_notification(
    success=event.trading_success,
    mode=event.trading_mode,
    orders_count=event.orders_placed,
    correlation_id=event.correlation_id,
    pdf_attached=(pdf_s3_uri is not None),
)

# Send notification with PDF attachment
success = send_email_notification(
    subject=subject,
    html_content=html_content,
    text_content=f"Trading execution completed. Success: {event.trading_success}",
    recipient_email=event.recipient_override,
    s3_attachments=s3_attachments,
)
```

### 4. Extend ReportRenderer

**File:** `the_alchemiser/reporting/renderer.py`

**Changes:**
- Add `render_execution_pdf(context, output_path=None) -> tuple[bytes, dict]`
- Load and render `execution_report.html` template
- Use same Playwright PDF generation logic as account reports

**Method Signature:**

```python
def render_execution_pdf(
    self,
    context: dict[str, Any],
    output_path: str | None = None,
) -> tuple[bytes, dict[str, Any]]:
    """Render execution report PDF from context.
    
    Args:
        context: Execution report context with strategy signals, orders, etc.
        output_path: Optional path to save PDF locally
        
    Returns:
        Tuple of (pdf_bytes, metadata) where metadata includes:
        - file_size_bytes: Size of PDF
        - generation_time_ms: Time taken to generate
        - page_count: Number of pages
    """
    template = self.env.get_template("execution_report.html")
    html_content = template.render(**context)
    
    # Convert to PDF using Playwright (existing logic)
    # ...
```

### 5. Create Execution Report Template

**New File:** `the_alchemiser/reporting/templates/execution_report.html`

**Template Structure:**
- **Header:** Trading mode, timestamp, correlation ID
- **Status Banner:** Success/failure with color coding
- **Strategy Signals Section:**
  - Table with strategy name, signal, reasoning, confidence
  - Color-coded signals (BUY=green, SELL=red, HOLD=gray)
- **Portfolio Rebalancing Plan:**
  - Table with symbol, current allocation, target allocation, delta
  - Visual indicators for increases/decreases
- **Order Execution Details:**
  - Table with symbol, side, quantity, price, status
  - Timestamps and order IDs
- **Execution Summary:**
  - Total orders placed/succeeded/failed
  - Total trade value
  - Execution duration
- **Footer:** Generated timestamp, report ID

**Design Inspiration:**
- Professional financial report styling
- Clean table layouts with borders
- Color coding for visual clarity
- A4 format, print-friendly
- Similar styling to existing `account_report.html`

### 6. Update IAM Permissions

**File:** `template.yaml`

**Changes:**
- Add Lambda invocation permissions to `NotificationServiceExecutionRole`

```yaml
- PolicyName: InvokeReportingLambda
  PolicyDocument:
    Version: "2012-10-17"
    Statement:
      - Effect: Allow
        Action:
          - lambda:InvokeFunction
        Resource:
          - !Sub "arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:the-alchemiser-report-generator-${Stage}"
```

### 7. Add Environment Variables

**File:** `template.yaml` → `NotificationServiceFunction`

**Changes:**
- Add `STAGE` environment variable for Lambda function name resolution

```yaml
Environment:
  Variables:
    STAGE: !Ref Stage
    # ... existing vars ...
```

### 8. Testing Requirements

#### Unit Tests

**`tests/reporting/test_execution_report_service.py`**
- Test context building from execution_data
- Test S3 upload with proper key naming
- Test ReportReady event emission
- Test error handling for missing fields

**`tests/notifications_v2/test_service.py`** (update existing)
- Test `_generate_execution_report()` with mocked Lambda client
- Test Lambda invocation with correct payload
- Test graceful degradation when PDF generation fails
- Test S3 URI passed to email client
- Test `pdf_attached=True` flag when PDF succeeds

**`tests/reporting/test_renderer.py`** (update existing)
- Test `render_execution_pdf()` with sample context
- Test PDF generation produces valid bytes
- Test metadata returned correctly

#### Integration Tests

**`tests/integration/test_execution_pdf_generation.py`**
- End-to-end test with real execution_data
- Mock Lambda response with S3 URI
- Verify email sent with attachment
- Verify S3 download attempted

#### Manual Testing
- Generate PDF in dev environment with real execution data
- Verify PDF renders correctly in various PDF readers
- Verify email attachment downloads and opens properly
- Test in both PAPER and LIVE modes

### 9. Documentation Updates

**Files to Update:**
- `the_alchemiser/reporting/README.md` - Add execution report documentation
- `the_alchemiser/notifications_v2/service.py` - Remove TODO comments, add docstrings
- Add example execution report screenshots to docs

## Implementation Order

1. **Phase 1 - Reporting Lambda Extension** (Backend)
   - Create `ExecutionReportService` 
   - Extend `lambda_handler.py` with execution report support
   - Add tests for execution report service

2. **Phase 2 - Template Design** (Frontend)
   - Create `execution_report.html` Jinja2 template
   - Test rendering with sample data
   - Refine styling and layout

3. **Phase 3 - Renderer Extension** (Backend)
   - Add `render_execution_pdf()` to `ReportRenderer`
   - Add tests for PDF generation

4. **Phase 4 - NotificationService Integration** (Backend)
   - Add `_generate_execution_report()` method
   - Update `_handle_trading_notification()`
   - Add Lambda invocation logic
   - Add tests with mocked Lambda

5. **Phase 5 - IAM & Deployment** (Infrastructure)
   - Update IAM permissions in `template.yaml`
   - Add environment variables
   - Deploy to dev environment

6. **Phase 6 - Testing & Validation** (QA)
   - Run full test suite
   - Manual testing in dev/staging
   - Verify PDFs and email attachments
   - Performance testing (Lambda cold starts)

7. **Phase 7 - Production Rollout** (Deployment)
   - Deploy to production
   - Monitor CloudWatch logs
   - Verify first production reports

## Acceptance Criteria

- [ ] Reporting Lambda accepts `generate_from_execution=true` events
- [ ] `ExecutionReportService` generates PDFs from execution_data
- [ ] Execution report template renders all execution details professionally
- [ ] NotificationService invokes Lambda and retrieves S3 URI
- [ ] Email sent with PDF attachment when generation succeeds
- [ ] Email sent without attachment when generation fails (graceful degradation)
- [ ] `pdf_attached` flag correctly set based on PDF generation status
- [ ] IAM permissions allow Lambda invocation
- [ ] All tests pass (unit, integration, e2e)
- [ ] PDF size < 5MB (typical 100-500KB)
- [ ] PDF generation time < 10 seconds
- [ ] Documentation updated with examples

## Success Metrics

- PDF generation success rate > 95%
- Average PDF generation time < 7 seconds
- Email delivery success rate unchanged (should remain > 99%)
- No increase in notification Lambda errors
- Positive user feedback on PDF reports

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Lambda timeout (5min) | Failed PDFs | Optimize template rendering, monitor metrics |
| S3 download failures | Email without attachment | Already handled via graceful degradation |
| Lambda cold starts | Slow first execution | Accept trade-off; consider provisioned concurrency |
| PDF size too large | Email delivery issues | Compress images, optimize layout |
| Missing execution_data fields | Template errors | Validate execution_data, provide defaults |

## Related Issues

- #2726 - Original issue requesting simplified emails with PDFs
- PR #2730 - Infrastructure for simplified emails and S3 attachments

## Dependencies

- boto3 (Lambda invocation)
- jinja2 (template rendering)
- playwright (PDF generation)
- Existing reporting Lambda infrastructure

## Estimated Effort

- **Development:** 3-4 days
- **Testing:** 1-2 days
- **Documentation:** 0.5 day
- **Total:** ~5-7 days

## Labels

- `feature`
- `notifications`
- `reporting`
- `priority-high`
- `pdf-generation`

---

## GitHub Issue Template

Copy the content above when creating the issue, with title:

**Title:** `Integrate PDF report generation for trading execution notifications`

**Labels:** `feature`, `notifications`, `reporting`, `priority-high`, `pdf-generation`
