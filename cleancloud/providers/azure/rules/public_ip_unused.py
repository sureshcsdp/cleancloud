from datetime import datetime, timezone
from typing import List, Optional

from azure.mgmt.network import NetworkManagementClient

from cleancloud.models.confidence import Confidence, Risk
from cleancloud.models.finding import Finding


def find_unused_public_ips(
    *,
    subscription_id: str,
    credential,
    region_filter: str = None,
    client: Optional[NetworkManagementClient] = None,
) -> List[Finding]:
    """
    Find unattached or unused Azure Public IPs.
    Read-only, safe.

    IAM permissions:
    - Microsoft.Network/publicIPAddresses/read
    """
    findings: List[Finding] = []

    net_client = client or NetworkManagementClient(
        credential=credential,
        subscription_id=subscription_id,
    )

    for pip in net_client.public_ip_addresses.list_all():
        if region_filter and pip.location != region_filter:
            continue

        # Skip attached IPs
        if pip.ip_configuration is not None:
            continue

        findings.append(
            Finding(
                provider="azure",
                rule_id="azure.public_ip_unused",
                resource_type="azure.public_ip",
                resource_id=pip.id,
                region=pip.location,
                title="Unused Azure Public IP",
                summary="Public IP is not attached to any resource",
                reason="IP configuration is None (not attached)",
                risk=Risk.LOW.value,
                confidence=Confidence.HIGH.value,
                detected_at=datetime.now(timezone.utc),
                details={
                    "resource_name": pip.name,
                    "subscription_id": subscription_id,
                    "attached": False,
                    "ip_address": pip.ip_address,
                    "tags_present": bool(pip.tags),
                },
            )
        )

    return findings
