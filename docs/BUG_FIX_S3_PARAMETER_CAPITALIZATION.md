# Bug Fix: S3 Parameter Capitalization

**Business Unit:** Execution | **Status:** Fixed | **Version:** 2.24.1

## Summary
Fixed critical S3 persistence failure caused by incorrect parameter naming in boto3 API calls. The code used lowercase parameter names (`bucket`, `key`, `body`, `content_type`) but boto3's S3 API requires capitalized names (`Bucket`, `Key`, `Body`, `ContentType`).

## Impact
- **Severity:** High (data persistence failure)
- **System:** Trade ledger S3 persistence
- **Symptom:** "Parameter validation failed" errors when persisting trade ledger
- **Detection:** Production logs showing successful trades but failed S3 uploads

## Root Cause
The `S3ClientProtocol` type definition and the `put_object()` call used **lowercase** parameter names, which don't match boto3's actual API signature.

**Boto3 S3 API signature (correct):**
```python
s3_client.put_object(
    Bucket="bucket-name",      # ✅ Capitalized
    Key="path/to/file",        # ✅ Capitalized
    Body="file content",       # ✅ Capitalized
    ContentType="application/json"  # ✅ Capitalized
)
```

**Original code (broken):**
```python
# Protocol definition - WRONG parameter names
class S3ClientProtocol(Protocol):
    def put_object(
        self,
        bucket: str,           # ❌ Should be Bucket
        key: str,              # ❌ Should be Key
        body: str,             # ❌ Should be Body
        content_type: str,     # ❌ Should be ContentType
    ) -> dict[str, Any]: ...

# Usage - WRONG parameter names
s3_client.put_object(
    bucket=self._settings.trade_ledger.bucket_name,     # ❌
    key=s3_key,                                          # ❌
    body=json.dumps(ledger_data, indent=2),             # ❌
    content_type="application/json",                     # ❌
)
```

## Error Message
```
Parameter validation failed:
Missing required parameter in input: "Bucket"
Missing required parameter in input: "Key"
Unknown parameter in input: "bucket", must be one of: ACL, Body, Bucket, ...
Unknown parameter in input: "key", must be one of: ACL, Body, Bucket, ...
Unknown parameter in input: "body", must be one of: ACL, Body, Bucket, ...
Unknown parameter in input: "content_type", must be one of: ACL, Body, Bucket, ...
```

## Fix
Updated both the protocol definition and the call site to use capitalized parameter names:

```python
# Protocol definition - FIXED
class S3ClientProtocol(Protocol):
    """Protocol for boto3 S3 client interface (subset used)."""

    def put_object(
        self,
        Bucket: str,           # ✅ Matches boto3 API
        Key: str,              # ✅ Matches boto3 API
        Body: str,             # ✅ Matches boto3 API
        ContentType: str,      # ✅ Matches boto3 API
    ) -> dict[str, Any]: ...

# Usage - FIXED
s3_client.put_object(
    Bucket=self._settings.trade_ledger.bucket_name,     # ✅
    Key=s3_key,                                          # ✅
    Body=json.dumps(ledger_data, indent=2),             # ✅
    ContentType="application/json",                      # ✅
)
```

## Evidence
### Before Fix (Production Logs)
```json
{
  "event": "✅ Rebalance plan completed: 13/13 orders succeeded",
  "correlation_id": "587f8b6c-9c59-4444-b524-a669c9f6ab96",
  "level": "info"
}
{
  "error": "Parameter validation failed: Missing required parameter in input: \"Bucket\"...",
  "event": "Failed to persist trade ledger to S3",
  "level": "error"
}
```

### After Fix (Expected Behavior)
```json
{
  "event": "✅ Rebalance plan completed: 13/13 orders succeeded",
  "correlation_id": "587f8b6c-9c59-4444-b524-a669c9f6ab96",
  "level": "info"
}
{
  "event": "Trade ledger persisted to S3",
  "bucket": "the-alchemiser-v2-trade-ledger-dev",
  "key": "trade-ledgers/2025/10/15/143722-ce0723c9-b1f1-41c8-9dab-7d621d4bcfd1-test-corr-123.json",
  "entries": 11,
  "level": "info"
}
```

## Testing
Updated test assertions to match corrected parameter names:

```python
# Test validation - FIXED
call_kwargs = mock_s3_client.put_object.call_args[1]
assert call_kwargs["Bucket"] == "test-bucket"      # ✅ Capitalized
assert call_kwargs["Key"].startswith("trade-ledgers/")  # ✅ Capitalized
assert call_kwargs["ContentType"] == "application/json"  # ✅ Capitalized
```

All S3 persistence tests pass:
- `test_persist_to_s3_success` ✅
- `test_persist_to_s3_disabled` ✅
- `test_persist_to_s3_no_entries` ✅
- `test_persist_to_s3_idempotency` ✅

## Configuration (No Changes Required)
The S3 bucket and credentials are already configured correctly via CloudFormation:

**Environment Variables (set by CloudFormation):**
```bash
TRADE_LEDGER__BUCKET_NAME=the-alchemiser-v2-trade-ledger-${Stage}
TRADE_LEDGER__ENABLED=true
```

**IAM Permissions (already granted):**
```yaml
- Effect: Allow
  Action:
    - s3:PutObject
    - s3:GetObject
    - s3:ListBucket
  Resource:
    - !GetAtt TradeLedgerBucket.Arn
    - !Sub "${TradeLedgerBucket.Arn}/*"
```

**No GitHub secrets needed** - S3 access uses Lambda execution role.

## Related Files
- `the_alchemiser/execution_v2/services/trade_ledger.py` (lines 45-53, 431-436)
- `tests/execution_v2/test_trade_ledger.py` (lines 355-357)
- `template.yaml` (S3 bucket and IAM configuration)

## Deployment Notes
- **Breaking Change:** No (internal parameter names only)
- **Backward Compatible:** Yes (no API changes)
- **Production Impact:** Fixes trade ledger persistence in production
- **Version:** 2.24.1 (PATCH - bug fix)

## Follow-Up Actions
- [x] Fix parameter names in code
- [x] Update test assertions
- [x] Verify type checking passes
- [x] Document fix
- [ ] Monitor next production run for successful S3 uploads
- [ ] Verify trade ledger entries appear in S3 bucket

## References
- **Boto3 S3 API docs:** https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html
- **Production logs:** CloudWatch Logs showing parameter validation errors
- **CloudFormation:** template.yaml lines 111, 118-129, 291-299
