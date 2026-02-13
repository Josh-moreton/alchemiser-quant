"""Business Unit: scripts | Status: current."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import boto3

print("=== Checking CloudTrail for EarlyValidation hook failures ===\n")
ct = boto3.client("cloudtrail", region_name="us-east-1")

# Look for CreateChangeSet events in the last 6 hours
events_resp = ct.lookup_events(
    LookupAttributes=[
        {"AttributeKey": "EventName", "AttributeValue": "CreateChangeSet"},
    ],
    StartTime=datetime.now(timezone.utc) - timedelta(hours=6),
    MaxResults=10,
)

for ev in events_resp.get("Events", []):
    detail = json.loads(ev.get("CloudTrailEvent", "{}"))
    req = detail.get("requestParameters", {})
    stack = req.get("stackName", "")
    if "alchemiser-prod" not in stack:
        continue
    print(f"Time: {ev.get('EventTime')}")
    print(f"Stack: {stack}")
    error_code = detail.get("errorCode", "")
    error_msg = detail.get("errorMessage", "")
    if error_code:
        print(f"Error: {error_code} - {error_msg}")
    resp_elem = detail.get("responseElements")
    if resp_elem:
        print(f"Response: {json.dumps(resp_elem, indent=2, default=str)[:1000]}")
    print()

print("\n=== Checking for DescribeChangeSetHooks events ===\n")
try:
    events2 = ct.lookup_events(
        LookupAttributes=[
            {"AttributeKey": "EventName", "AttributeValue": "DescribeChangeSetHooks"},
        ],
        StartTime=datetime.now(timezone.utc) - timedelta(hours=6),
        MaxResults=5,
    )
    for ev in events2.get("Events", []):
        print(json.dumps(json.loads(ev.get("CloudTrailEvent", "{}")), indent=2, default=str)[:2000])
except Exception:
    pass

print("\n=== Trying describe_change_set_hooks on any existing changeset ===\n")
cfn = boto3.client("cloudformation", region_name="us-east-1")
try:
    stacks = cfn.list_stacks(StackStatusFilter=["REVIEW_IN_PROGRESS"])
    prod = [s for s in stacks["StackSummaries"] if s["StackName"] == "alchemiser-prod"]
    if prod:
        cs_list = cfn.list_change_sets(StackName="alchemiser-prod")
        for cs in cs_list["Summaries"]:
            print(f"Changeset: {cs['ChangeSetName']} | Status: {cs['Status']}")
            print(f"  Reason: {cs.get('StatusReason', 'N/A')}")
            try:
                hooks = cfn.describe_change_set_hooks(
                    StackName="alchemiser-prod", ChangeSetName=cs["ChangeSetName"]
                )
                print(f"  Hooks: {json.dumps(hooks.get('Hooks', []), indent=4, default=str)[:3000]}")
            except Exception as ex:
                print(f"  Hooks API error: {ex}")
    else:
        print("No REVIEW_IN_PROGRESS stack found")
except Exception as ex:
    print(f"Error: {ex}")

print("\n=== Broad resource scan for alchemiser-prod naming conflicts ===\n")

# Check EVERY resource type that could match based on the template
# Focus on resources the hook might check that we missed

# EventBridge Scheduler schedule groups
try:
    scheduler = boto3.client("scheduler", region_name="us-east-1")
    groups = scheduler.list_schedule_groups()
    for g in groups.get("ScheduleGroups", []):
        if "alchemiser-prod" in g.get("Name", ""):
            print(f"FOUND Schedule Group: {g['Name']}")
except Exception as ex:
    print(f"Schedule groups check: {ex}")

# Lambda event source mappings 
try:
    lam = boto3.client("lambda", region_name="us-east-1")
    mappings = lam.list_event_source_mappings()
    for m in mappings.get("EventSourceMappings", []):
        fn = m.get("FunctionArn", "")
        if "alchemiser-prod" in fn:
            print(f"FOUND Event Source Mapping: {m['UUID']} -> {fn}")
except Exception as ex:
    print(f"Event source mappings check: {ex}")

# CloudWatch Log Groups (check again)
try:
    logs = boto3.client("logs", region_name="us-east-1")
    paginator = logs.get_paginator("describe_log_groups")
    for page in paginator.paginate(logGroupNamePrefix="/aws/lambda/alchemiser-prod"):
        for lg in page.get("logGroups", []):
            print(f"FOUND Log Group: {lg['logGroupName']}")
except Exception as ex:
    print(f"Log groups check: {ex}")

# EventBridge rules on all buses
try:
    eb = boto3.client("events", region_name="us-east-1")
    # Check default bus
    rules = eb.list_rules(NamePrefix="alchemiser-prod")
    for r in rules.get("Rules", []):
        print(f"FOUND EB Rule (default bus): {r['Name']}")
    # Check any alchemiser buses
    buses = eb.list_event_buses(NamePrefix="alchemiser-prod")
    for b in buses.get("EventBuses", []):
        print(f"FOUND EB Bus: {b['Name']}")
        rules2 = eb.list_rules(EventBusName=b["Name"])
        for r in rules2.get("Rules", []):
            print(f"  FOUND Rule on {b['Name']}: {r['Name']}")
except Exception as ex:
    print(f"EventBridge check: {ex}")

# IAM Roles
try:
    iam = boto3.client("iam", region_name="us-east-1")
    paginator = iam.get_paginator("list_roles")
    for page in paginator.paginate():
        for role in page["Roles"]:
            if "alchemiser-prod" in role["RoleName"].lower():
                print(f"FOUND IAM Role: {role['RoleName']}")
except Exception as ex:
    print(f"IAM check: {ex}")

# S3
try:
    s3 = boto3.client("s3", region_name="us-east-1")
    buckets = s3.list_buckets()
    for b in buckets.get("Buckets", []):
        if "alchemiser-prod" in b["Name"]:
            print(f"FOUND S3 Bucket: {b['Name']}")
except Exception as ex:
    print(f"S3 check: {ex}")

# DynamoDB
try:
    ddb = boto3.client("dynamodb", region_name="us-east-1")
    paginator = ddb.get_paginator("list_tables")
    for page in paginator.paginate():
        for t in page["TableNames"]:
            if "alchemiser-prod" in t:
                print(f"FOUND DynamoDB Table: {t}")
except Exception as ex:
    print(f"DynamoDB check: {ex}")

# SQS
try:
    sqs = boto3.client("sqs", region_name="us-east-1")
    queues = sqs.list_queues(QueueNamePrefix="alchemiser-prod")
    for q in queues.get("QueueUrls", []):
        print(f"FOUND SQS Queue: {q}")
except Exception as ex:
    print(f"SQS check: {ex}")

# SNS
try:
    sns = boto3.client("sns", region_name="us-east-1")
    topics = sns.list_topics()
    for t in topics.get("Topics", []):
        if "alchemiser-prod" in t["TopicArn"]:
            print(f"FOUND SNS Topic: {t['TopicArn']}")
except Exception as ex:
    print(f"SNS check: {ex}")

# CloudWatch alarms
try:
    cw = boto3.client("cloudwatch", region_name="us-east-1")
    alarms = cw.describe_alarms(AlarmNamePrefix="alchemiser-prod")
    for a in alarms.get("MetricAlarms", []):
        print(f"FOUND CW Alarm: {a['AlarmName']}")
except Exception as ex:
    print(f"CloudWatch check: {ex}")

# Scheduler schedules
try:
    scheduler = boto3.client("scheduler", region_name="us-east-1")
    scheds = scheduler.list_schedules(NamePrefix="alchemiser-prod")
    for s in scheds.get("Schedules", []):
        print(f"FOUND Schedule: {s['Name']}")
except Exception as ex:
    print(f"Scheduler check: {ex}")

print("\n=== SCAN COMPLETE ===")
