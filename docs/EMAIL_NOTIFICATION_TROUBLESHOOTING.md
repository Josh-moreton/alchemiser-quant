# Email Notification Troubleshooting Guide

## Problem: Emails Not Being Sent

**Observed:** Trading runs complete successfully, but no email notifications are sent.

## Root Cause Analysis

### How Email Configuration Works

```
GitHub Secrets (EMAIL__PASSWORD)
    ↓
GitHub Actions CD workflow exports to environment
    ↓
scripts/deploy.sh passes to SAM deploy
    ↓
CloudFormation template.yaml sets Lambda environment variable
    ↓
Lambda execution: get_email_password() reads EMAIL__PASSWORD
    ↓
EmailClient sends email via SMTP
```

### Configuration Flow

**1. GitHub Repository Secrets**
- Secret name: `EMAIL__PASSWORD`
- Location: GitHub repo → Settings → Secrets and variables → Actions → Repository secrets
- **NOT** environment-specific secrets (dev/prod environments)

**2. GitHub Actions Workflow** (`.github/workflows/cd.yml`)
```yaml
- name: Prepare environment variables (dev)
  env:
    EMAIL__PASSWORD: ${{ secrets.EMAIL__PASSWORD }}  # ← Reads from repo secrets
  run: |
    if [ -n "$EMAIL__PASSWORD" ]; then echo "EMAIL__PASSWORD=$EMAIL__PASSWORD" >> $GITHUB_ENV; fi
```

**3. Deploy Script** (`scripts/deploy.sh`)
```bash
EMAIL_PASSWORD_PARAM=${EMAIL__PASSWORD:-""}

if [[ -n "$EMAIL_PASSWORD_PARAM" ]]; then
    PARAMS+=("EmailPassword=$EMAIL_PASSWORD_PARAM")  # ← Passes to SAM
fi
```

**4. CloudFormation Template** (`template.yaml`)
```yaml
Parameters:
  EmailPassword:
    Type: String
    Default: ""
    NoEcho: true

Globals:
  Function:
    Environment:
      Variables:
        EMAIL__PASSWORD: !If [ IsDev, !Ref EmailPassword, !Ref ProdEmailPassword ]
```

**5. Lambda Runtime**
- Environment variable: `EMAIL__PASSWORD`
- Code reads via: `get_email_password()` → checks `EMAIL__PASSWORD`, `EMAIL_PASSWORD`, `EMAIL__SMTP_PASSWORD`, `SMTP_PASSWORD`

### Why Emails Might Not Be Sent

#### Scenario 1: Secret Not Set in GitHub
**Check:**
```bash
# Go to GitHub repository
# Settings → Secrets and variables → Actions → Repository secrets
# Look for: EMAIL__PASSWORD
```

**If missing:** Add the secret with your SMTP password

**Test:**
```bash
# Check if secret is available in workflow
# In GitHub Actions logs, look for:
"Exporting dev ALPACA_* env vars for deploy.sh"
```

#### Scenario 2: Secret Set But Empty
**Check deploy.sh logic:**
```bash
if [[ -n "$EMAIL_PASSWORD_PARAM" ]]; then
    PARAMS+=("EmailPassword=$EMAIL_PASSWORD_PARAM")
fi
```

**If empty:** `EmailPassword` parameter not passed → Lambda gets empty string → `get_email_password()` returns `None` → EmailClient skips sending

**Lambda logs would show:**
```json
{"event": "Email password not found in environment variables"}
{"event": "Email configuration not available - skipping email notification"}
```

#### Scenario 3: Deployed Without Email Password
**Check CloudWatch Logs:**
```bash
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-dev --follow
```

**Look for:**
```json
{"event": "Email password not found - email notifications will be disabled"}
```

**Or:**
```json
{"event": "Email configuration not available - skipping email notification"}
```

**Fix:** Redeploy with email password set

#### Scenario 4: SMTP Authentication Failure
**Check CloudWatch Logs:**
```bash
aws logs filter-pattern "Failed to send email" /aws/lambda/the-alchemiser-v2-lambda-dev
```

**Look for:**
```json
{"event": "Failed to send email notification: ..."}
```

**Common causes:**
- Wrong password
- SMTP server blocked
- Port blocked (587)
- TLS/SSL issues

