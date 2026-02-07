#!/bin/bash
# One-time migration script: monolith stack -> 3-stack architecture
# This script deletes the existing monolith stack and deploys fresh
# with the new shared -> data -> core architecture.
#
# WARNING: This DELETES all resources (DynamoDB tables, S3 buckets, etc.)
# and recreates them. Only use when data loss is acceptable.
#
# Usage: ./scripts/migrate-to-multi-stack.sh [dev|staging|prod]

set -e

ENVIRONMENT="${1:-dev}"
if [ "$ENVIRONMENT" != "dev" ] && [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "prod" ]; then
    echo "ERROR: Invalid environment: $ENVIRONMENT (use 'dev', 'staging', or 'prod')"
    exit 1
fi

OLD_STACK="alchemiser-${ENVIRONMENT}"
SHARED_STACK="alchemiser-${ENVIRONMENT}-shared"
DATA_STACK="alchemiser-${ENVIRONMENT}-data"

echo "============================================"
echo " Multi-Stack Migration: $ENVIRONMENT"
echo "============================================"
echo ""
echo "This will:"
echo "  1. Delete the old monolith stack: $OLD_STACK"
echo "  2. Delete any retained resources (DynamoDB tables, S3 buckets)"
echo "  3. Deploy 3 new stacks: $SHARED_STACK -> $DATA_STACK -> $OLD_STACK"
echo ""
echo "WARNING: ALL DATA WILL BE LOST (tables, buckets, etc.)"
echo ""

if [ "$ENVIRONMENT" = "prod" ]; then
    echo "!!! PRODUCTION ENVIRONMENT DETECTED !!!"
    echo ""
fi

read -p "Are you sure you want to proceed? [y/N] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Migration cancelled."
    exit 0
fi

# ========================================================================
# PHASE 1: Delete any previously-failed new stacks (if they exist)
# ========================================================================
echo ""
echo "--- Phase 1: Cleaning up any partial new stacks ---"

for stack in "$SHARED_STACK" "$DATA_STACK"; do
    STATUS=$(aws cloudformation describe-stacks --stack-name "$stack" \
        --query 'Stacks[0].StackStatus' --output text --no-cli-pager 2>/dev/null || echo "DOES_NOT_EXIST")

    if [ "$STATUS" != "DOES_NOT_EXIST" ]; then
        echo "Deleting partial stack: $stack (status: $STATUS)..."

        # If stack is in REVIEW_IN_PROGRESS, we can still delete it directly.
        # If it's in a *_IN_PROGRESS state (other than REVIEW), wait for it first.
        if [[ "$STATUS" == *_IN_PROGRESS ]] && [[ "$STATUS" != "REVIEW_IN_PROGRESS" ]]; then
            echo "  Stack is in $STATUS, waiting for it to stabilize..."
            aws cloudformation wait stack-$( [[ "$STATUS" == CREATE* ]] && echo "create" || echo "update" )-complete \
                --stack-name "$stack" --no-cli-pager 2>/dev/null || true
        fi

        aws cloudformation delete-stack --stack-name "$stack" --no-cli-pager
        echo "Waiting for $stack deletion..."
        aws cloudformation wait stack-delete-complete --stack-name "$stack" --no-cli-pager 2>/dev/null || {
            echo "  WARNING: Wait timed out or failed for $stack. Checking status..."
            RETRY_STATUS=$(aws cloudformation describe-stacks --stack-name "$stack" \
                --query 'Stacks[0].StackStatus' --output text --no-cli-pager 2>/dev/null || echo "DELETED")
            if [ "$RETRY_STATUS" != "DELETED" ] && [ "$RETRY_STATUS" != "DOES_NOT_EXIST" ]; then
                echo "  Stack still exists ($RETRY_STATUS). Retrying delete with --retain-resources..."
                aws cloudformation delete-stack --stack-name "$stack" --no-cli-pager 2>/dev/null || true
                aws cloudformation wait stack-delete-complete --stack-name "$stack" --no-cli-pager 2>/dev/null || true
            fi
        }
        echo "  Deleted: $stack"
    else
        echo "  $stack does not exist (OK)"
    fi
done

