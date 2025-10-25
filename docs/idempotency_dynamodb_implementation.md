# Idempotency Service - DynamoDB Backend Implementation Guide

## Overview

The idempotency service provides deduplication for Lambda requests and event processing. It currently uses an in-memory backend suitable for development and testing. For production use with AWS Lambda, implement a DynamoDB-backed storage.

## Architecture

### Current Implementation
- **In-Memory Backend** (`InMemoryIdempotencyBackend`): Simple dictionary-based storage with TTL support
- **Service Layer** (`IdempotencyService`): High-level API abstracting backend details
- **Protocol** (`IdempotencyBackend`): Interface contract for backend implementations

### Production Requirements
For AWS Lambda deployments with multiple concurrent invocations, persistent storage is required:
- **DynamoDB**: Recommended for AWS Lambda (built-in TTL, atomic operations, auto-scaling)
- **Redis/ElastiCache**: Alternative for high-throughput scenarios

## Implementing a DynamoDB Backend

### 1. Create DynamoDB Table

```python
# Example CloudFormation/SAM template
IdempotencyTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: alchemiser-idempotency-keys
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: idempotency_key
        AttributeType: S
    KeySchema:
      - AttributeName: idempotency_key
        KeyType: HASH
    TimeToLiveSpecification:
      Enabled: true
      AttributeName: expiry_time
    Tags:
      - Key: Purpose
        Value: Idempotency
```

### 2. Implement DynamoDB Backend

Create `the_alchemiser/shared/services/dynamodb_idempotency_backend.py`:

```python
"""DynamoDB-backed idempotency service implementation."""

from __future__ import annotations

import time
from typing import Any

import boto3
from botocore.exceptions import ClientError


class DynamoDBIdempotencyBackend:
    """DynamoDB implementation of idempotency backend.
    
    Uses DynamoDB conditional writes to provide atomic check-and-set
    operations for distributed idempotency checking.
    """
    
    def __init__(
        self, 
        table_name: str = "alchemiser-idempotency-keys",
        region: str = "us-east-1"
    ) -> None:
        """Initialize DynamoDB backend.
        
        Args:
            table_name: Name of DynamoDB table for idempotency keys
            region: AWS region for DynamoDB table
        """
        self.table_name = table_name
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(table_name)
    
    def check_and_set(self, key: str, ttl_seconds: int = 3600) -> bool:
        """Atomically check if key exists and create if not.
        
        Uses DynamoDB conditional write to ensure atomicity across
        multiple Lambda invocations.
        
        Args:
            key: Idempotency key to check/set
            ttl_seconds: Time-to-live in seconds
            
        Returns:
            True if key was newly created (first time),
            False if key already exists (duplicate)
        """
        expiry_time = int(time.time()) + ttl_seconds
        
        try:
            # Conditional write: only succeed if key doesn't exist
            self.table.put_item(
                Item={
                    "idempotency_key": key,
                    "expiry_time": expiry_time,
                    "created_at": int(time.time()),
                },
                ConditionExpression="attribute_not_exists(idempotency_key)"
            )
            return True  # Key was created - not a duplicate
            
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                # Key already exists - this is a duplicate
                return False
            raise  # Other errors should propagate
    
    def is_processed(self, key: str) -> bool:
        """Check if key exists in DynamoDB.
        
        Args:
            key: Idempotency key to check
            
        Returns:
            True if key exists (already processed), False otherwise
        """
        try:
            response = self.table.get_item(Key={"idempotency_key": key})
            
            # Key exists if Item is in response
            if "Item" not in response:
                return False
            
            # Check if key has expired (DynamoDB TTL is eventual)
            item = response["Item"]
            if int(time.time()) >= item.get("expiry_time", 0):
                return False
                
            return True
            
        except ClientError:
            # On error, assume not processed (fail-open)
            return False
    
    def mark_processed(self, key: str, ttl_seconds: int = 3600) -> None:
        """Mark key as processed in DynamoDB.
        
        Args:
            key: Idempotency key to mark
            ttl_seconds: Time-to-live in seconds
        """
        expiry_time = int(time.time()) + ttl_seconds
        
        self.table.put_item(
            Item={
                "idempotency_key": key,
                "expiry_time": expiry_time,
                "created_at": int(time.time()),
            }
        )
```

### 3. Update Lambda Handler Configuration

Modify `the_alchemiser/lambda_handler.py`:

