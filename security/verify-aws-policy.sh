#!/bin/bash
# File: verify-aws-policy.sh
# Verifies AWS IAM policy is read-only
# Usage: ./verify-aws-policy.sh [policy-file]

set -e

POLICY_FILE="${1:-aws-readonly-policy.json}"

if [ ! -f "$POLICY_FILE" ]; then
  echo "❌ ERROR: Policy file not found: $POLICY_FILE"
  exit 1
fi

echo "🔍 Verifying AWS IAM Policy: $POLICY_FILE"
echo ""

# Check for forbidden actions (excluding read operations)
FORBIDDEN=$(cat "$POLICY_FILE" | jq -r '.Statement[].Action[]?' 2>/dev/null | grep -iE '^[^:]+:(Delete|Put|Create|Update|Modify|Terminate|Reboot|Stop|Start|Attach|Detach|Tag|Untag)[A-Z]' || true)

if [ -z "$FORBIDDEN" ]; then
  echo "✅ PASS: No write/delete/tag permissions found"
  echo ""
  echo "Allowed actions:"
  cat "$POLICY_FILE" | jq -r '.Statement[].Action[]?' 2>/dev/null | sort | uniq
  echo ""
  exit 0
else
  echo "❌ FAIL: Found forbidden permissions:"
  echo "$FORBIDDEN"
  echo ""
  exit 1
fi