# ========================================================================
# PHASE 2: Update old stack to remove DeletionPolicy: Retain, then delete
# ========================================================================
echo ""
echo "--- Phase 2: Deleting old monolith stack ($OLD_STACK) ---"

OLD_STATUS=$(aws cloudformation describe-stacks --stack-name "$OLD_STACK" \
    --query 'Stacks[0].StackStatus' --output text --no-cli-pager 2>/dev/null || echo "DOES_NOT_EXIST")

if [ "$OLD_STATUS" = "DOES_NOT_EXIST" ]; then
    echo "  Old stack does not exist (OK, skipping)"
else
    echo "  Old stack status: $OLD_STATUS"

    # Force-delete the stack. Resources with DeletionPolicy: Retain will
    # be orphaned and cleaned up in Phase 3.
    echo "  Deleting stack $OLD_STACK..."
    aws cloudformation delete-stack --stack-name "$OLD_STACK" --no-cli-pager
    echo "  Waiting for stack deletion (this may take several minutes)..."
    aws cloudformation wait stack-delete-complete --stack-name "$OLD_STACK" --no-cli-pager 2>/dev/null || {
        # If wait fails, check if DELETE_FAILED due to retained resources
        FINAL_STATUS=$(aws cloudformation describe-stacks --stack-name "$OLD_STACK" \
            --query 'Stacks[0].StackStatus' --output text --no-cli-pager 2>/dev/null || echo "DELETED")
        if [ "$FINAL_STATUS" = "DELETE_FAILED" ]; then
            echo "  Stack delete partially failed (retained resources). Force-deleting..."
            # Get resources that are NOT yet deleted - only these can be passed to --retain-resources.
            # Resources in DELETE_COMPLETE are already gone and must NOT be listed.
            RETAINED=$(aws cloudformation describe-stack-resources --stack-name "$OLD_STACK" \
                --query 'StackResources[?ResourceStatus!=`DELETE_COMPLETE`].LogicalResourceId' \
                --output text --no-cli-pager 2>/dev/null || echo "")
            # Retry delete, retaining those resources (they'll be cleaned up in Phase 3)
            RETAIN_ARGS=""
            for r in $RETAINED; do
                RETAIN_ARGS="$RETAIN_ARGS $r"
            done
            if [ -n "$RETAIN_ARGS" ]; then
                echo "  Retaining resources: $RETAIN_ARGS"
                aws cloudformation delete-stack --stack-name "$OLD_STACK" \
                    --retain-resources $RETAIN_ARGS --no-cli-pager
            else
                aws cloudformation delete-stack --stack-name "$OLD_STACK" --no-cli-pager
            fi
            echo "  Waiting for force-delete..."
            aws cloudformation wait stack-delete-complete --stack-name "$OLD_STACK" --no-cli-pager || true
        fi
    }
    echo "  Old stack deleted."
fi

# ========================================================================
# PHASE 3: Clean up retained/orphaned resources
# ========================================================================
echo ""
echo "--- Phase 3: Cleaning up retained resources ---"

# DynamoDB tables (DeletionPolicy: Retain means they survive stack deletion)
TABLES=(
    "alchemiser-${ENVIRONMENT}-trade-ledger"
    "alchemiser-${ENVIRONMENT}-market-data-fetch-requests"
    "alchemiser-${ENVIRONMENT}-bad-data-markers"
    "alchemiser-${ENVIRONMENT}-account-data"
)

for table in "${TABLES[@]}"; do
    if aws dynamodb describe-table --table-name "$table" --no-cli-pager >/dev/null 2>&1; then
        echo "  Deleting DynamoDB table: $table"
        aws dynamodb delete-table --table-name "$table" --no-cli-pager >/dev/null 2>&1 || true
    else
        echo "  Table $table does not exist (OK)"
    fi
done

# S3 buckets (must be emptied before deletion)
BUCKETS=(
    "alchemiser-${ENVIRONMENT}-reports"
    "alchemiser-${ENVIRONMENT}-market-data"
    "alchemiser-${ENVIRONMENT}-performance-reports"
)

