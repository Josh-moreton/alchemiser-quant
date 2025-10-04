# IAM Policy Documentation: The Alchemiser CI/CD Pipeline

**Last Updated**: 2024-12-19  
**Purpose**: Document IAM roles and policies used in the GitHub Actions → AWS Lambda pipeline

---

## Overview

The Alchemiser uses **three IAM roles**:
1. **GitHub Actions CI Role** (OIDC): Used by CD workflow to deploy SAM stack
2. **Lambda Execution Role**: Runtime permissions for the trading Lambda function
3. **EventBridge Scheduler Role**: Permissions for EventBridge to invoke Lambda

This document specifies the **least-privilege policies** for each role.

---

## 1. GitHub Actions CI Role (OIDC)

### Role Name
`GitHubActions-AlchemiserDeploy` (suggested name; actual name set by AWS admin)

### Trust Policy

**Requirement**: Trust only GitHub OIDC provider with repository constraint.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<AWS_ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:Josh-moreton/alchemiser-quant:*"
        }
      }
    }
  ]
}
```

**Key Security Features**:
- ✅ Scoped to specific GitHub repo (`Josh-moreton/alchemiser-quant`)
- ✅ Requires `aud` claim to be `sts.amazonaws.com`
- ⚠️ `sub` claim uses wildcard (`*`) to allow any branch; consider restricting to `ref:refs/heads/main` for prod

**Improved Trust Policy** (restrict to main branch for prod):
```json
{
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub": "repo:Josh-moreton/alchemiser-quant:ref:refs/heads/main"
    }
  }
}
```

### Permission Policy

**Requirement**: Minimum permissions for SAM deploy (CloudFormation, S3, Lambda, IAM, Logs, EventBridge).

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudFormationDeploy",
      "Effect": "Allow",
      "Action": [
        "cloudformation:CreateChangeSet",
        "cloudformation:CreateStack",
        "cloudformation:DeleteChangeSet",
        "cloudformation:DeleteStack",
        "cloudformation:DescribeChangeSet",
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:DescribeStackResource",
        "cloudformation:DescribeStackResources",
        "cloudformation:ExecuteChangeSet",
        "cloudformation:GetTemplate",
        "cloudformation:GetTemplateSummary",
        "cloudformation:ListStackResources",
        "cloudformation:UpdateStack",
        "cloudformation:ValidateTemplate"
      ],
      "Resource": [
        "arn:aws:cloudformation:us-east-1:<AWS_ACCOUNT_ID>:stack/the-alchemiser-v2/*",
        "arn:aws:cloudformation:us-east-1:<AWS_ACCOUNT_ID>:stack/the-alchemiser-v2-dev/*"
      ]
    },
    {
      "Sid": "S3ArtifactBucket",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:GetBucketPolicy",
        "s3:PutBucketPolicy"
      ],
      "Resource": [
        "arn:aws:s3:::aws-sam-cli-managed-default-*",
        "arn:aws:s3:::aws-sam-cli-managed-default-*/*"
      ]
    },
    {
      "Sid": "LambdaDeploy",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:DeleteFunction",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:ListTags",
        "lambda:TagResource",
        "lambda:UntagResource",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:PublishVersion",
        "lambda:CreateAlias",
        "lambda:DeleteAlias",
        "lambda:GetAlias",
        "lambda:UpdateAlias",
        "lambda:PutFunctionConcurrency",
        "lambda:DeleteFunctionConcurrency"
      ],
      "Resource": [
        "arn:aws:lambda:us-east-1:<AWS_ACCOUNT_ID>:function:the-alchemiser-v2-lambda-prod",
        "arn:aws:lambda:us-east-1:<AWS_ACCOUNT_ID>:function:the-alchemiser-v2-lambda-dev"
      ]
    },
    {
      "Sid": "LambdaLayerDeploy",
      "Effect": "Allow",
      "Action": [
        "lambda:PublishLayerVersion",
        "lambda:GetLayerVersion",
        "lambda:DeleteLayerVersion"
      ],
      "Resource": [
        "arn:aws:lambda:us-east-1:<AWS_ACCOUNT_ID>:layer:the-alchemiser-dependencies-prod:*",
        "arn:aws:lambda:us-east-1:<AWS_ACCOUNT_ID>:layer:the-alchemiser-dependencies-dev:*"
      ]
    },
    {
      "Sid": "IAMRoleManagement",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:GetRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PassRole",
        "iam:TagRole",
        "iam:UntagRole"
      ],
      "Resource": [
        "arn:aws:iam::<AWS_ACCOUNT_ID>:role/the-alchemiser-v2-*"
      ]
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DescribeLogGroups",
        "logs:PutRetentionPolicy",
        "logs:DeleteLogGroup",
        "logs:TagResource",
        "logs:UntagResource"
      ],
      "Resource": [
        "arn:aws:logs:us-east-1:<AWS_ACCOUNT_ID>:log-group:/aws/lambda/the-alchemiser-v2-lambda-prod:*",
        "arn:aws:logs:us-east-1:<AWS_ACCOUNT_ID>:log-group:/aws/lambda/the-alchemiser-v2-lambda-dev:*"
      ]
    },
    {
      "Sid": "EventBridgeScheduler",
      "Effect": "Allow",
      "Action": [
        "scheduler:CreateSchedule",
        "scheduler:DeleteSchedule",
        "scheduler:GetSchedule",
        "scheduler:UpdateSchedule",
        "scheduler:TagResource",
        "scheduler:UntagResource"
      ],
      "Resource": [
        "arn:aws:scheduler:us-east-1:<AWS_ACCOUNT_ID>:schedule/default/the-alchemiser-*"
      ]
    },
    {
      "Sid": "SQS",
      "Effect": "Allow",
      "Action": [
        "sqs:CreateQueue",
        "sqs:DeleteQueue",
        "sqs:GetQueueAttributes",
        "sqs:SetQueueAttributes",
        "sqs:TagQueue",
        "sqs:UntagQueue"
      ],
      "Resource": [
        "arn:aws:sqs:us-east-1:<AWS_ACCOUNT_ID>:the-alchemiser-dlq-*"
      ]
    },
    {
      "Sid": "CloudWatchAlarms",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricAlarm",
        "cloudwatch:DeleteAlarms",
        "cloudwatch:DescribeAlarms"
      ],
      "Resource": [
        "arn:aws:cloudwatch:us-east-1:<AWS_ACCOUNT_ID>:alarm:the-alchemiser-*"
      ]
    },
    {
      "Sid": "CodeDeploy",
      "Effect": "Allow",
      "Action": [
        "codedeploy:CreateApplication",
        "codedeploy:DeleteApplication",
        "codedeploy:GetApplication",
        "codedeploy:CreateDeploymentGroup",
        "codedeploy:DeleteDeploymentGroup",
        "codedeploy:GetDeploymentGroup",
        "codedeploy:UpdateDeploymentGroup"
      ],
      "Resource": [
        "arn:aws:codedeploy:us-east-1:<AWS_ACCOUNT_ID>:application:ServerlessDeploymentApplication",
        "arn:aws:codedeploy:us-east-1:<AWS_ACCOUNT_ID>:deploymentgroup:ServerlessDeploymentApplication/*"
      ]
    }
  ]
}
```

