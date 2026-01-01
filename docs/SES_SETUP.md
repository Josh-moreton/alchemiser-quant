# Amazon SES Setup Guide for The Alchemiser

This guide covers the complete setup process for Amazon SES (Simple Email Service) to send email notifications from The Alchemiser trading system.

## Overview

The Alchemiser uses Amazon SES to send email notifications with:
- **HTML + Plain Text** templates for rich formatting
- **Environment-safe routing** to prevent accidental emails in non-prod
- **Deduplication** to prevent notification spam
- **Recovery tracking** to send "fixed" emails when errors clear

## Prerequisites

- AWS Account with appropriate permissions
- Domain ownership (for domain-based sending) OR ability to verify email addresses
- Access to DNS records (for domain-based setup)

## Setup Steps

### 1. Choose Sending Identity

You have two options:

#### Option A: Domain-Based Sending (Recommended for Production)
- **Pros**: Professional, supports any email address at your domain, better deliverability
- **Cons**: Requires DNS access and verification
- **Use Case**: Production deployments

#### Option B: Email Address Verification
- **Pros**: Quick setup, no DNS required
- **Cons**: Must verify each sender address individually, less flexible
- **Use Case**: Development and testing

**Recommendation**: Use Option A (domain-based) for production.

### 2. Verify Your Domain or Email Address

#### For Domain-Based Sending:

1. Go to AWS Console → Amazon SES → **Verified identities**
2. Click **Create identity**
3. Select **Domain** as identity type
4. Enter your domain (e.g., `rwxt.org`)
5. Check **Generate DKIM settings** (recommended)
6. Click **Create identity**

AWS will provide DNS records you need to add. See section below for DNS configuration.

#### For Email Address Verification:

1. Go to AWS Console → Amazon SES → **Verified identities**
2. Click **Create identity**
3. Select **Email address** as identity type
4. Enter your sender email (e.g., `notifications@rwxt.org`)
5. Click **Create identity**
6. Check your inbox for a verification email and click the link

### 3. Configure DNS Records (Domain-Based Only)

You need to add the following DNS records:

#### DKIM Records (Provided by AWS)
AWS will provide 3 CNAME records. Add all of them to your DNS:

```
_domainkey1.rwxt.org → <aws-provided-value>
_domainkey2.rwxt.org → <aws-provided-value>
_domainkey3.rwxt.org → <aws-provided-value>
```

**Verification**: May take 24-72 hours. Check the SES console for status.

#### SPF Record
Add or update your SPF TXT record:

```
TXT @ "v=spf1 include:amazonses.com ~all"
```

If you already have an SPF record, add `include:amazonses.com` to it:

```
TXT @ "v=spf1 include:_spf.google.com include:amazonses.com ~all"
```

**Important**: Only one SPF record is allowed per domain. Merge if you have existing SPF.

#### DMARC Record (Highly Recommended)
Add a DMARC policy to improve deliverability:

```
TXT _dmarc "v=DMARC1; p=none; rua=mailto:postmaster@rwxt.org"
```

**Policy Options**:
- `p=none`: Monitor only (recommended for initial setup)
- `p=quarantine`: Quarantine suspicious emails (after monitoring)
- `p=reject`: Reject failing emails (strictest)

**Best Practice**: Start with `p=none`, monitor reports, then move to `p=quarantine` or `p=reject`.

### 4. Request Production Access (If in Sandbox)

By default, new SES accounts are in **sandbox mode** with limitations:
- Can only send to verified email addresses
- Limited to 200 emails per day
- Limited to 1 email per second

#### Check Sandbox Status:
1. Go to AWS Console → Amazon SES → **Account dashboard**
2. Look for "Email sending" section
3. If it says "Sandbox", you're limited

#### Request Production Access:
1. In the Account dashboard, click **Request production access**
2. Fill out the form:
   - **Mail Type**: Transactional
   - **Website URL**: Your website or GitHub repo
   - **Use Case Description**: Example text below
   - **Expected sending volume**: Be realistic (e.g., 100 emails/day)
   - **How you will handle bounces**: "We monitor bounce rates via SES events and stop sending to bouncing addresses"
3. Submit and wait for approval (usually 24-48 hours)

**Example Use Case Description**:
```
We operate an automated quantitative trading system that sends operational notifications
to internal team members. Email types include:
- Daily trading run summaries (success/failure)
- System error alerts and recovery notifications
- Data pipeline status updates

All emails are transactional, sent to a small list of verified team members, and related
to system operations. We do not send marketing emails or bulk communications.
```

### 5. Configure Per-Environment Sending

The Alchemiser supports per-environment configuration:

#### Production (`stage=prod`):
- Sends to real recipients from `NOTIFICATIONS_TO_PROD`
- Requires `ALLOW_REAL_EMAILS=true` (set by default in template.yaml)

#### Non-Production (`stage=dev`, `stage=staging`):
- **Default**: Sends to `NOTIFICATIONS_TO_NONPROD` (safe override)
- **Option 1**: Use `NOTIFICATIONS_OVERRIDE_TO` to force specific recipients
- **Option 2**: Set `ALLOW_REAL_EMAILS=true` to send to real addresses (not recommended)