for bucket in "${BUCKETS[@]}"; do
    if aws s3api head-bucket --bucket "$bucket" --no-cli-pager 2>/dev/null; then
        echo "  Emptying S3 bucket: $bucket"
        aws s3 rm "s3://${bucket}" --recursive --no-cli-pager 2>/dev/null || true
        echo "  Deleting S3 bucket: $bucket"
        aws s3api delete-bucket --bucket "$bucket" --no-cli-pager 2>/dev/null || true
    else
        echo "  Bucket $bucket does not exist (OK)"
    fi
done

# SNS topics
TOPICS_PREFIX="alchemiser-${ENVIRONMENT}-dlq-alerts"
echo "  Checking for SNS topic: $TOPICS_PREFIX"
TOPIC_ARN=$(aws sns list-topics --no-cli-pager --query "Topics[?contains(TopicArn, '${TOPICS_PREFIX}')].TopicArn" --output text 2>/dev/null || echo "")
if [ -n "$TOPIC_ARN" ] && [ "$TOPIC_ARN" != "None" ]; then
    echo "  Deleting SNS topic: $TOPIC_ARN"
    aws sns delete-topic --topic-arn "$TOPIC_ARN" --no-cli-pager 2>/dev/null || true
else
    echo "  Topic not found (OK)"
fi

# EventBridge bus
EVENT_BUS="alchemiser-${ENVIRONMENT}-events"
if aws events describe-event-bus --name "$EVENT_BUS" --no-cli-pager >/dev/null 2>&1; then
    echo "  Deleting EventBridge rules on bus: $EVENT_BUS"
    RULES=$(aws events list-rules --event-bus-name "$EVENT_BUS" --query 'Rules[].Name' --output text --no-cli-pager 2>/dev/null || echo "")
    for rule in $RULES; do
        # Remove targets first
        TARGETS=$(aws events list-targets-by-rule --event-bus-name "$EVENT_BUS" --rule "$rule" \
            --query 'Targets[].Id' --output text --no-cli-pager 2>/dev/null || echo "")
        if [ -n "$TARGETS" ]; then
            aws events remove-targets --event-bus-name "$EVENT_BUS" --rule "$rule" \
                --ids $TARGETS --no-cli-pager 2>/dev/null || true
        fi
        aws events delete-rule --event-bus-name "$EVENT_BUS" --name "$rule" --no-cli-pager 2>/dev/null || true
    done
    echo "  Deleting EventBridge bus: $EVENT_BUS"
    aws events delete-event-bus --name "$EVENT_BUS" --no-cli-pager 2>/dev/null || true
else
    echo "  EventBridge bus $EVENT_BUS does not exist (OK)"
fi

# EventBridge Scheduler schedules
SCHEDULES=(
    "alchemiser-${ENVIRONMENT}-data-refresh"
    "alchemiser-${ENVIRONMENT}-account-data"
)
for sched in "${SCHEDULES[@]}"; do
    if aws scheduler get-schedule --name "$sched" --no-cli-pager >/dev/null 2>&1; then
        echo "  Deleting schedule: $sched"
        aws scheduler delete-schedule --name "$sched" --no-cli-pager 2>/dev/null || true
    else
        echo "  Schedule $sched does not exist (OK)"
    fi
done

echo ""
echo "  Retained resources cleaned up."

# Wait for DynamoDB tables to finish deleting
echo "  Waiting for DynamoDB table deletions to complete..."
for table in "${TABLES[@]}"; do
    aws dynamodb wait table-not-exists --table-name "$table" --no-cli-pager 2>/dev/null || true
done
echo "  All tables deleted."

# ========================================================================
# PHASE 4: Deploy fresh 3-stack architecture
# ========================================================================
echo ""
echo "--- Phase 4: Deploying 3-stack architecture ---"
echo ""

chmod +x scripts/deploy.sh
./scripts/deploy.sh "$ENVIRONMENT"

echo ""
echo "============================================"
echo " Migration complete!"
echo "============================================"
echo ""
echo "New stacks:"
echo "  1. $SHARED_STACK  (EventBus, Layers, TradeLedger, S3)"
echo "  2. $DATA_STACK    (Data Lambda, AccountData Lambda)"
echo "  3. $OLD_STACK     (Strategy, Portfolio, Execution, etc.)"
