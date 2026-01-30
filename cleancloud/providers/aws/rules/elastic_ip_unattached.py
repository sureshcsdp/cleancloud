from datetime import datetime, timezone
from typing import List

import boto3
from botocore.exceptions import ClientError

from cleancloud.core.confidence import ConfidenceLevel
from cleancloud.core.evidence import Evidence
from cleancloud.core.finding import Finding
from cleancloud.core.risk import RiskLevel


def find_unattached_elastic_ips(
    session: boto3.Session,
    region: str,
    days_unattached: int = 30,
) -> List[Finding]:
    """
    Find Elastic IPs that are not attached to any instance for 30+ days.

    Unattached Elastic IPs cost $0.005/hour (~$3.60/month) when not associated.

    SAFE RULE (review-only):
    - EIP does not have AssociationId (not attached)
    - EIP age >= days_unattached threshold

    IAM permissions:
    - ec2:DescribeAddresses
    """
    ec2 = session.client("ec2", region_name=region)

    now = datetime.now(timezone.utc)
    findings: List[Finding] = []

    try:
        # Note: describe_addresses is not pageable
        response = ec2.describe_addresses()
        for eip in response.get("Addresses", []):
            # Skip if attached to an instance or network interface
            if "AssociationId" in eip:
                continue

            # Calculate age since allocation
            allocation_time = eip.get("AllocationTime")
            if not allocation_time:
                # Classic EIPs might not have AllocationTime, skip age check
                age_days = None
            else:
                age_days = (now - allocation_time).days

            # Apply age threshold (skip if too young)
            if age_days is not None and age_days < days_unattached:
                continue

            # Build evidence
            signals_used = ["Elastic IP is not associated with any instance or network interface"]
            if age_days is not None:
                signals_used.append(
                    f"Elastic IP has been unattached for {age_days} days, exceeding threshold of {days_unattached} days"
                )

            evidence = Evidence(
                signals_used=signals_used,
                signals_not_checked=[
                    "Application-level usage",
                    "Manual operational workflows",
                    "Future planned attachments",
                    "Disaster recovery intent",
                ],
                time_window=f"{days_unattached} days",
            )

            # Build details
            details = {
                "public_ip": eip.get("PublicIp"),
                "domain": eip.get("Domain", "vpc"),
            }

            if age_days is not None:
                details["age_days"] = age_days
                details["allocation_time"] = allocation_time.isoformat()

            if "Tags" in eip:
                details["tags"] = eip["Tags"]

            findings.append(
                Finding(
                    provider="aws",
                    rule_id="aws.ec2.elastic_ip.unattached",
                    resource_type="aws.ec2.elastic_ip",
                    resource_id=eip["AllocationId"],
                    region=region,
                    title="Unattached Elastic IP",
                    summary=(
                        f"Elastic IP unattached for {age_days} days (costs $3.60/month)"
                        if age_days
                        else "Elastic IP not attached to any instance"
                    ),
                    reason=(
                        f"Elastic IP has been unattached for {age_days} days, incurring charges"
                        if age_days
                        else "Elastic IP not attached, incurring charges"
                    ),
                    risk=RiskLevel.LOW,
                    confidence=ConfidenceLevel.HIGH,  # Clear signal: unattached EIPs cost money
                    detected_at=now,
                    evidence=evidence,
                    details=details,
                )
            )

    except ClientError as e:
        if e.response["Error"]["Code"] == "UnauthorizedOperation":
            raise PermissionError("Missing required IAM permission: ec2:DescribeAddresses") from e
        raise

    return findings
