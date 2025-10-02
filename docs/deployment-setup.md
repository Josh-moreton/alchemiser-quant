# Automated Deployment Setup Guide

This guide walks you through setting up automated Lambda deployments via GitHub Releases.

## Prerequisites

- AWS Account with administrator access
- GitHub repository with admin permissions
- Alpaca trading account (paper and/or live)

## Step 1: Configure AWS OIDC Provider

1. **Go to AWS IAM Console** → Identity Providers
2. **Add Provider:**
   - Provider Type: `OpenID Connect`
   - Provider URL: `https://token.actions.githubusercontent.com`
   - Audience: `sts.amazonaws.com`
3. **Click "Add provider"**

## Step 2: Create IAM Role for GitHub Actions

1. **Go to AWS IAM Console** → Roles
2. **Create Role:**
   - Trusted entity type: `Web identity`
   - Identity provider: `token.actions.githubusercontent.com`
   - Audience: `sts.amazonaws.com`
3. **Add Trust Policy:**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
         },
         "Action": "sts:AssumeRoleWithWebIdentity",
         "Condition": {
           "StringEquals": {
             "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
           },
           "StringLike": {
             "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_ORG/alchemiser-quant:*"
           }
         }
       }
     ]
   }
   ```
   **Replace:**
   - `YOUR_ACCOUNT_ID` with your AWS account ID
   - `YOUR_GITHUB_ORG` with your GitHub organization or username

4. **Attach Policies:**
   
   Option A - Use AWS Managed Policies (Quick Setup):
   - `AWSCloudFormationFullAccess`
   - `AWSLambda_FullAccess`
   - `IAMFullAccess`
   - `AmazonS3FullAccess`
   - `CloudWatchLogsFullAccess`
   - `AmazonEventBridgeFullAccess`

   Option B - Create Custom Policy (Recommended for Production):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "cloudformation:*",
           "lambda:*",
           "iam:CreateRole",
           "iam:DeleteRole",
           "iam:PutRolePolicy",
           "iam:DeleteRolePolicy",
           "iam:GetRole",
           "iam:PassRole",
           "iam:AttachRolePolicy",
           "iam:DetachRolePolicy",
           "s3:CreateBucket",
           "s3:PutObject",
           "s3:GetObject",
           "s3:ListBucket",
           "logs:CreateLogGroup",
           "logs:PutRetentionPolicy",
           "logs:DeleteLogGroup",
           "scheduler:*",
           "sqs:*"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

5. **Name the Role:** `GitHubDeployRole`
6. **Copy the Role ARN** (e.g., `arn:aws:iam::123456789012:role/GitHubDeployRole`)

## Step 3: Configure GitHub Secrets

1. **Go to GitHub Repository** → Settings → Secrets and variables → Actions
2. **Add the following Repository Secrets:**

   ### Required for All Deployments:
   - **Name:** `AWS_DEPLOY_ROLE_ARN`
     - **Value:** `arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubDeployRole`

   ### Required for Dev/Paper Trading:
   - **Name:** `ALPACA_KEY`
     - **Value:** Your Alpaca paper trading API key
   - **Name:** `ALPACA_SECRET`
     - **Value:** Your Alpaca paper trading secret key

   ### Optional for Dev:
   - **Name:** `ALPACA_ENDPOINT`
     - **Value:** `https://paper-api.alpaca.markets/v2` (default if not set)

   ### Required for Production/Live Trading:
   - **Name:** `PROD_ALPACA_KEY`
     - **Value:** Your Alpaca live trading API key
   - **Name:** `PROD_ALPACA_SECRET`
     - **Value:** Your Alpaca live trading secret key

   ### Optional for Production:
   - **Name:** `PROD_ALPACA_ENDPOINT`
     - **Value:** `https://api.alpaca.markets` (default if not set)
   - **Name:** `PROD_EMAIL_PASSWORD`
     - **Value:** Your SMTP password for email notifications

## Step 4: Configure GitHub Variables (Optional)

1. **Go to GitHub Repository** → Settings → Secrets and variables → Actions → Variables tab
2. **Add Repository Variable:**
   - **Name:** `AWS_REGION`
   - **Value:** `us-east-1` (or your preferred region)

## Step 5: Test the Deployment

### Test Dev Deployment:

1. **Create a dev release tag:**
   ```bash
   git tag v1.0.0-dev
   git push origin v1.0.0-dev
   ```

2. **Create a GitHub Release:**
   - Go to GitHub → Releases → Draft a new release
   - Choose tag: `v1.0.0-dev`
   - Title: `Dev Release v1.0.0-dev`
   - Description: Test deployment to dev environment
   - Mark as pre-release: ✓
   - Click "Publish release"

3. **Monitor the deployment:**
   - Go to Actions tab
   - Watch the "Deploy Lambda via SAM" workflow
   - Check for successful deployment

### Test Prod Deployment:

1. **Create a production release tag:**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Create a GitHub Release:**
   - Go to GitHub → Releases → Draft a new release
   - Choose tag: `v1.0.0`
   - Title: `Release v1.0.0`
   - Description: Production deployment
   - Click "Publish release"

3. **Monitor the deployment:**
   - Go to Actions tab
   - Watch the "Deploy Lambda via SAM" workflow
   - ⚠️ **WARNING:** This deploys to production with live trading!

## Step 6: Verify Deployment

### Check Lambda Function:

```bash
# List Lambda functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `the-alchemiser`)].FunctionName'

# Check function configuration
aws lambda get-function --function-name the-alchemiser-v2-lambda-dev

# View logs
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-dev --follow
```

### Check CloudFormation Stack:

```bash
# List stacks
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE

# Describe stack
aws cloudformation describe-stacks --stack-name the-alchemiser-v2-dev
```

## Troubleshooting

### Workflow Fails with "Role ARN not found"
- Verify `AWS_DEPLOY_ROLE_ARN` secret is set correctly
- Ensure the IAM role exists in AWS
- Check the role ARN format: `arn:aws:iam::ACCOUNT_ID:role/ROLE_NAME`

### Workflow Fails with "Access Denied"
- Verify the IAM role has necessary permissions
- Check the trust policy includes your GitHub repository
- Ensure the OIDC provider is configured correctly

### Deployment Fails with "Missing Parameter"
- Verify all required secrets are set for the environment
- Dev requires: `ALPACA_KEY`, `ALPACA_SECRET`
- Prod requires: `PROD_ALPACA_KEY`, `PROD_ALPACA_SECRET`

### SAM Build Fails
- Check Poetry dependencies are valid
- Ensure `template.yaml` is in repository root
- Verify Python 3.12 compatibility

## Next Steps

After successful setup:

1. **Create releases for deployments** instead of manual `make deploy`
2. **Use semantic versioning** for release tags (v1.0.0, v1.0.1, etc.)
3. **Monitor deployments** in GitHub Actions tab
4. **Review CloudWatch Logs** for Lambda execution
5. **Set up notifications** for deployment failures (GitHub Actions notifications)

## Security Best Practices

✅ **Do:**
- Use OIDC authentication (no long-lived keys)
- Store sensitive data in GitHub Secrets
- Use separate credentials for dev and prod
- Regularly rotate API keys
- Monitor deployment logs

❌ **Don't:**
- Commit secrets to repository
- Share AWS credentials
- Use production keys in dev environment
- Deploy directly to production without testing
- Skip security updates

## Additional Resources

- [GitHub Actions OIDC with AWS](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [AWS SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [CloudFormation Best Practices](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html)
