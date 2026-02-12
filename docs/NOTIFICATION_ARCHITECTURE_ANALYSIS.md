# Notification Architecture Analysis & Recommendations

## Executive Summary

This document analyzes the current notification architecture of the Alchemiser trading system and provides recommendations for decoupling error notifications from daily operational reports based on AWS best practices.

**Key Findings:**
- Current architecture uses a **unified event-driven approach** where all notifications (errors, daily reports, system events) are triggered by EventBridge events
- This creates **tight coupling** between operational workflows and notification delivery
- AWS best practices recommend **separating error notifications from daily reports** using different delivery patterns

**Primary Recommendations:**
1. **Keep daily operational reports event-driven** (current approach is correct)
2. **Decouple critical error notifications** to use CloudWatch Alarms → SNS for immediate, reliable delivery
3. **Maintain application-level errors** in the event-driven flow for contextual information
4. **Create separate notification channels** with different SNS topics for errors vs reports

---

## Current Architecture Analysis

### Notification Types & Sources

The system currently sends **6 types of notifications**, all routed through EventBridge → NotificationsFunction → SES:

| Notification Type | Category | Trigger Event | Data Source |
|---|---|---|---|
| **Trading Success Summary** | Daily Report | `AllTradesCompleted` | Pre-aggregated in event payload + DynamoDB queries |
| **Trading Workflow Failure** | Application Error | `WorkflowFailed` | Error context in event payload |
| **Hedge Evaluation** | Daily Report | `HedgeEvaluationCompleted` | Pre-aggregated in event payload |
| **Market Data Update** | Daily Report | `DataLakeUpdateCompleted` | Data freshness metrics in event |
| **Schedule Events** | Daily Report | `ScheduleCreated` | Schedule details in event |
| **Infrastructure Failures** | System Error | CloudWatch Alarms / Lambda Destinations | Alarm state change events |

### Current Event Flow

```
Business Logic → EventBridge → NotificationsFunction → SES → Email
       ↓
   CloudWatch Alarms → Default EventBridge Bus → NotificationsFunction → SES → Email
```

### Strengths of Current Architecture

✅ **Unified observability** - All notifications flow through a single Lambda, simplifying monitoring  
✅ **Rich context** - Business events carry domain-specific data (trade summaries, P&L, strategy performance)  
✅ **Pre-aggregated data** - Daily reports don't require additional database queries (efficient)  
✅ **Deduplication** - TradeAggregator uses DynamoDB lock to prevent duplicate notifications  
✅ **Environment safety** - `ALLOW_REAL_EMAILS` flag prevents accidental production emails in dev/staging

### Weaknesses & Risks

❌ **Single point of failure** - If NotificationsFunction fails, ALL notifications (errors + reports) are lost  
❌ **Error notification delay** - Critical infrastructure failures depend on Lambda cold start & execution  
❌ **Tight coupling** - Workflow failures require successful EventBridge publish before notification  
❌ **Lambda error feedback loop** - NotificationsErrorsAlarm triggers NotificationsFunction itself (circular dependency risk)  
❌ **No separation of concerns** - Urgent errors and routine reports share the same delivery channel

---

## AWS Best Practices Research

### Key Findings from AWS Documentation

#### 1. Error Notifications Should Be Immediate & Decoupled

**AWS Recommendation:**  
Use **CloudWatch Alarms → SNS** for critical infrastructure errors that require immediate attention.

