# EventBridge Migration - Recommended Action Plan

**Date:** 2025-10-16  
**Decision:** CONTINUE with current branch (feat/eventbridge)  
**Rationale:** Architecture is sound, 75% complete, restarting would waste 50+ hours of work  
**Estimated Completion:** 4 weeks (16-27 hours of work)  

---

## Executive Summary

**RECOMMENDATION: CONTINUE AND COMPLETE** the EventBridge migration using a phased approach.

**Key Points:**
- ✅ Architecture is solid (8.5/10 quality score)
- ✅ Infrastructure complete and well-documented
- ✅ Multiple bugs already fixed iteratively
- ⚠️ Needs production validation and logging improvements
- ⚠️ Missing operational runbook

**Effort Analysis:**
- **Continue:** 16-27 hours to complete
- **Restart:** 64-101 hours to rebuild
- **Savings:** ~50-75 hours

---

## 4-Phase Completion Plan

### Phase 1: Validation (Week 1) - 6-8 hours

**Goal:** Deploy to AWS and validate with real services

**Tasks:**
1. **Deploy to AWS Dev** (1 hour)
   ```bash
   ./scripts/deploy.sh dev
   ```

2. **Trigger Test Workflow** (30 min)
   - Manual trigger or wait for scheduler
   - Monitor CloudWatch logs in real-time

3. **Collect CloudWatch Logs** (1 hour)
   ```bash
   aws logs tail /aws/lambda/the-alchemiser-v2-lambda-dev --follow
   aws logs filter-log-events --log-group-name /aws/lambda/the-alchemiser-v2-lambda-dev \
     --start-time $(date -u -d '1 hour ago' +%s)000 > logs_sample.json
   ```

4. **Analyze Logging Issues** (2-3 hours)
   - Identify verbose modules
   - Test correlation ID queries
   - Measure log volume
   - Document specific problems with examples

5. **Check Metrics** (1 hour)
   - Lambda duration and cold starts
   - EventBridge success/failure rates
   - DLQ message count
   - Idempotency duplicate rate

6. **Document Findings** (1-2 hours)
   - Create analysis document with actual data
   - Include log samples showing issues
   - List specific modules needing adjustment

**Deliverable:** `EVENTBRIDGE_PRODUCTION_VALIDATION_REPORT.md` with real AWS data

---

### Phase 2: Logging Improvements (Week 2) - 4-8 hours

**Goal:** Fix identified logging and observability issues

**Tasks:**
1. **Reduce Verbosity** (2-3 hours)
   - Change log levels from DEBUG to INFO for production modules
   - Remove unnecessary log statements in hot paths
   - Focus on modules identified in Phase 1

2. **Improve Correlation Tracing** (1-2 hours)
   - Ensure ALL log statements include correlation_id
   - Create CloudWatch Insights saved queries
   - Test queries across log streams

3. **Create CloudWatch Dashboard** (1-2 hours)
   ```yaml
   # Add to template.yaml
   TradingDashboard:
     Type: AWS::CloudWatch::Dashboard
     Properties:
       DashboardName: !Sub 'alchemiser-trading-${Stage}'
       DashboardBody: # ... metrics and log widgets
   ```

4. **Test Dashboard** (30 min)
   - Deploy dashboard to AWS
   - Verify metrics display correctly
   - Save CloudWatch Insights queries

**Deliverable:** Improved logging with working CloudWatch dashboard

---

### Phase 3: Operational Readiness (Week 3) - 4-6 hours

**Goal:** Ensure production-ready with operational documentation

**Tasks:**
1. **Create Operational Runbook** (2-3 hours)
   - Common failure scenarios and solutions
   - DLQ replay procedures (step-by-step)
   - Alarm response procedures
   - Escalation paths

2. **Configure Notifications** (1 hour)
   - Create SNS topic for alarms
   - Configure email/Slack notifications
   - Test alarm notifications

3. **Validate Idempotency** (1 hour)
   - Manually replay events from EventBridge archive
   - Verify duplicate detection works
   - Test DLQ replay procedures

4. **Document Rollback** (30 min)
   - Step-by-step rollback procedures
   - Test rollback in dev environment

**Deliverable:** `EVENTBRIDGE_OPERATIONAL_RUNBOOK.md` with incident response procedures

---

### Phase 4: Production Deployment (Week 4) - 2-5 hours

**Goal:** Deploy to production with monitoring

**Tasks:**
1. **Pre-deployment Review** (30 min)
   - Verify all Phase 1-3 tasks complete
   - Review documentation
   - Confirm rollback plan ready

2. **Deploy to Production** (1 hour)
   ```bash
   ./scripts/deploy.sh prod
   ```

3. **Monitor First 24 Hours** (2-3 hours over 24 hours)
   - Watch CloudWatch dashboard
   - Check DLQ for failed events
   - Verify email notifications
   - Monitor AWS costs

4. **Post-deployment Validation** (1 hour)
   - Verify 5+ successful workflows
   - Check log volume and costs
   - Confirm no alarms triggered
   - Validate trading accuracy

5. **Complete Documentation** (30 min)
   - Update lessons learned
   - Close out migration tasks
   - Celebrate success! 🎉

**Deliverable:** Production system running successfully with complete documentation

---

## Success Criteria

