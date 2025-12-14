from datetime import datetime, timezone
from typing import List

import boto3

from cleancloud.models.confidence import Confidence, Risk
from cleancloud.models.finding import Finding


def find_inactive_cloudwatch_logs(
    session: boto3.Session,
    region: str,
) -> List[Finding]:
    """
    Find CloudWatch log groups with:
    - Infinite retention (never expire)

    NOTE:
    Ingestion activity is intentionally NOT inferred in MVP
    to avoid false positives.

    IAM permissions:
    - logs:DescribeLogGroups
    """
    logs = session.client("logs", region_name=region)
    paginator = logs.get_paginator("describe_log_groups")

    findings: List[Finding] = []
    now = datetime.now(timezone.utc)

    for page in paginator.paginate():
        for lg in page.get("logGroups", []):
            retention_days = lg.get("retentionInDays")  # None = never expire

            if retention_days is None:
                findings.append(
                    Finding(
                        provider="aws",
                        rule_id="aws.cloudwatch.logs.infinite_retention",
                        resource_type="cloudwatch_log_group",
                        resource_id=lg["logGroupName"],
                        region=region,
                        title="CloudWatch log group with infinite retention",
                        summary="Log group has no retention policy configured",
                        reason="Retention is not set (logs never expire)",
                        risk=Risk.LOW.value,
                        confidence=Confidence.HIGH.value,
                        detected_at=now,
                        details={
                            "stored_bytes": lg.get("storedBytes"),
                            "retention_days": retention_days,
                        },
                    )
                )

    return findings