```python
# Replace in-memory backend with DynamoDB for production
from the_alchemiser.shared.services.dynamodb_idempotency_backend import (
    DynamoDBIdempotencyBackend
)

# Initialize with DynamoDB backend
_dynamodb_backend = DynamoDBIdempotencyBackend(
    table_name=os.getenv("IDEMPOTENCY_TABLE_NAME", "alchemiser-idempotency-keys")
)
_idempotency_service = IdempotencyService(backend=_dynamodb_backend)
```

### 4. Add boto3 Dependency

Update `pyproject.toml`:

```toml
[tool.poetry.dependencies]
boto3 = "^1.35.0"  # Add boto3 for DynamoDB access
```

### 5. Update IAM Permissions

Grant Lambda function DynamoDB permissions:

```yaml
# SAM/CloudFormation
Policies:
  - DynamoDBCrudPolicy:
      TableName: !Ref IdempotencyTable
```

## Testing DynamoDB Backend

### Unit Tests

Create `tests/shared/services/test_dynamodb_idempotency_backend.py`:

```python
import pytest
from moto import mock_aws
import boto3

from the_alchemiser.shared.services.dynamodb_idempotency_backend import (
    DynamoDBIdempotencyBackend
)

@pytest.fixture
def dynamodb_table():
    """Create mock DynamoDB table for testing."""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="test-idempotency",
            KeySchema=[{"AttributeName": "idempotency_key", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "idempotency_key", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        yield table

def test_check_and_set_new_key(dynamodb_table):
    """Test check_and_set returns True for new key."""
    backend = DynamoDBIdempotencyBackend(table_name="test-idempotency")
    result = backend.check_and_set("test-key-1")
    assert result is True

def test_check_and_set_duplicate_key(dynamodb_table):
    """Test check_and_set returns False for duplicate."""
    backend = DynamoDBIdempotencyBackend(table_name="test-idempotency")
    backend.check_and_set("test-key-1")
    result = backend.check_and_set("test-key-1")
    assert result is False
```

### Integration Tests

Test against real DynamoDB (or DynamoDB Local):

```python
def test_concurrent_lambda_invocations():
    """Test idempotency across concurrent Lambda invocations."""
    backend = DynamoDBIdempotencyBackend()
    
    # Simulate concurrent invocations with same correlation_id
    key = "workflow-123-correlation-456"
    
    # First invocation should succeed
    assert backend.check_and_set(key) is True
    
    # Concurrent invocation should fail (duplicate)
    assert backend.check_and_set(key) is False
```

## Performance Considerations

### DynamoDB Capacity
- **On-Demand Mode**: Recommended for variable workloads, auto-scales
- **Provisioned Mode**: Use for predictable, high-volume workloads
- **GSIs**: Not required for simple key lookups

### TTL Settings
- **Lambda retries**: 24 hours (86400s) for event replay protection
- **High-frequency events**: 1 hour (3600s) for memory efficiency
- **EventBridge retries**: Match retry window (typically 24h)

### Costs
- **DynamoDB writes**: ~$1.25 per million write requests
- **DynamoDB reads**: ~$0.25 per million read requests
- **Storage**: ~$0.25 per GB-month (negligible for keys with TTL)

## Migration Strategy

### Phase 1: Development (Current)
- Use in-memory backend for local development
- No external dependencies required

### Phase 2: Production Deployment
1. Create DynamoDB table via IaC (CloudFormation/Terraform)
2. Implement DynamoDB backend class
3. Add boto3 dependency
4. Update Lambda IAM role
5. Configure environment variable for table name
6. Deploy and test with canary deployment

### Phase 3: Monitoring
- CloudWatch metrics for DynamoDB operations
- Lambda logs for idempotency hits/misses
- Alarms for throttling or errors

## Alternative: EventBridge Deduplication

For event-driven architectures, consider EventBridge's native deduplication:

```python
# EventBridge automatically deduplicates based on event_id
# No need for custom idempotency service if using EventBridge

response = events_client.put_events(
    Entries=[{
        'Source': 'the-alchemiser',
        'DetailType': 'TradingSignal',
        'Detail': json.dumps(event_data),
        'EventBusName': 'alchemiser-events',
        # EventBridge uses this for deduplication (5-minute window)
        'EventId': correlation_id,
    }]
)
```

## References

- [DynamoDB Conditional Writes](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/WorkingWithItems.html#WorkingWithItems.ConditionalUpdate)
- [DynamoDB TTL](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html)
- [AWS Lambda Powertools - Idempotency](https://docs.powertools.aws.dev/lambda/python/latest/utilities/idempotency/)
- [EventBridge Deduplication](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevents-deduplication.html)