### Phase 1 Success
- [ ] Deployed to AWS dev environment
- [ ] Real CloudWatch logs collected
- [ ] Specific logging issues documented with examples
- [ ] Metrics collected and analyzed

### Phase 2 Success
- [ ] Verbose logging reduced in identified modules
- [ ] CloudWatch dashboard deployed and working
- [ ] Correlation ID queries working across log streams
- [ ] Log costs acceptable

### Phase 3 Success
- [ ] Operational runbook complete and reviewed
- [ ] SNS notifications configured and tested
- [ ] Idempotency validated with replay test
- [ ] Rollback procedures documented and tested

### Phase 4 Success
- [ ] Deployed to production successfully
- [ ] 5+ workflows completed successfully
- [ ] No DLQ messages accumulating
- [ ] All alarms healthy
- [ ] Documentation complete

---

## Risk Mitigation

### High-Priority Risks

**Risk: Production deployment fails**
- **Mitigation:** Test in dev/staging first
- **Rollback:** Use documented rollback procedure
- **Contact:** Keep AWS support contact ready

**Risk: DLQ accumulates messages**
- **Mitigation:** Monitor alarms, respond quickly
- **Procedure:** Use runbook DLQ replay steps
- **Escalation:** Document in runbook

**Risk: Log costs exceed budget**
- **Mitigation:** Monitor costs daily during Phase 1-2
- **Action:** Adjust log retention if needed
- **Target:** Keep under $10/month

### Medium-Priority Risks

**Risk: Lambda timeouts**
- **Mitigation:** 600s timeout should be sufficient
- **Monitoring:** Track duration metrics
- **Action:** Investigate if >60s average

**Risk: Payload size exceeds limit**
- **Mitigation:** 200KB validation already in place
- **Future:** Implement S3 fallback if needed
- **Monitoring:** Track payload sizes in logs

---

## Alternative: Staged Migration (If Needed)

If full migration seems too risky, consider staged approach:

### Stage 1: Hybrid Mode (Week 1-2)
- Enable both in-memory and EventBridge buses
- Publish to both, process from in-memory
- Validate EventBridge events without relying on them
- **Rollback:** Disable EventBridge publishing

### Stage 2: Single Event Type (Week 3)
- Migrate only SignalGenerated events to EventBridge
- Keep other events in-memory
- Validate end-to-end for one event type
- **Rollback:** Feature flag to in-memory

### Stage 3: Full Migration (Week 4)
- Migrate remaining event types
- Remove in-memory bus
- Complete testing and documentation
- **Rollback:** Restore in-memory bus

**Note:** This adds complexity but reduces risk. Only recommended if Phase 1 reveals significant issues.

---

## Quick Decision Matrix

| Scenario | Recommendation |
|----------|---------------|
| Phase 1 shows minor logging issues | **Continue to Phase 2** - Fix logging |
| Phase 1 shows major architectural problems | **Consider staged migration** - Hybrid mode first |
| Phase 1 completely successful | **Skip to Phase 3** - Focus on operations |
| Phase 2 logging fixes don't improve situation | **Revisit logging strategy** - May need structured logging library |
| Phase 3 operational testing reveals gaps | **Delay Phase 4** - Complete runbook fully |
| Phase 4 production deployment fails | **Execute rollback** - Use documented procedure |

---

## Communication Plan

### Weekly Status Updates
- **Monday:** Week goals and tasks
- **Friday:** Week completion status and blockers
- **Ad-hoc:** Any critical issues discovered

### Stakeholder Communication
- **Development Team:** Daily stand-ups during active work
- **Operations Team:** Training sessions before Phase 4
- **Management:** Weekly summary of progress

### Documentation Updates
- Update README.md with deployment status
- Keep CHANGELOG.md current
- Update issue tracker with progress

---

## Resource Requirements

### Personnel
- **Developer:** 1 person, 16-27 hours over 4 weeks
- **Operations:** 2-4 hours for training and validation
- **Reviewer:** 2-3 hours for documentation review

### AWS Resources
- **Dev Environment:** Already configured
- **CloudWatch:** Included in AWS free tier + minimal costs
- **Lambda:** Estimated $8-10/month
- **EventBridge:** ~$0.30/month
- **Total:** ~$10-15/month

### Tools
- AWS CLI configured
- SAM CLI installed
- Docker for SAM builds
- Access to CloudWatch console

---

## Next Immediate Steps

1. **TODAY:** Review and approve this action plan
2. **THIS WEEK:** Execute Phase 1 (deploy to AWS dev)
3. **NEXT WEEK:** Execute Phase 2 (fix logging)
4. **WEEK 3:** Execute Phase 3 (operational readiness)
5. **WEEK 4:** Execute Phase 4 (production deployment)

---

## Conclusion

**The path forward is clear:**
1. ✅ Current implementation is solid
2. ✅ Completing is faster than restarting (saves 50+ hours)
3. ✅ Phased approach minimizes risk
4. ✅ Success criteria well-defined

**RECOMMENDATION: Begin Phase 1 immediately**

Deploy to AWS dev this week and collect real data. All decisions about next steps should be based on actual production validation, not theoretical concerns.

---

**Document Version:** 1.0  
**Status:** Ready for Review  
**Next Update:** After Phase 1 completion
