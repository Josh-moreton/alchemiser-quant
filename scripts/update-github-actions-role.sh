#!/bin/bash
# Update GitHubActionsRole with necessary IAM permissions for CloudFormation deployments

set -e

echo "🔐 Updating GitHubActionsRole with IAM permissions for CloudFormation"
echo "================================================================"

# Define the policy document
POLICY_JSON=$(cat <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowIAMManagementForAlchemiserResources",
      "Effect": "Allow",
      "Action": [
        "iam:GetRole",
        "iam:GetRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:CreatePolicy",
        "iam:GetPolicy",
        "iam:GetPolicyVersion",
        "iam:DeletePolicy",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:ListAttachedRolePolicies",
        "iam:ListRolePolicies",
        "iam:PassRole"
      ],
      "Resource": [
        "arn:aws:iam::211125653762:role/the-alchemiser-v2-*",
        "arn:aws:iam::211125653762:policy/TradingSystemPolicy",
        "arn:aws:iam::211125653762:policy/SchedulerLambdaInvokePolicy"
      ]
    }
  ]
}
EOF
)

# Check if role exists
echo "Checking if GitHubActionsRole exists..."
if ! aws iam get-role --role-name GitHubActionsRole &>/dev/null; then
    echo "❌ Error: GitHubActionsRole not found"
    exit 1
fi

echo "✅ Role found"

# Put the policy
echo "Adding IAM management policy to GitHubActionsRole..."
aws iam put-role-policy \
    --role-name GitHubActionsRole \
    --policy-name AlchemiserIAMManagement \
    --policy-document "$POLICY_JSON"

echo ""
echo "✅ Policy added successfully!"
echo ""
echo "Policy name: AlchemiserIAMManagement"
echo "Applied to: GitHubActionsRole"
echo ""
echo "You can now redeploy with: git push origin main"