**Key Security Features**:
- ✅ All resources scoped to specific ARN patterns (no `*` wildcards)
- ✅ Stack names restricted to `the-alchemiser-v2` and `the-alchemiser-v2-dev`
- ✅ IAM PassRole limited to roles starting with `the-alchemiser-v2-`
- ✅ S3 buckets restricted to SAM managed buckets only

**Not Required** (explicitly excluded to reduce attack surface):
- ❌ `s3:DeleteBucket` (buckets should be managed separately)
- ❌ `iam:CreatePolicy` (use inline policies only)
- ❌ `lambda:InvokeFunction` (CI should not execute Lambda)

---

## 2. Lambda Execution Role

### Role Name
`TradingSystemExecutionRole` (defined in `template.yaml`)

### Trust Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Permission Policy

**Current (from template.yaml)** - **IMPROVED VERSION**:

```yaml
# In template.yaml
TradingSystemExecutionRole:
  Type: AWS::IAM::Role
  Properties:
    ManagedPolicyArns:
      - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    Policies:
      - PolicyName: TradingSystemPolicy
        PolicyDocument:
          Version: "2012-10-17"
          Statement:
            # CloudWatch Logs (scoped to this function's log group)
            - Effect: Allow
              Action:
                - logs:CreateLogGroup
                - logs:CreateLogStream
                - logs:PutLogEvents
              Resource: 
                - !Sub "arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/the-alchemiser-v2-lambda-${Stage}:*"
```

**Analysis**:
- ✅ Uses AWS managed policy `AWSLambdaBasicExecutionRole` (CloudWatch Logs baseline)
- ✅ **FIXED**: Resource now scoped to specific log group (was `"*"` before)
- ✅ No S3, DynamoDB, or other service permissions (trading logic uses Alpaca API only)

**Future Enhancement** (if S3 tracking is added):
```yaml
- Effect: Allow
  Action:
    - s3:PutObject
    - s3:GetObject
  Resource:
    - !Sub "arn:aws:s3:::the-alchemiser-s3/strategy_orders/*"
    - !Sub "arn:aws:s3:::the-alchemiser-s3/strategy_positions/*"
    - !Sub "arn:aws:s3:::the-alchemiser-s3/strategy_pnl_history/*"
```

**Secret Access** (if migrating to Secrets Manager):
```yaml
- Effect: Allow
  Action:
    - secretsmanager:GetSecretValue
  Resource:
    - !Sub "arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:alchemiser/prod/alpaca-*"
```