#### Scenario 5: Neutral Mode Enabled
**Check template.yaml:**
```yaml
EMAIL__NEUTRAL_MODE: true  # ← Emails might be suppressed
```

**Check CloudWatch Logs:**
```bash
# Look for neutral mode warnings
aws logs filter-pattern "neutral" /aws/lambda/the-alchemiser-v2-lambda-dev
```

**Fix:** Set `EMAIL__NEUTRAL_MODE: false` in template.yaml if you want real emails

## Diagnostic Steps

### Step 1: Verify GitHub Secret Exists

**Go to GitHub:**
```
Your repo → Settings → Secrets and variables → Actions → Repository secrets
```

**Check:**
- ✅ Secret named `EMAIL__PASSWORD` exists
- ✅ Value is not empty
- ✅ It's a **repository secret**, NOT an environment secret

### Step 2: Check Workflow Logs

**Go to GitHub Actions:**
```
Your repo → Actions → Latest CD workflow run
```

**Look for:**
```
Prepare environment variables (dev)
Exporting dev ALPACA_* env vars for deploy.sh
```

**Check if email password was exported:**
```bash
# If EMAIL__PASSWORD was set, you should see it exported
# (value redacted in logs due to NoEcho)
```

### Step 3: Check CloudFormation Stack Parameters

**AWS Console:**
```bash
aws cloudformation describe-stacks \
  --stack-name the-alchemiser-v2-dev \
  --query 'Stacks[0].Parameters[?ParameterKey==`EmailPassword`]'
```

**Expected output:**
```json
[
  {
    "ParameterKey": "EmailPassword",
    "ParameterValue": "****"  # Hidden due to NoEcho
  }
]
```

**If missing:** Parameter not passed during deployment

### Step 4: Check Lambda Environment Variables

**AWS Console:**
```bash
aws lambda get-function-configuration \
  --function-name the-alchemiser-v2-lambda-dev \
  --query 'Environment.Variables.EMAIL__PASSWORD'
```

**Expected output:**
```
"<your-password>"  # Should NOT be empty
```

**If empty or missing:** Lambda doesn't have the password

### Step 5: Check CloudWatch Logs for Email Errors

**Command:**
```bash
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-dev \
  --follow \
  --filter-pattern "email"
```

**Look for:**
- ✅ Good: `"Email notification sent successfully"`
- ❌ Bad: `"Email password not found"`
- ❌ Bad: `"Email configuration not available"`
- ❌ Bad: `"Failed to send email notification"`

### Step 6: Test Email Configuration Locally

**Create test script:**
```python
# test_email.py
import os
from the_alchemiser.shared.notifications import EmailClient

# Set environment variables
os.environ["EMAIL__SMTP_SERVER"] = "smtp.mail.me.com"
os.environ["EMAIL__SMTP_PORT"] = "587"
os.environ["EMAIL__FROM_EMAIL"] = "josh@rwxt.org"
os.environ["EMAIL__TO_EMAIL"] = "josh@rwxt.org"
os.environ["EMAIL__PASSWORD"] = "your-password-here"
os.environ["EMAIL__NEUTRAL_MODE"] = "false"

# Test sending
client = EmailClient()
result = client.send_plain_text(
    subject="Test from Alchemiser",
    text_content="This is a test email from your trading system."
)

print(f"Email sent: {result}")
```

**Run:**
```bash
poetry run python test_email.py
```

## Solutions

### Solution 1: Add GitHub Secret

**If secret is missing:**

1. Go to GitHub repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `EMAIL__PASSWORD`
4. Value: Your SMTP app-specific password
5. Click "Add secret"

**For iCloud Mail (smtp.mail.me.com):**
- Generate app-specific password: https://appleid.apple.com/account/manage
- Use the generated password, NOT your Apple ID password

### Solution 2: Redeploy with Email Password

**If Lambda doesn't have the password:**

**Option A: Manual deploy with password**
```bash
export EMAIL__PASSWORD="your-password"
./scripts/deploy.sh dev
```

**Option B: Trigger GitHub Actions deploy**
```bash
# Push to main branch or manually trigger workflow
# GitHub Actions → CD → Run workflow → Select dev environment
```

