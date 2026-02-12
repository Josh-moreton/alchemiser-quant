# Notification Architecture Quick Reference

## TL;DR - What Should I Do?

### Your Question: "Should daily emails be event-driven or scheduled?"

**Answer: EVENT-DRIVEN (Keep current approach)**

✅ Your current approach is **correct and follows AWS best practices**

**Why?**
- Your events already contain pre-aggregated data (P&L, portfolio snapshot, strategy performance)
- No need to query DynamoDB (more efficient)
- Reports sent immediately after workflow completion (timely)
- Natural trigger point aligns with business logic

**When to use scheduled instead:**
- If you need to aggregate data from multiple sources at a fixed time
- If data changes constantly and you want a specific time snapshot
- **NOT YOUR CASE** - your data is already aggregated in events

---

### Your Question: "Should errors use CloudWatch as source?"

**Answer: YES for infrastructure errors, NO for application errors**

#### Infrastructure Errors → CloudWatch Alarms → SNS (RECOMMENDED)

Use CloudWatch Alarms for:
- ✅ Lambda timeouts
- ✅ Lambda crashes
- ✅ DLQ messages
- ✅ Stuck execution runs
- ✅ Stuck aggregation sessions
- ✅ Out of memory errors

**Why?**
- Faster delivery (no Lambda cold start)
- More reliable (no custom code execution)
- Works even if application is completely broken
- Breaks circular dependency (NotificationsErrorsAlarm won't trigger NotificationsFunction)

#### Application Errors → EventBridge → NotificationsFunction (KEEP CURRENT)

Keep EventBridge for:
- ✅ WorkflowFailed events
- ✅ Lambda async invocation failures
- ✅ Business logic errors

**Why?**
- These events contain rich domain context (which strategy failed, which symbol, etc.)
- NotificationsFunction adds value by formatting and enriching
- You want detailed error messages with suggested actions

---

### Your Question: "Should we be decoupled from main flow?"

**Answer: YES for critical errors, NO for business reports**

```
CRITICAL ERRORS (Decouple)
Infrastructure failures → CloudWatch Alarm → SNS → Email
- Independent of application state
- Faster, more reliable
- Works even if everything is broken

APPLICATION ERRORS & REPORTS (Keep Coupled)
Business logic → EventBridge → NotificationsFunction → Email
- Rich context and formatting
- Pre-aggregated data
- Natural trigger point
```

---

## Decision Matrix

| Notification Type | Current Approach | Recommended | Change Needed? |
|---|---|---|---|
| **Daily Trading Summary** | Event-driven | Event-driven | ✅ No change |
| **Hedge Evaluation** | Event-driven | Event-driven | ✅ No change |
| **Market Data Update** | Event-driven | Event-driven | ✅ No change |
| **Schedule Events** | Event-driven | Event-driven | ✅ No change |
| **WorkflowFailed** | Event-driven | Event-driven | ⚠️ Route to different SNS topic |
| **Lambda Errors** | EventBridge | CloudWatch → SNS | ⚠️ Remove EventBridge, use AlarmActions |
| **DLQ Messages** | EventBridge | CloudWatch → SNS | ⚠️ Remove EventBridge, use AlarmActions |
| **Stuck Runs** | EventBridge | CloudWatch → SNS | ⚠️ Remove EventBridge, use AlarmActions |

---

## What Needs to Change?

### Minimal Changes Required

1. **Create two SNS topics** (5 minutes)
   - `ErrorNotificationsTopic` - for on-call engineers
   - `ReportNotificationsTopic` - for stakeholders

2. **Update CloudWatch Alarms** (10 minutes)
   - Add `AlarmActions: [!Ref ErrorNotificationsTopic]` to each alarm
   - Remove `CloudWatchAlarmEvent` from NotificationsFunction

3. **Update NotificationsFunction** (15 minutes)
   - Add logic to route WorkflowFailed → ErrorNotificationsTopic
   - Route other events → ReportNotificationsTopic
   - Update IAM policies for SNS publish

4. **Update subscribers** (10 minutes)
   - Subscribe on-call team to ErrorNotificationsTopic
   - Subscribe stakeholders to ReportNotificationsTopic

**Total effort: ~40 minutes + testing**

---

## What Stays the Same?

✅ Daily reports remain event-driven (correct approach)  
✅ NotificationsFunction still formats and enriches notifications  
✅ SES still used for rich HTML emails  
✅ EventBridge still routes business events  
✅ All existing event flows continue to work  
✅ No breaking changes to business logic Lambdas

---

## Benefits of Recommended Changes

### Reliability
- Infrastructure errors delivered even if NotificationsFunction is broken
- Faster error delivery (no Lambda cold start delay)
- No circular dependency (NotificationsErrorsAlarm won't trigger NotificationsFunction)

### Separation of Concerns
- On-call engineers get errors only (not daily reports)
- Stakeholders get reports only (not error spam)
- Different SNS topics enable different alerting policies

### Maintainability
- Infrastructure monitoring independent of application logic
- Easier to add new notification types (clear decision tree)
- Aligns with AWS best practices

---

## When to Use Each Pattern

### Pattern 1: CloudWatch Alarm → SNS
**Use for:**
- Infrastructure failures
- Lambda errors/timeouts
- System health metrics
- Anything that needs immediate attention from on-call

**Example:**
```yaml
DLQMessageAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmActions:
      - !Ref ErrorNotificationsTopic  # Direct SNS delivery
```

### Pattern 2: EventBridge → NotificationsFunction → SNS
**Use for:**
- Application errors with context
- Daily operational reports
- Business logic events
- Anything that needs formatting/enrichment

**Example:**
```python
# Event published by business logic
publish_to_eventbridge(WorkflowFailedEvent(
    error="Strategy timeout",
    strategy="1-KMLM.clj",
    context={"symbol": "AAPL", ...}
))

# NotificationsFunction enriches and routes to ErrorNotificationsTopic
```

### Pattern 3: EventBridge Schedule → Lambda
**Use for:**
- Periodic batch jobs
- Fixed-time aggregations
- **NOT for Alchemiser daily reports** (events are better)

---

## Cost Impact

**Current monthly cost:** ~$0.02  
**New monthly cost:** ~$0.01  
**Savings:** ~$0.01/month (negligible)

**Takeaway:** Cost is not a factor in this decision

---

## Risk Assessment

### Migration Risk: LOW

✅ Additive changes only (no breaking changes)  
✅ Can test in dev/staging before production  
✅ Can rollback in < 5 minutes if issues arise  
✅ Old flows continue to work during migration  
✅ No changes to business logic Lambdas

### Operational Risk: LOW → REDUCED

Current risks:
- ❌ Single point of failure (NotificationsFunction)
- ❌ Circular dependency (NotificationsErrorsAlarm)
- ❌ Slow error delivery (Lambda cold start)

After migration:
- ✅ Infrastructure errors independent of application
- ✅ No circular dependency
- ✅ Faster error delivery

---

## Implementation Timeline

**Total estimated time: 4-6 hours**

```
Phase 1: Create SNS topics (30 min)
Phase 2: Update CloudWatch Alarms (1 hour)
Phase 3: Update NotificationsFunction (2 hours)
Phase 4: Testing in dev/staging (1-2 hours)
Phase 5: Production rollout (30 min)
```

Can be done incrementally with no downtime.

---

## Next Steps

1. **Review this analysis** with team
2. **Approve recommendations** if alignment reached
3. **Execute Phase 1** (create SNS topics in dev)
4. **Test and iterate** before production rollout

---

## Questions & Answers

### Q: "Will this affect our daily report emails?"
**A:** No breaking changes. Reports continue to be sent via events, just routed to a different SNS topic for better audience targeting.

### Q: "What if NotificationsFunction fails after migration?"
**A:** Infrastructure errors (DLQ, timeouts, stuck runs) will still be delivered via CloudWatch → SNS. Only application errors (WorkflowFailed) depend on NotificationsFunction, and those are less critical.

### Q: "Can we roll back if something goes wrong?"
**A:** Yes, in < 5 minutes. Just remove `AlarmActions` from CloudWatch Alarms and redeploy. Old flows continue to work during migration.

### Q: "Do we need to change any business logic?"
**A:** No. Business logic Lambdas don't need to change. Only infrastructure configuration (template.yaml) and NotificationsFunction routing logic.

### Q: "Is this a lot of work?"
**A:** No. Estimated 4-6 hours including testing. Changes are minimal and localized to notification layer.

---

## Further Reading

- [Full Analysis Document](./NOTIFICATION_ARCHITECTURE_ANALYSIS.md) - 460 lines, comprehensive details
- [Architecture Diagrams](./NOTIFICATION_ARCHITECTURE_DIAGRAMS.md) - Mermaid diagrams, testing checklists, cost analysis
- [AWS Best Practice Alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Best-Practice-Alarms.html)
- [Event-Driven Architecture Best Practices](https://www.tinybird.co/blog/event-driven-architecture-best-practices-for-databases-and-files)

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-12  
**Author:** GitHub Copilot (Quick Reference)  
**Status:** Draft - Pending Review
