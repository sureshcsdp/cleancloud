from datetime import datetime, timedelta, timezone

from cleancloud.providers.aws.rules.elastic_ip_unattached import (
    find_unattached_elastic_ips,
)


def test_find_unattached_elastic_ips(mock_boto3_session):
    region = "us-east-1"
    ec2 = mock_boto3_session._ec2

    old_date = datetime.now(timezone.utc) - timedelta(days=60)
    recent_date = datetime.now(timezone.utc) - timedelta(days=10)

    # Mock describe_addresses (not pageable)
    ec2.describe_addresses.return_value = {
        "Addresses": [
            {
                "AllocationId": "eipalloc-1",
                "PublicIp": "203.0.113.1",
                "Domain": "vpc",
                "AllocationTime": old_date,
                # No AssociationId = unattached
            },
            {
                "AllocationId": "eipalloc-2",
                "PublicIp": "203.0.113.2",
                "Domain": "vpc",
                "AllocationTime": old_date,
                "AssociationId": "eipassoc-123",  # attached
                "InstanceId": "i-123",
            },
            {
                "AllocationId": "eipalloc-3",
                "PublicIp": "203.0.113.3",
                "Domain": "vpc",
                "AllocationTime": recent_date,  # too young
                # No AssociationId = unattached but recent
            },
            {
                "AllocationId": "eipalloc-4",
                "PublicIp": "203.0.113.4",
                "Domain": "standard",
                # No AllocationTime (classic EIP edge case)
                # No AssociationId = unattached
            },
        ]
    }

    findings = find_unattached_elastic_ips(mock_boto3_session, region)
    eip_ids = {f.resource_id for f in findings}

    # Positive: old unattached EIP
    assert "eipalloc-1" in eip_ids

    # Positive: classic EIP without AllocationTime (no age check)
    assert "eipalloc-4" in eip_ids

    # Negative: attached EIP
    assert "eipalloc-2" not in eip_ids

    # Negative: unattached but too recent
    assert "eipalloc-3" not in eip_ids


def test_find_unattached_elastic_ips_custom_threshold(mock_boto3_session):
    region = "us-east-1"
    ec2 = mock_boto3_session._ec2

    date_45_days_ago = datetime.now(timezone.utc) - timedelta(days=45)

    ec2.describe_addresses.return_value = {
        "Addresses": [
            {
                "AllocationId": "eipalloc-5",
                "PublicIp": "203.0.113.5",
                "Domain": "vpc",
                "AllocationTime": date_45_days_ago,
            }
        ]
    }

    # Test with custom 60-day threshold
    findings = find_unattached_elastic_ips(mock_boto3_session, region, days_unattached=60)
    eip_ids = {f.resource_id for f in findings}

    # Should NOT be detected (45 days < 60 days threshold)
    assert "eipalloc-5" not in eip_ids

    # Test with custom 30-day threshold (default)
    findings = find_unattached_elastic_ips(mock_boto3_session, region, days_unattached=30)
    eip_ids = {f.resource_id for f in findings}

    # Should be detected (45 days >= 30 days threshold)
    assert "eipalloc-5" in eip_ids


def test_find_unattached_elastic_ips_empty(mock_boto3_session):
    region = "us-east-1"
    ec2 = mock_boto3_session._ec2

    ec2.describe_addresses.return_value = {"Addresses": []}

    findings = find_unattached_elastic_ips(mock_boto3_session, region)

    assert len(findings) == 0