### Solution 3: Update CloudFormation Stack

**If stack was deployed without password:**

```bash
aws cloudformation update-stack \
  --stack-name the-alchemiser-v2-dev \
  --use-previous-template \
  --parameters \
    ParameterKey=Stage,ParameterValue=dev \
    ParameterKey=AlpacaKey,UsePreviousValue=true \
    ParameterKey=AlpacaSecret,UsePreviousValue=true \
    ParameterKey=AlpacaEndpoint,UsePreviousValue=true \
    ParameterKey=EmailPassword,ParameterValue="your-password" \
    ParameterKey=LoggingLevel,UsePreviousValue=true \
    ParameterKey=DslMaxWorkers,UsePreviousValue=true \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```

### Solution 4: Disable Neutral Mode

**If emails are suppressed:**

**Edit template.yaml:**
```yaml
EMAIL__NEUTRAL_MODE: false  # Changed from true
```

**Redeploy:**
```bash
./scripts/deploy.sh dev
```

### Solution 5: Test SMTP Connection

**If authentication fails:**

**Test SMTP manually:**
```python
import smtplib

server = smtplib.SMTP("smtp.mail.me.com", 587)
server.starttls()
server.login("josh@rwxt.org", "your-password")
print("✅ SMTP authentication successful!")
server.quit()
```

**If this fails:**
- Check password is correct
- Verify app-specific password is active
- Check firewall/network allows port 587
- Try alternative SMTP servers

## Quick Checklist

- [ ] GitHub secret `EMAIL__PASSWORD` exists and is not empty
- [ ] GitHub Actions CD workflow exports `EMAIL__PASSWORD`
- [ ] `deploy.sh` passes `EmailPassword` parameter to SAM
- [ ] CloudFormation stack has `EmailPassword` parameter
- [ ] Lambda environment variable `EMAIL__PASSWORD` is set
- [ ] CloudWatch logs don't show "Email password not found"
- [ ] `EMAIL__NEUTRAL_MODE` is `false` (if you want real emails)
- [ ] SMTP credentials are valid (test locally)
- [ ] Network allows outbound SMTP (port 587)

## Monitoring Email Delivery

**Add logging to verify emails are attempted:**

```bash
# Watch for email-related logs
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-dev \
  --follow \
  --filter-pattern "email|Email|SMTP"
```

**Expected flow:**
```json
{"event": "Email config loaded successfully"}
{"event": "Sending email notification", "subject": "..."}
{"event": "Email notification sent successfully to josh@rwxt.org"}
```

## Current Status (Based on Your Logs)

**From your test run logs:**
- ✅ Workflow completed successfully
- ✅ No explicit email errors in logs
- ❓ No "Email sent" confirmation logs either

**Most likely cause: Event-driven emails not yet implemented!**

## The Real Issue: Notification Architecture Not Fully Deployed

### How Email Notifications SHOULD Work

```
Trading completes
    ↓
Orchestrator handles TradeExecuted event
    ↓
Publishes TradingNotificationRequested to EventBridge
    ↓
EventBridge routes to NotificationService (lambda_handler_eventbridge)
    ↓
NotificationService sends email via EmailClient
```

### Why Emails Aren't Being Sent

**The notification service is NOT listening to events yet!**

Looking at your system architecture:
1. ✅ Trading workflow completes
2. ✅ Orchestrator publishes `TradeExecuted` event
3. ✅ Orchestrator tries to publish `TradingNotificationRequested` event
4. ❌ **EventBridge Rules are DISABLED** (we disabled them in this session!)
5. ❌ **No handler registered for `TradingNotificationRequested`**
6. ❌ Email never sent

### Proof from Code

**File:** `the_alchemiser/orchestration/event_driven_orchestrator.py` (line 492-493)
```python
# Send success notification
self._send_trading_notification(event, success=True)
```

**File:** `the_alchemiser/lambda_handler_eventbridge.py` (line 171-174)
```python
event_map: dict[str, type[BaseEvent]] = {
    "WorkflowStarted": WorkflowStarted,
    "SignalGenerated": SignalGenerated,
    "RebalancePlanned": RebalancePlanned,
    "TradeExecuted": TradeExecuted,
    "WorkflowCompleted": WorkflowCompleted,
    "WorkflowFailed": WorkflowFailed,
}
```

