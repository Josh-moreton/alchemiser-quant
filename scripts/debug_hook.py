"""Business Unit: scripts | Status: current."""
from __future__ import annotations

import json

import boto3

cfn = boto3.client("cloudformation", region_name="us-east-1")

# Check if stack exists
stacks = cfn.list_stacks(
    StackStatusFilter=[
        "REVIEW_IN_PROGRESS",
        "CREATE_COMPLETE",
        "CREATE_FAILED",
        "CREATE_IN_PROGRESS",
    ]
)
prod = [s for s in stacks["StackSummaries"] if s["StackName"] == "alchemiser-prod"]

if not prod:
    print("No alchemiser-prod stack found in active states.")
    print("Creating a changeset to trigger the hook failure for debugging...")

    # Build first if needed
    import subprocess
    import sys

    print("Running sam build...")
    result = subprocess.run(
        ["sam", "build", "--parallel", "--config-env", "prod"],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        print(f"sam build failed: {result.stderr[:500]}")
        sys.exit(1)
    print("Build complete. Creating changeset via sam deploy --no-execute-changeset...")

    result = subprocess.run(
        [
            "sam",
            "deploy",
            "--no-fail-on-empty-changeset",
            "--no-execute-changeset",
            "--resolve-s3",
            "--config-env",
            "prod",
            "--parameter-overrides",
            "Stage=prod",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    print("STDOUT:", result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
    print("STDERR:", result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
    if "FAILED" in result.stdout or "FAILED" in result.stderr:
        print("\n>>> Changeset FAILED - inspecting...")

    # Wait for it to complete or fail
    import time

    for i in range(30):
        time.sleep(2)
        try:
            cs = cfn.describe_change_set(
                StackName="alchemiser-prod",
                ChangeSetName="debug-hook-failure",
            )
            status = cs["Status"]
            print(f"  [{i*2}s] Status: {status}")
            if status in ("FAILED", "CREATE_COMPLETE"):
                if status == "FAILED":
                    print(f"  Reason: {cs.get('StatusReason', 'N/A')}")
                break
        except Exception as ex:
            print(f"  [{i*2}s] Waiting... ({ex})")

    prod = [{"StackName": "alchemiser-prod"}]

print(f"\nStack found: {prod[0]['StackName']}")

# Get changesets
cs_list = cfn.list_change_sets(StackName="alchemiser-prod")
for s in cs_list["Summaries"]:
    print(f"\nChangeset: {s['ChangeSetName']}")
    print(f"  Status: {s['Status']}")
    print(f"  Reason: {s.get('StatusReason', 'N/A')}")

# Get stack events
try:
    events = cfn.describe_stack_events(StackName="alchemiser-prod")
    print("\nStack Events (last 10):")
    for e in events["StackEvents"][:10]:
        logical = e.get("LogicalResourceId", "")
        status = e.get("ResourceStatus", "")
        reason = e.get("ResourceStatusReason", "")
        print(f"  {logical} | {status} | {reason}")
except Exception as ex:
    print(f"Events error: {ex}")

# Try describe-change-set-hooks
if cs_list["Summaries"]:
    cs_name = cs_list["Summaries"][0]["ChangeSetName"]
    try:
        hooks = cfn.describe_change_set_hooks(
            StackName="alchemiser-prod", ChangeSetName=cs_name
        )
        print(f"\n=== Hook Results for {cs_name} ===")
        for h in hooks.get("Hooks", []):
            print(f"  Hook: {h.get('TypeName', '?')}")
            print(f"  Status: {h.get('HookStatus', '?')}")
            print(f"  Reason: {h.get('HookStatusReason', '?')}")
            print(f"  Invocation: {h.get('InvocationPoint', '?')}")
            target = h.get("TargetDetails", {})
            print(f"  Target: {json.dumps(target, indent=4)}")
            print()
    except Exception as ex:
        print(f"\ndescribe_change_set_hooks error: {ex}")

# Also try CloudTrail for the hook invocation
print("\n=== Checking CloudTrail for recent EarlyValidation events ===")
try:
    ct = boto3.client("cloudtrail", region_name="us-east-1")
    from datetime import datetime, timedelta, timezone

    events_resp = ct.lookup_events(
        LookupAttributes=[
            {"AttributeKey": "EventName", "AttributeValue": "CreateChangeSet"},
        ],
        StartTime=datetime.now(timezone.utc) - timedelta(hours=2),
        MaxResults=5,
    )
    for ev in events_resp.get("Events", []):
        print(f"  Time: {ev.get('EventTime')}")
        print(f"  Name: {ev.get('EventName')}")
        detail = json.loads(ev.get("CloudTrailEvent", "{}"))
        error_code = detail.get("errorCode", "")
        error_msg = detail.get("errorMessage", "")
        if error_code or error_msg:
            print(f"  Error: {error_code} - {error_msg}")
        # Look for hook info in responseElements
        resp_elem = detail.get("responseElements")
        if resp_elem:
            print(f"  Response: {json.dumps(resp_elem, indent=2, default=str)[:500]}")
        print()
except Exception as ex:
    print(f"  CloudTrail error: {ex}")