**Environment Variables** (configured in `template.yaml`):
```yaml
SES_FROM_ADDRESS: notifications@rwxt.org
SES_REPLY_TO_ADDRESS: notifications@rwxt.org
SES_REGION: !Ref AWS::Region
NOTIFICATIONS_TO_PROD: notifications@rwxt.org
NOTIFICATIONS_TO_NONPROD: notifications@rwxt.org
ALLOW_REAL_EMAILS: !If [ IsProduction, "true", "false" ]
```

### 6. Optional: Create Configuration Set

Configuration sets enable event tracking (deliveries, bounces, complaints):

1. Go to AWS Console → Amazon SES → **Configuration sets**
2. Click **Create set**
3. Enter a name (e.g., `alchemiser-email-tracking`)
4. Add event destinations:
   - **CloudWatch**: Publish metrics (deliveries, bounces, complaints)
   - **SNS**: Get real-time notifications on bounces/complaints
   - **EventBridge**: Route events to EventBridge (advanced)

5. Update `template.yaml` to use the configuration set:
```yaml
SES_CONFIGURATION_SET: alchemiser-email-tracking
```

**Benefits**:
- Monitor delivery rates
- Track bounce and complaint rates
- Alert on issues

### 7. Test Email Sending

#### Option 1: Via AWS Console
1. Go to Amazon SES → **Email addresses** (or **Domains**)
2. Select your verified identity
3. Click **Send test email**
4. Enter recipient and content
5. Send

#### Option 2: Via Lambda (Recommended)
After deployment, trigger a test notification:
```bash
# Test in dev environment
aws lambda invoke \
  --function-name alchemiser-dev-notifications \
  --payload '{"test": true}' \
  response.json
```

Check CloudWatch Logs for:
- `"Email sent via SES"` log entry
- `message_id` from SES
- Any error messages

### 8. Monitor and Troubleshoot

#### CloudWatch Logs
All email sends are logged with structured data:
```json
{
  "message": "Email sent via SES",
  "message_id": "abc123...",
  "to_addresses": ["notifications@rwxt.org"],
  "subject_preview": "Alchemiser Daily Run — SUCCESS — 2026-01-01",
  "routing_override": false,
  "stage": "prod"
}
```

#### SES Sending Statistics
Monitor in AWS Console → Amazon SES → **Sending statistics**:
- **Sent**: Total emails sent
- **Deliveries**: Successfully delivered
- **Bounces**: Hard bounces (permanent failures)
- **Complaints**: Spam complaints

**Best Practices**:
- Keep bounce rate < 5%
- Keep complaint rate < 0.1%
- Set up alarms for high bounce/complaint rates

#### Common Issues

**Issue**: "Email address not verified"
- **Solution**: Verify email in SES console or use verified domain

**Issue**: "Account in sandbox mode"
- **Solution**: Request production access (see Step 4)

**Issue**: "Daily sending quota exceeded"
- **Solution**: Request quota increase or wait 24 hours (quotas reset daily)

**Issue**: "DNS verification pending"
- **Solution**: Wait up to 72 hours for DNS propagation; verify records are correct

**Issue**: "MessageRejected: Email address is not verified"
- **Solution**: In sandbox mode, you can only send to verified addresses. Request production access.

## Deployment Checklist

Before deploying to production:

- [ ] Domain verified in SES (or sender email verified)
- [ ] DKIM records added to DNS and verified (green checkmark in SES console)
- [ ] SPF record added to DNS
- [ ] DMARC record added to DNS (recommended)
- [ ] Production access requested and approved (if in sandbox)
- [ ] Configuration set created (optional but recommended)
- [ ] Test email sent successfully
- [ ] `NOTIFICATIONS_TO_PROD` configured with correct recipient(s)
- [ ] Non-prod environments configured with safe override addresses
- [ ] Monitoring and alarms set up (optional)

## Security Notes

1. **Never hardcode email addresses** in code. Use environment variables.
2. **Non-prod safety**: Always use `NOTIFICATIONS_OVERRIDE_TO` or default non-prod routing to prevent accidental emails to real users.
3. **IAM Permissions**: The NotificationsFunction has least-privilege IAM permissions for SES:
   ```yaml
   - Effect: Allow
     Action:
       - ses:SendEmail
       - ses:SendRawEmail
     Resource: "*"
   ```
4. **Secrets**: SES credentials are managed by IAM roles. No additional secrets needed.

## Cost Estimate

Amazon SES pricing (as of 2026):
- **First 62,000 emails/month**: $0.10 per 1,000 emails
- **Beyond 62,000 emails/month**: $0.12 per 1,000 emails
- **Data transfer**: $0.12 per GB (outbound)

**Example**: 
- 100 emails/day × 30 days = 3,000 emails/month
- Cost: 3 × $0.10 = **$0.30/month**

Very cost-effective for operational notifications.

## References

- [Amazon SES Developer Guide](https://docs.aws.amazon.com/ses/latest/dg/)
- [SPF Record Syntax](https://tools.ietf.org/html/rfc7208)
- [DKIM Overview](https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim.html)
- [DMARC Overview](https://dmarc.org/)
- [SES Sandbox Removal](https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html)

## Support

For issues:
1. Check CloudWatch Logs: `/aws/lambda/alchemiser-{stage}-notifications`
2. Check SES Console: Account dashboard and sending statistics
3. Review this guide for common issues
4. Contact AWS Support if production access request is delayed
