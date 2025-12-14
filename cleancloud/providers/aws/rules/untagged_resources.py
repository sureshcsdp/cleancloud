from datetime import datetime, timezone
from typing import List

import boto3

from cleancloud.models.confidence import Confidence, Risk
from cleancloud.models.finding import Finding


def find_untagged_resources(
    session: boto3.Session,
    region: str,
) -> List[Finding]:
    """
    Detect untagged AWS resources:
    - EBS volumes
    - S3 buckets
    - CloudWatch log groups

    IAM permissions:
    - ec2:DescribeVolumes
    - s3:ListAllMyBuckets
    - s3:GetBucketTagging
    - logs:DescribeLogGroups
    """
    findings: List[Finding] = []
    now = datetime.now(timezone.utc)

    # --- EBS Volumes ---
    ec2 = session.client("ec2", region_name=region)
    for page in ec2.get_paginator("describe_volumes").paginate():
        for vol in page.get("Volumes", []):
            if not vol.get("Tags"):
                findings.append(
                    Finding(
                        provider="aws",
                        rule_id="aws.resource.untagged",
                        resource_type="ebs_volume",
                        resource_id=vol["VolumeId"],
                        region=region,
                        title="Untagged EBS volume",
                        summary="EBS volume has no tags",
                        reason="No tags found on resource",
                        risk=Risk.LOW.value,
                        confidence=Confidence.MEDIUM.value,
                        detected_at=now,
                        details={
                            "availability_zone": vol["AvailabilityZone"],
                            "size_gb": vol["Size"],
                        },
                    )
                )

    # --- S3 Buckets (global) ---
    s3 = session.client("s3")
    for bucket in s3.list_buckets().get("Buckets", []):
        bucket_name = bucket["Name"]
        try:
            tag_set = s3.get_bucket_tagging(Bucket=bucket_name).get("TagSet", [])
        except s3.exceptions.ClientError:
            tag_set = []

        if not tag_set:
            findings.append(
                Finding(
                    provider="aws",
                    rule_id="aws.resource.untagged",
                    resource_type="s3_bucket",
                    resource_id=bucket_name,
                    region=None,
                    title="Untagged S3 bucket",
                    summary="S3 bucket has no tags",
                    reason="No tags found on resource",
                    risk=Risk.LOW.value,
                    confidence=Confidence.MEDIUM.value,
                    detected_at=now,
                    details={},
                )
            )

    # --- CloudWatch Log Groups ---
    logs = session.client("logs", region_name=region)
    for page in logs.get_paginator("describe_log_groups").paginate():
        for lg in page.get("logGroups", []):
            if not lg.get("tags"):
                findings.append(
                    Finding(
                        provider="aws",
                        rule_id="aws.resource.untagged",
                        resource_type="cloudwatch_log_group",
                        resource_id=lg["logGroupName"],
                        region=region,
                        title="Untagged CloudWatch log group",
                        summary="Log group has no tags",
                        reason="No tags found on resource",
                        risk=Risk.LOW.value,
                        confidence=Confidence.MEDIUM.value,
                        detected_at=now,
                        details={},
                    )
                )

    return findings