**Rationale:**
- Lower latency (no Lambda cold start)
- Higher reliability (no custom code execution required)
- Independent of application state (works even if application is completely broken)
- Avoids circular dependencies (alarms don't depend on the system they monitor)

**Sources:**
- [AWS Best Practice Alarms](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Best-Practice-Alarms.html)
- [CloudWatch Lambda Error Notifications](https://www.antstack.com/blog/how-to-get-instant-email-notifications-for-aws-lambda-errors-with-cloudwatch-alarms/)

#### 2. Daily Reports Should Use Scheduled OR Event-Driven Patterns

**AWS Recommendation:**  
For **daily summary reports**, choose based on data characteristics:

| Pattern | Best For | Alchemiser Use Case |
|---|---|---|
| **Scheduled Lambda** | Periodic batch aggregations, fixed time snapshots | ❌ Not ideal - requires querying DynamoDB |
| **Event-driven Lambda** | Real-time aggregations, pre-computed summaries | ✅ Current approach is optimal |
| **Hybrid** | Events update aggregates, scheduled job sends report | ⚠️ Possible optimization |

**Rationale for Alchemiser:**  
The current event-driven approach is **correct** because:
- Trade execution events already contain **pre-aggregated data** (P&L, portfolio snapshot, strategy performance)
- No additional database queries needed (efficient)
- Reports are sent immediately after workflow completion (timely)
- Natural trigger point aligns with business logic completion

**Sources:**
- [AWS EventBridge Scheduled Lambda Tutorial](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-run-lambda-schedule.html)
- [Event-Driven Architecture Best Practices](https://www.tinybird.co/blog/event-driven-architecture-best-practices-for-databases-and-files)

#### 3. Separate SNS Topics for Different Audiences

**AWS Recommendation:**  
Use **different SNS topics** for errors vs reports to:
- Enable different subscriber lists (on-call engineers vs stakeholders)
- Apply different retention and alerting policies
- Reduce notification fatigue
- Allow independent scaling and monitoring

**Sources:**
- [CloudWatch Alarms Best Practices](https://moldstud.com/articles/p-what-are-the-best-practices-for-setting-up-cloudwatch-alarms-and-notifications-in-aws)

---

## Recommended Architecture

### High-Level Design

Separate notifications into **two independent delivery paths**:

```
┌─────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE ERRORS                     │
│                    (Immediate, Critical)                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
CloudWatch Alarms ──────► SNS Topic (Errors) ──────► Email (On-Call Team)
                            │
                            └──► PagerDuty / OpsGenie (Optional)


┌─────────────────────────────────────────────────────────────┐
│              APPLICATION EVENTS & DAILY REPORTS              │
│               (Contextual, Informational)                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
Business Events ──────► EventBridge ──────► NotificationsFunction
                                                   │
                                                   ▼
                                        SNS Topic (Reports) ──────► Email (Stakeholders)
```

### Detailed Recommendations

#### Recommendation 1: Create Separate SNS Topics

**Action:**  
Create two SNS topics with different purposes and subscribers:

```yaml
# template.yaml additions
ErrorNotificationsTopic:
  Type: AWS::SNS::Topic
  Properties:
    TopicName: !Sub "alchemiser-${Stage}-error-notifications"
    DisplayName: "Alchemiser Critical Error Notifications"

ReportNotificationsTopic:
  Type: AWS::SNS::Topic
  Properties:
    TopicName: !Sub "alchemiser-${Stage}-report-notifications"
    DisplayName: "Alchemiser Daily Reports & Updates"
```

**Subscribers:**
- **ErrorNotificationsTopic**: On-call engineers, incident response team
- **ReportNotificationsTopic**: Stakeholders, portfolio managers, operations team

#### Recommendation 2: Route CloudWatch Alarms Directly to SNS

**Action:**  
Remove CloudWatch Alarms from EventBridge routing and connect directly to SNS:

```yaml
# For each CloudWatch Alarm (e.g., DLQMessageAlarm)
DLQMessageAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    # ... existing properties ...
    AlarmActions:
      - !Ref ErrorNotificationsTopic  # Direct SNS delivery
    TreatMissingData: notBreaching
```

**Benefits:**
- Faster delivery (no Lambda execution delay)
- Higher reliability (no custom code)
- Independent of application state
- Breaks circular dependency (NotificationsErrorsAlarm won't trigger NotificationsFunction)

**Alarms to Route to SNS:**
- ✅ `DLQMessageAlarm` - Messages in execution DLQ
- ✅ `FifoDLQMessageAlarm` - Messages in parallel execution DLQ
- ✅ `StuckRunsAlarm` - Execution runs stuck > 30 minutes
- ✅ `StuckAggregationSessionsAlarm` - Aggregation sessions stuck > 30 minutes
- ✅ `StrategyOrchestratorErrorsAlarm` - Orchestrator Lambda errors
- ✅ `StrategyWorkerErrorsAlarm` - Strategy Worker Lambda errors
- ✅ `StrategyAggregatorErrorsAlarm` - Aggregator Lambda errors
- ✅ `RebalancePlannerErrorsAlarm` - Rebalance Planner Lambda errors
- ✅ `NotificationsErrorsAlarm` - Notifications Lambda errors (CRITICAL)

#### Recommendation 3: Keep Application Events Event-Driven

**Action:**  
Maintain current event-driven flow for business logic notifications:

**Route to NotificationsFunction → ReportNotificationsTopic:**
- ✅ `AllTradesCompleted` - Daily trading summary with P&L, strategy performance
- ✅ `HedgeEvaluationCompleted` - Hedge evaluation results
- ✅ `DataLakeUpdateCompleted` - Market data refresh confirmation
- ✅ `ScheduleCreated` - Schedule changes, early closes, holidays

**Route to NotificationsFunction → ErrorNotificationsTopic:**
- ✅ `WorkflowFailed` - Application-level errors with rich context
- ✅ `LambdaAsyncFailureEvent` - Lambda async invocation failures

**Rationale:**
- These events contain **pre-aggregated business data** that enriches notifications
- Application errors benefit from **domain context** (which strategy failed, which symbol, etc.)
- NotificationsFunction adds value by formatting, enriching, and attaching reports

#### Recommendation 4: Update NotificationsFunction for Dual-Topic Routing

**Action:**  
Modify NotificationsFunction to publish to different SNS topics based on event type:

```python
# functions/notifications/service.py

def determine_notification_topic(event_type: str) -> str:
    """Route notification to appropriate SNS topic."""
    error_events = {
        "WorkflowFailed",
        "Lambda Function Invocation Result - Failure",
    }
    
    if event_type in error_events:
        return os.environ["ERROR_NOTIFICATIONS_TOPIC_ARN"]
    else:
        return os.environ["REPORT_NOTIFICATIONS_TOPIC_ARN"]
```

**Benefits:**
- Maintains current rich notification formatting
- Enables different subscriber lists per topic
- Preserves application context in error notifications
- Keeps successful reports separate from error alerts

#### Recommendation 5: Add CloudWatch Log Metric Filters (Optional Enhancement)

**Action:**  
Create metric filters for application-level errors logged to CloudWatch Logs:

```yaml
WorkflowFailedMetricFilter:
  Type: AWS::Logs::MetricFilter
  Properties:
    LogGroupName: !Sub "/aws/lambda/alchemiser-${Stage}-strategy"
    FilterPattern: '[timestamp, request_id, level=ERROR*, ...]'
    MetricTransformations:
      - MetricName: ApplicationErrors
        MetricNamespace: Alchemiser/Application
        MetricValue: "1"

ApplicationErrorsAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub "alchemiser-${Stage}-application-errors"
    MetricName: ApplicationErrors
    Namespace: Alchemiser/Application
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 1
    ComparisonOperator: GreaterThanOrEqualToThreshold
    AlarmActions:
      - !Ref ErrorNotificationsTopic
```

**Benefits:**
- Catches errors that occur **before** WorkflowFailed event can be published
- Provides an independent monitoring layer
- Aligns with AWS best practice of separating observability from application logic

---

## Implementation Considerations

### Pros & Cons of Recommended Changes

#### Advantages

✅ **Separation of concerns** - Errors and reports have independent delivery paths  
✅ **Higher reliability** - Infrastructure errors don't depend on Lambda execution  
✅ **Faster error delivery** - CloudWatch → SNS is lower latency than CloudWatch → EventBridge → Lambda → SNS  
✅ **Independent scaling** - Different SNS topics can have different subscriber lists, retention policies  
✅ **Breaks circular dependency** - NotificationsErrorsAlarm won't trigger NotificationsFunction  
✅ **Better audience targeting** - On-call engineers get errors only, stakeholders get reports only  
✅ **Maintains context** - Application errors still get rich domain context through NotificationsFunction

#### Disadvantages

⚠️ **Slightly more complex** - Two SNS topics to manage instead of unified SES delivery  
⚠️ **SNS email formatting** - Direct SNS emails are plain text, less rich than SES HTML emails  
⚠️ **Migration effort** - Requires updating subscribers to new SNS topics  
⚠️ **Testing overhead** - Need to test both SNS topics in dev/staging

### Migration Complexity: LOW-MEDIUM

**Estimated Effort:** 4-6 hours  
**Risk:** Low (additive changes, no breaking changes)

**Steps:**
1. Create two SNS topics in `template.yaml`
2. Update CloudWatch Alarms to use `AlarmActions` with ErrorNotificationsTopic
3. Remove CloudWatch Alarm EventBridge rules from NotificationsFunction
4. Add topic ARN environment variables to NotificationsFunction
5. Update NotificationsFunction to route to appropriate SNS topic
6. Update IAM policies to allow SNS publish to both topics
7. Subscribe test email addresses to both topics in dev
8. Test each notification type end-to-end
9. Update production subscribers after validation

### Backward Compatibility

✅ **No breaking changes**  
- Current SES delivery continues to work
- New SNS topics are additive
- EventBridge routing remains functional during migration
- Can roll back by removing AlarmActions from alarms

---

## Alternative Approaches Considered

### Alternative 1: Scheduled Daily Report Lambda

**Approach:**  
Replace event-driven reports with a scheduled Lambda that queries DynamoDB at 5 PM ET daily.

**Verdict:** ❌ **Not Recommended**

**Rationale:**
- Current event-driven approach is **more efficient** (pre-aggregated data in events)
- No benefit to polling DynamoDB when data is already available in events
- Adds unnecessary database load
- Loses natural trigger point (workflow completion)
- Increases latency (reports sent hours after trades complete)

### Alternative 2: Fully Event-Driven (Current Architecture)

**Approach:**  
Keep everything event-driven through NotificationsFunction.

**Verdict:** ⚠️ **Acceptable but Not Optimal**

**Rationale:**
- Simple to maintain
- Unified observability
- Works well for application-level notifications
- **But:** Creates single point of failure for critical infrastructure errors
- **But:** Slower, less reliable for urgent error alerts

### Alternative 3: Direct SES from Each Lambda

**Approach:**  
Remove NotificationsFunction entirely, have each Lambda send emails via SES directly.

**Verdict:** ❌ **Not Recommended**

**Rationale:**
- Duplicates email formatting logic across Lambdas
- Harder to maintain consistent email templates
- No centralized notification observability
- Increases complexity of business logic Lambdas

---

## Decision Matrix

| Criterion | Current (All Events) | Recommended (Hybrid) | Alternative 1 (Scheduled) |
|---|---|---|---|
| **Error Notification Speed** | Medium (Lambda delay) | Fast (Direct SNS) | N/A |
| **Error Reliability** | Medium (Lambda SPOF) | High (Independent) | N/A |
| **Report Timeliness** | High (Immediate) | High (Immediate) | Low (Scheduled delay) |
| **Report Efficiency** | High (Pre-aggregated) | High (Pre-aggregated) | Low (Query DynamoDB) |
| **Separation of Concerns** | Low | High | Medium |
| **Complexity** | Low | Medium | Medium |
| **AWS Best Practice Alignment** | Medium | High | Low |
| **Maintenance Effort** | Low | Medium | Medium |

**Recommendation:** **Hybrid approach (Recommendation 2 in this document)**

---

## Implementation Plan (If Approved)

### Phase 1: Add SNS Topics (Non-Breaking)
- [ ] Create `ErrorNotificationsTopic` in `template.yaml`
- [ ] Create `ReportNotificationsTopic` in `template.yaml`
- [ ] Deploy to dev environment
- [ ] Subscribe test email addresses to both topics
- [ ] Verify topic creation and subscription

### Phase 2: Update CloudWatch Alarms (Additive)
- [ ] Add `AlarmActions` to all CloudWatch Alarms pointing to `ErrorNotificationsTopic`
- [ ] Deploy to dev environment
- [ ] Test alarm triggers (e.g., manually put message in DLQ)
- [ ] Verify SNS email delivery

### Phase 3: Update NotificationsFunction (Dual-Channel)
- [ ] Add `ERROR_NOTIFICATIONS_TOPIC_ARN` environment variable
- [ ] Add `REPORT_NOTIFICATIONS_TOPIC_ARN` environment variable
- [ ] Update IAM role to allow `sns:Publish` to both topics
- [ ] Modify notification service to route to appropriate topic
- [ ] Deploy to dev environment
- [ ] Test both error and report events end-to-end

### Phase 4: Remove CloudWatch Alarm EventBridge Rules (Cleanup)
- [ ] Remove `CloudWatchAlarmEvent` rule from NotificationsFunction Events
- [ ] Deploy to dev environment
- [ ] Verify CloudWatch alarms still deliver via SNS
- [ ] Confirm NotificationsFunction no longer receives alarm events

### Phase 5: Production Rollout
- [ ] Update staging subscribers
- [ ] Deploy to staging
- [ ] Run full end-to-end test in staging
- [ ] Update production subscribers
- [ ] Deploy to production
- [ ] Monitor for 1 week
- [ ] Deprecate old SNS topics (if any)

---

## Conclusion

The current notification architecture is **mostly correct** for daily operational reports (event-driven is optimal), but should be **enhanced** to separate critical infrastructure errors for higher reliability and faster delivery.

**Key Takeaways:**
1. ✅ **Keep daily reports event-driven** (current approach is correct)
2. ⚠️ **Decouple infrastructure errors** to use CloudWatch Alarms → SNS directly
3. ✅ **Maintain application errors** in event flow for rich context
4. ✅ **Use separate SNS topics** for different audiences and priorities

**Next Steps:**
1. Review recommendations with stakeholders
2. Approve implementation plan
3. Execute phased rollout starting with dev environment
4. Monitor and iterate based on operational feedback

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-12  
**Author:** GitHub Copilot (Architectural Analysis)  
**Status:** Draft - Pending Review