**Missing:** `TradingNotificationRequested` is NOT in the event map!

### The Fix

#### Step 1: Add TradingNotificationRequested to Event Map

**Edit:** `the_alchemiser/lambda_handler_eventbridge.py`

```python
from the_alchemiser.shared.events import (
    RebalancePlanned,
    SignalGenerated,
    TradeExecuted,
    TradingNotificationRequested,  # Add this
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
)

event_map: dict[str, type[BaseEvent]] = {
    "WorkflowStarted": WorkflowStarted,
    "SignalGenerated": SignalGenerated,
    "RebalancePlanned": RebalancePlanned,
    "TradeExecuted": TradeExecuted,
    "WorkflowCompleted": WorkflowCompleted,
    "WorkflowFailed": WorkflowFailed,
    "TradingNotificationRequested": TradingNotificationRequested,  # Add this
}
```

#### Step 2: Add Handler for TradingNotificationRequested

**Edit:** `the_alchemiser/lambda_handler_eventbridge.py`

```python
def _get_handler_for_event(
    container: ApplicationContainer, detail_type: str
) -> EventHandler | None:
    # Import handlers
    from the_alchemiser.execution_v2.handlers import TradingExecutionHandler
    from the_alchemiser.notifications_v2.service import NotificationService
    from the_alchemiser.portfolio_v2.handlers import PortfolioAnalysisHandler

    handler_map: dict[str, Callable[[], EventHandler]] = {
        "SignalGenerated": lambda: PortfolioAnalysisHandler(container),
        "RebalancePlanned": lambda: TradingExecutionHandler(container),
        "TradingNotificationRequested": lambda: NotificationService(container),  # Add this
    }

    factory = handler_map.get(detail_type)
    return factory() if factory else None
```

#### Step 3: Create EventBridge Rule for Trading Notifications

**Edit:** `template.yaml`

```yaml
# Event Rule: Route TradingNotificationRequested to NotificationService
TradingNotificationRule:
  Type: AWS::Events::Rule
  Properties:
    Name: !Sub "alchemiser-trading-notification-${Stage}"
    Description: Route TradingNotificationRequested events to notification handler
    EventBusName: !Ref AlchemiserEventBus
    State: ENABLED
    EventPattern:
      source:
        - alchemiser.orchestration
      detail-type:
        - TradingNotificationRequested
    Targets:
      - Arn: !GetAtt TradingSystemFunction.Arn
        Id: NotificationHandler
        RetryPolicy:
          MaximumRetryAttempts: 2
          MaximumEventAgeInSeconds: 1800
        DeadLetterConfig:
          Arn: !GetAtt EventDLQ.Arn

# Lambda Permission: Allow EventBridge to invoke Lambda for trading notifications
TradingNotificationPermission:
  Type: AWS::Lambda::Permission
  Properties:
    FunctionName: !Ref TradingSystemFunction
    Action: lambda:InvokeFunction
    Principal: events.amazonaws.com
    SourceArn: !GetAtt TradingNotificationRule.Arn
```

#### Step 4: Ensure Email Password is Set

**Check GitHub Secrets:**
- Go to: Settings → Secrets and variables → Actions → Repository secrets
- Verify: `EMAIL__PASSWORD` exists with your SMTP password

**Redeploy:**
```bash
./scripts/deploy.sh dev
```

### When Emails ARE Sent

**Email notifications are sent:**
1. ✅ After every trade execution (success or failure)
2. ✅ When TradeExecuted event is processed by orchestrator
3. ✅ When TradingNotificationRequested event reaches NotificationService

**Emails include:**
- Trading summary (success/failure)
- Orders executed
- Strategy signals
- Portfolio changes
- Execution metrics

### Quick Fix Summary

**Current state:**
- Trading works ✅
- Events published ✅
- EventBridge routes events ❌ (rules disabled)
- Email handler registered ❌ (not in event map)
- Emails sent ❌

**After fix:**
- Add `TradingNotificationRequested` to event map
- Add `NotificationService` to handler map
- Create EventBridge Rule for trading notifications
- Re-enable ALL EventBridge Rules
- Redeploy

**Then you'll get emails!** 📧
