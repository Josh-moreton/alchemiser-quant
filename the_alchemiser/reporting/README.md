# Reporting Module

Business Unit: reporting | Status: current

## Overview

The reporting module generates professional PDF account reports from deterministic snapshot data. Reports are rendered using Playwright (headless Chromium) and Jinja2 templates, and stored in S3 for archival and distribution.

## Components

### 1. Metrics Calculator (`metrics.py`)
Computes key performance metrics from account snapshots:
- **Sharpe Ratio**: Risk-adjusted return measure
- **Calmar Ratio**: Return/max drawdown ratio
- **Maximum Drawdown**: Worst peak-to-trough decline
- **CAGR**: Compound Annual Growth Rate

### 2. PDF Renderer (`renderer.py`)
Renders reports using:
- **Jinja2**: HTML template engine
- **Playwright**: Headless Chromium for PDF generation
- **Template**: `templates/account_report.html`

Key features:
- A4 format with professional styling
- Responsive tables and charts
- Deterministic rendering (same input → identical output)

### 3. Report Service (`service.py`)
Orchestrates the report generation workflow:
1. Load snapshot from DynamoDB
2. Compute metrics
3. Render HTML
4. Convert to PDF
5. Upload to S3
6. Emit `ReportReady` event

### 4. Lambda Handler (`lambda_handler.py`)
AWS Lambda entry point for serverless execution.

**Event Structure:**
```json
{
  "account_id": "PA123456789",
  "snapshot_id": "2024-10-25T12:00:00+00:00",  // Optional
  "use_latest": false,  // Use latest snapshot if true
  "report_type": "account_summary",  // Optional
  "correlation_id": "req-abc-123"  // For tracing
}
```

**Response:**
```json
{
  "status": "success",
  "report_id": "report-abc123",
  "s3_uri": "s3://bucket/reports/PA123/2024/10/report.pdf",
  "file_size_bytes": 245678,
  "generation_time_ms": 7234
}
```

## S3 Storage Structure

Reports are organized by account and date:
```
reports/
  {account_id}/
    {YYYY}/
      {MM}/
        {report_type}_{snapshot_id}_{report_id}.pdf
```

Example:
```
reports/PA123456789/2024/10/account_summary_snap-abc_report-xyz.pdf
```

## Performance Metrics

- **Generation Time**: < 10 seconds (typical: 5-7s)
- **PDF Size**: < 5 MB (typical: 100-500KB)
- **Memory**: 512MB - 1GB (Playwright requires more memory)
- **Timeout**: 5 minutes (Lambda max for PDF generation)

## Dependencies

- `boto3`: AWS S3 client for report storage
- `jinja2`: HTML template rendering
- `playwright`: Headless browser for PDF generation
- `numpy`: Numerical computations for metrics

## Testing

Run tests with:
```bash
poetry run pytest tests/reporting/ -v
```

Test coverage:
- ✅ Metrics calculations (17 tests)
- ✅ PDF rendering (6 tests)
- ✅ Template context preparation
- ✅ Error handling

## Integration

### Direct Lambda Invocation
```python
import boto3

lambda_client = boto3.client('lambda')
response = lambda_client.invoke(
    FunctionName='the-alchemiser-report-generator-prod',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'account_id': 'PA123456789',
        'use_latest': True
    })
)
```

### Event Bus Integration
The service publishes `ReportReady` events that can trigger:
- Email notifications
- Dashboard updates
- Audit logging
- Archival workflows

### Step Functions (Future)
Can be integrated into Step Function workflows:
```yaml
CreateSnapshot -> GenerateReport -> SendNotification
```

## Local Development

1. **Install dependencies:**
   ```bash
   poetry install
   playwright install chromium
   ```

2. **Run tests:**
   ```bash
   poetry run pytest tests/reporting/
   ```

3. **Test rendering locally:**
   ```python
   from the_alchemiser.reporting.renderer import ReportRenderer
   from the_alchemiser.shared.repositories.account_snapshot_repository import AccountSnapshotRepository
   
   # Load snapshot
   repo = AccountSnapshotRepository(table_name="...")
   snapshot = repo.get_latest_snapshot("PA123456789")
   
   # Render PDF
   renderer = ReportRenderer()
   pdf_bytes, metadata = renderer.render_pdf(snapshot, output_path="/tmp/report.pdf")
   ```

## Configuration

Environment variables:
- `TRADE_LEDGER__TABLE_NAME`: DynamoDB table for snapshots
- `REPORTS_S3_BUCKET`: S3 bucket for report storage
- `LOGGING__LEVEL`: Logging level (INFO, DEBUG, etc.)

## Error Handling

The module handles common errors gracefully:
- Snapshot not found → ValueError with clear message
- PDF generation failure → Logged with correlation ID
- S3 upload failure → Retries with exponential backoff
- Invalid snapshot data → Validation errors with context

## Security

- ✅ No live API calls (deterministic from snapshots)
- ✅ S3 encryption enabled (AES256)
- ✅ IAM least privilege (read DynamoDB, write S3)
- ✅ Public access blocked on S3 bucket
- ✅ Sensitive data redacted from logs
- ✅ CodeQL security scan passing

## Future Enhancements

1. **Visual Charts**: Add equity curve and allocation pie charts
2. **Historical Data**: Include longer-term performance trends
3. **Customization**: Allow custom report templates and branding
4. **Multi-Period**: Generate comparative reports across periods
5. **Email Integration**: Direct email delivery with PDF attachment
6. **Scheduling**: Automated daily/weekly/monthly report generation

## Maintenance

- Keep Playwright up to date for security patches
- Monitor PDF generation times and optimize if needed
- Review S3 lifecycle policies and adjust retention
- Update metrics calculations as needed
- Maintain test coverage above 90%

## Support

For issues or questions:
1. Check CloudWatch logs: `/aws/lambda/the-alchemiser-report-generator-{stage}`
2. Review S3 bucket for generated reports
3. Check DynamoDB for available snapshots
4. Verify IAM permissions are correct
