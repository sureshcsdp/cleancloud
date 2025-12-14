from datetime import datetime, timezone
from typing import List, Optional

from azure.mgmt.compute import ComputeManagementClient

from cleancloud.models.confidence import Confidence, Risk
from cleancloud.models.finding import Finding

MIN_AGE_DAYS_MEDIUM = 30
MIN_AGE_DAYS_HIGH = 90


def _age_in_days(created_at: datetime) -> int:
    now = datetime.now(timezone.utc)
    return (now - created_at).days


def find_old_snapshots(
    *,
    subscription_id: str,
    credential,
    region_filter: str = None,
    client: Optional[ComputeManagementClient] = None,
) -> List[Finding]:
    """
    Find old Azure managed snapshots that may be orphaned.

    Signals used:
    - Snapshot age exceeds conservative thresholds

    This rule is read-only and safe.

    IAM permissions:
    - Microsoft.Compute/snapshots/read
    """

    findings: List[Finding] = []

    compute_client = client or ComputeManagementClient(
        credential=credential,
        subscription_id=subscription_id,
    )

    for snapshot in compute_client.snapshots.list():
        # Azure uses 'location' instead of region
        if region_filter and snapshot.location != region_filter:
            continue

        if not snapshot.time_created:
            continue

        age_days = _age_in_days(snapshot.time_created)

        if age_days >= MIN_AGE_DAYS_HIGH:
            confidence = Confidence.HIGH.value
        elif age_days >= MIN_AGE_DAYS_MEDIUM:
            confidence = Confidence.MEDIUM.value
        else:
            continue  # too new, ignore

        findings.append(
            Finding(
                provider="azure",
                rule_id="azure.old_snapshot",
                resource_type="azure.snapshot",
                resource_id=snapshot.id,
                region=snapshot.location,
                title="Old Azure managed snapshot",
                summary=f"Snapshot has existed for {age_days} days",
                reason="Snapshot age exceeds configured threshold",
                risk=Risk.LOW.value,
                confidence=confidence,
                detected_at=datetime.now(timezone.utc),
                details={
                    "resource_name": snapshot.name,
                    "subscription_id": subscription_id,
                    "age_days": age_days,
                    "disk_size_gb": snapshot.disk_size_gb,
                    "sku": snapshot.sku.name if snapshot.sku else None,
                    "tags_present": bool(snapshot.tags),
                },
            )
        )

    return findings
