#!/bin/bash
# Creates IAM user for Streamlit dashboard with read-only access
# Run: ./scripts/create_dashboard_iam_user.sh

set -e

USER_NAME="alchemiser-dashboard-readonly"
POLICY_NAME="AlchemiserDashboardReadOnly"

echo "Creating IAM user: $USER_NAME"
aws iam create-user --user-name "$USER_NAME" --no-cli-pager

echo ""
echo "Creating IAM policy: $POLICY_NAME"
POLICY_ARN=$(aws iam create-policy --policy-name "$POLICY_NAME" --no-cli-pager --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DynamoDBReadProd",
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:DescribeTable"
            ],
            "Resource": [
                "arn:aws:dynamodb:us-east-1:*:table/alchemiser-prod-*",
                "arn:aws:dynamodb:us-east-1:*:table/alchemiser-prod-*/index/*"
            ]
        },
        {
            "Sid": "CloudWatchLogsReadProd",
            "Effect": "Allow",
            "Action": [
                "logs:FilterLogEvents",
                "logs:GetLogEvents",
                "logs:DescribeLogStreams",
                "logs:DescribeLogGroups"
            ],
            "Resource": [
                "arn:aws:logs:us-east-1:*:log-group:/aws/lambda/alchemiser-prod-*:*"
            ]
        }
    ]
}' --query 'Policy.Arn' --output text)

echo "Policy ARN: $POLICY_ARN"

echo ""
echo "Attaching policy to user..."
aws iam attach-user-policy --user-name "$USER_NAME" --policy-arn "$POLICY_ARN" --no-cli-pager

echo ""
echo "Creating access keys..."
echo "========================================"
aws iam create-access-key --user-name "$USER_NAME" --no-cli-pager
echo "========================================"

echo ""
echo "✅ Done! Copy the AccessKeyId and SecretAccessKey above for Streamlit secrets."
echo "⚠️  The SecretAccessKey will NOT be shown again!"
