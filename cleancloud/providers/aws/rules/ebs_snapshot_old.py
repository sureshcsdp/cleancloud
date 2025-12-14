from datetime import datetime, timezone
from typing import List

import boto3

from cleancloud.models.confidence import Confidence, Risk
from cleancloud.models.finding import Finding


def find_old_ebs_snapshots(
    session: boto3.Session,
    region: str,
    days_old: int = 90,
) -> List[Finding]:
    """
    Find EBS snapshots older than `days_old`.

    Conservative rule:
    - No AMI linkage detection yet (future enhancement)

    IAM permissions:
    - ec2:DescribeSnapshots
    """
    ec2 = session.client("ec2", region_name=region)
    paginator = ec2.get_paginator("describe_snapshots")

    now = datetime.now(timezone.utc)
    findings: List[Finding] = []

    for page in paginator.paginate(OwnerIds=["self"]):
        for snap in page.get("Snapshots", []):
            start_time = snap["StartTime"]
            age_days = (now - start_time).days

            if age_days >= days_old:
                findings.append(
                    Finding(
                        provider="aws",
                        rule_id="aws.ebs.snapshot.old",
                        resource_type="ebs_snapshot",
                        resource_id=snap["SnapshotId"],
                        region=region,
                        title="Old EBS snapshot",
                        summary=f"EBS snapshot older than {days_old} days",
                        reason="Snapshot age exceeds configured threshold",
                        risk=Risk.LOW.value,
                        confidence=Confidence.HIGH.value,
                        detected_at=now,
                        details={
                            "start_time": start_time.isoformat(),
                            "age_days": age_days,
                            "volume_id": snap.get("VolumeId"),
                            "tags": snap.get("Tags", []),
                        },
                    )
                )

    return findings