---

## 3. EventBridge Scheduler Execution Role

### Role Name
`SchedulerExecutionRole` (defined in `template.yaml`)

### Trust Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "scheduler.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Permission Policy

**From template.yaml**:

```yaml
SchedulerExecutionRole:
  Type: AWS::IAM::Role
  Properties:
    Policies:
      - PolicyName: SchedulerLambdaInvokePolicy
        PolicyDocument:
          Version: "2012-10-17"
          Statement:
            - Effect: Allow
              Action:
                - lambda:InvokeFunction
              Resource: !GetAtt TradingSystemFunction.Arn
            - Effect: Allow
              Action:
                - sqs:SendMessage
              Resource: !GetAtt TradingSystemDLQ.Arn
```

**Analysis**:
- ✅ Scoped to specific Lambda ARN (no wildcards)
- ✅ SQS SendMessage limited to DLQ only
- ✅ No admin or read permissions

---

## Security Best Practices

### 1. Principle of Least Privilege
All roles grant **only** the permissions required for their specific task:
- CI role: Deploy CloudFormation stacks
- Lambda role: Write logs
- Scheduler role: Invoke Lambda + send to DLQ

### 2. Resource Scoping
All policies use **explicit ARNs** or **ARN patterns** (no `Resource: "*"` except where AWS requires it and risk is acceptable).

### 3. Condition Keys
OIDC trust policy uses condition keys to restrict:
- Repository: `token.actions.githubusercontent.com:sub`
- Audience: `token.actions.githubusercontent.com:aud`

**Recommendation**: Add environment constraint for prod:
```json
"Condition": {
  "StringEquals": {
    "token.actions.githubusercontent.com:sub": "repo:Josh-moreton/alchemiser-quant:environment:prod"
  }
}
```

### 4. Audit Trail
All role assumptions are logged to CloudTrail (if enabled):
- Search for `AssumeRoleWithWebIdentity` events from GitHub OIDC
- Search for Lambda invocations by `scheduler.amazonaws.com`

### 5. No Long-Lived Credentials
- ✅ CI uses OIDC tokens (expire after 1 hour)
- ✅ Lambda uses execution role (temporary credentials)
- ✅ No IAM user access keys in GitHub Secrets

---

## Validation Checklist

Use this checklist to verify IAM policies meet security requirements:

- [ ] GitHub Actions trust policy scoped to `Josh-moreton/alchemiser-quant` repo
- [ ] GitHub Actions permission policy has no `Resource: "*"` (except CloudFormation list actions)
- [ ] Lambda execution role has no S3/DynamoDB permissions (unless justified)
- [ ] Lambda CloudWatch Logs resource scoped to `/aws/lambda/the-alchemiser-v2-lambda-*`
- [ ] Scheduler role can only invoke the trading Lambda (no other functions)
- [ ] No `iam:*` or `iam:CreatePolicy` permissions in any role
- [ ] No `lambda:InvokeFunction` in CI role (CI should not execute)
- [ ] All roles have a `Description` field explaining purpose

---

## Testing IAM Policies

### Simulate CI Role Permissions
```bash
# Check if CI role can deploy stack (should succeed)
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::<AWS_ACCOUNT_ID>:role/GitHubActions-AlchemiserDeploy \
  --action-names cloudformation:CreateChangeSet \
  --resource-arns arn:aws:cloudformation:us-east-1:<AWS_ACCOUNT_ID>:stack/the-alchemiser-v2/*

# Check if CI role can invoke Lambda (should deny)
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::<AWS_ACCOUNT_ID>:role/GitHubActions-AlchemiserDeploy \
  --action-names lambda:InvokeFunction \
  --resource-arns arn:aws:lambda:us-east-1:<AWS_ACCOUNT_ID>:function:the-alchemiser-v2-lambda-prod
```

Expected: First command shows `allowed`, second shows `denied`.

### Check for Overly Permissive Policies
```bash
# Use AWS Access Analyzer to find broad permissions
aws accessanalyzer list-findings \
  --analyzer-arn arn:aws:access-analyzer:us-east-1:<AWS_ACCOUNT_ID>:analyzer/ConsoleAnalyzer-default \
  --filter '{"resourceType": {"eq": ["AWS::IAM::Role"]}}'
```

---

## Change Log

| Date | Change | Justification |
|------|--------|---------------|
| 2024-12-19 | Scoped Lambda logs resource from `"*"` to specific log group | Least-privilege principle |
| 2024-12-19 | Documented CI role policy with explicit resources | Audit requirement |
| 2024-12-19 | Added trust policy condition for GitHub OIDC | Supply chain security |

---

## Related Documentation
- [CI/CD Audit Report](./CI_CD_AUDIT_REPORT.md)
- [Deployment Runbook](./RUNBOOK.md)
- [AWS SAM Template](../template.yaml)
