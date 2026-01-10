#!/bin/bash
# File: verify-azure-role.sh
# Verifies Azure role is read-only
# Usage: ./verify-azure-role.sh [role-name]

set -e

ROLE_NAME="${1:-Reader}"

echo "🔍 Verifying Azure Role: $ROLE_NAME"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
  echo "❌ ERROR: Azure CLI (az) not found. Please install: https://docs.microsoft.com/cli/azure/install-azure-cli"
  exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
  echo "❌ ERROR: Not logged in to Azure. Run 'az login' first."
  exit 1
fi

# Get role definition
echo "Fetching role definition..."
ACTIONS=$(az role definition list --name "$ROLE_NAME" --output json 2>/dev/null | jq -r '.[0].permissions[0].actions[]?' || true)

if [ -z "$ACTIONS" ]; then
  echo "❌ ERROR: Role not found or no permissions: $ROLE_NAME"
  exit 1
fi

# Check for write actions (excluding */read)
FORBIDDEN=$(echo "$ACTIONS" | grep -iE '(delete|write|create|update|action)' | grep -v '^\*/read$' || true)

if [ -z "$FORBIDDEN" ]; then
  echo "✅ PASS: Role is read-only"
  echo ""
  echo "Allowed actions:"
  echo "$ACTIONS"
  echo ""
  exit 0
else
  echo "❌ FAIL: Found write permissions:"
  echo "$FORBIDDEN"
  echo ""
  exit 1
fi
