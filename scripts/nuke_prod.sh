#!/bin/bash
# Nuke all remaining alchemiser-prod resources from AWS
# Safe to re-run multiple times
set -euo pipefail
export AWS_PAGER=""

echo "=== Nuking all alchemiser-prod resources ==="

# 1. S3 buckets
echo ""
echo "--- S3 Buckets ---"
for bucket in $(aws s3api list-buckets --query 'Buckets[].Name' --output text); do
  if [[ "$bucket" == *alchemiser-prod* ]] || [[ "$bucket" == *alchemiser-shared* ]]; then
    echo "Deleting bucket: $bucket"
    aws s3 rb "s3://$bucket" --force 2>/dev/null || echo "  Failed (may already be gone)"
  fi
done

# 2. DynamoDB tables
echo ""
echo "--- DynamoDB Tables ---"
for table in $(aws dynamodb list-tables --query 'TableNames[?contains(@,`alchemiser-prod`)]' --output text); do
  echo "Deleting table: $table"
  aws dynamodb delete-table --table-name "$table" 2>/dev/null || echo "  Failed"
done

# 3. Lambda functions
echo ""
echo "--- Lambda Functions ---"
for fn in $(aws lambda list-functions --query 'Functions[].FunctionName' --output text); do
  if [[ "$fn" == *alchemiser-prod* ]]; then
    echo "Deleting function: $fn"
    aws lambda delete-function --function-name "$fn" 2>/dev/null || echo "  Failed"
  fi
done

# 4. Lambda layers (all versions)
echo ""
echo "--- Lambda Layers ---"
for layer in $(aws lambda list-layers --query 'Layers[].LayerName' --output text); do
  if [[ "$layer" == *alchemiser-prod* ]]; then
    for ver in $(aws lambda list-layer-versions --layer-name "$layer" --query 'LayerVersions[].Version' --output text); do
      echo "Deleting layer: $layer version $ver"
      aws lambda delete-layer-version --layer-name "$layer" --version-number "$ver" 2>/dev/null || echo "  Failed"
    done
  fi
done

# 5. SQS queues
echo ""
echo "--- SQS Queues ---"
for url in $(aws sqs list-queues --queue-name-prefix alchemiser-prod --query 'QueueUrls[]' --output text 2>/dev/null); do
  echo "Deleting queue: $url"
  aws sqs delete-queue --queue-url "$url" 2>/dev/null || echo "  Failed"
done

# 6. SNS topics
echo ""
echo "--- SNS Topics ---"
for arn in $(aws sns list-topics --query 'Topics[].TopicArn' --output text); do
  if [[ "$arn" == *alchemiser-prod* ]]; then
    echo "Deleting topic: $arn"
    aws sns delete-topic --topic-arn "$arn" 2>/dev/null || echo "  Failed"
  fi
done

# 7. EventBridge Scheduler schedules
echo ""
echo "--- EventBridge Scheduler Schedules ---"
for sched in $(aws scheduler list-schedules --query 'Schedules[].Name' --output text 2>/dev/null); do
  if [[ "$sched" == *alchemiser-prod* ]]; then
    echo "Deleting schedule: $sched"
    aws scheduler delete-schedule --name "$sched" 2>/dev/null || echo "  Failed"
  fi
done

# 8. EventBridge rules on custom bus
echo ""
echo "--- EventBridge Rules ---"
if aws events describe-event-bus --name alchemiser-prod-events &>/dev/null; then
  for rule in $(aws events list-rules --event-bus-name alchemiser-prod-events --query 'Rules[].Name' --output text 2>/dev/null); do
    echo "Removing targets and deleting rule: $rule"
    targets=$(aws events list-targets-by-rule --rule "$rule" --event-bus-name alchemiser-prod-events --query 'Targets[].Id' --output text 2>/dev/null)
    if [[ -n "$targets" ]]; then
      aws events remove-targets --rule "$rule" --event-bus-name alchemiser-prod-events --ids $targets 2>/dev/null || true
    fi
    aws events delete-rule --name "$rule" --event-bus-name alchemiser-prod-events 2>/dev/null || echo "  Failed"
  done
  echo "Deleting event bus: alchemiser-prod-events"
  aws events delete-event-bus --name alchemiser-prod-events 2>/dev/null || echo "  Failed"
fi

# 9. CloudWatch alarms
echo ""
echo "--- CloudWatch Alarms ---"
for alarm in $(aws cloudwatch describe-alarms --alarm-name-prefix alchemiser-prod --query 'MetricAlarms[].AlarmName' --output text 2>/dev/null); do
  echo "Deleting alarm: $alarm"
  aws cloudwatch delete-alarms --alarm-names "$alarm" 2>/dev/null || echo "  Failed"
done

# 10. IAM roles (created by SAM/CFn)
echo ""
echo "--- IAM Roles ---"
for role in $(aws iam list-roles --query 'Roles[].RoleName' --output text); do
  if [[ "$role" == *alchemiser-prod* ]]; then
    echo "Cleaning up role: $role"
    # Detach managed policies
    for policy_arn in $(aws iam list-attached-role-policies --role-name "$role" --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null); do
      aws iam detach-role-policy --role-name "$role" --policy-arn "$policy_arn" 2>/dev/null || true
    done
    # Delete inline policies
    for policy_name in $(aws iam list-role-policies --role-name "$role" --query 'PolicyNames[]' --output text 2>/dev/null); do
      aws iam delete-role-policy --role-name "$role" --policy-name "$policy_name" 2>/dev/null || true
    done
    aws iam delete-role --role-name "$role" 2>/dev/null || echo "  Failed"
  fi
done

# 11. CloudFormation stacks (including DELETE_FAILED)
echo ""
echo "--- CloudFormation Stacks ---"
for stack in $(aws cloudformation list-stacks --query 'StackSummaries[?contains(StackName,`alchemiser-prod`) || contains(StackName,`alchemiser-shared`)].StackName' --output text 2>/dev/null); do
  status=$(aws cloudformation describe-stacks --stack-name "$stack" --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "GONE")
  if [[ "$status" != "DELETE_COMPLETE" && "$status" != "GONE" ]]; then
    echo "Deleting stack: $stack (status: $status)"
    aws cloudformation delete-stack --stack-name "$stack" 2>/dev/null || echo "  Failed"
  fi
done

echo ""
echo "=== Done. Run this script again to verify everything is gone. ==="
