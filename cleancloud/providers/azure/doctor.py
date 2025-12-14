from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
from azure.mgmt.compute import ComputeManagementClient

from cleancloud.providers.azure.session import create_azure_session


def run_azure_doctor() -> None:
    """
    Validate Azure credentials and required read-only permissions.

    Raises PermissionError if:
        - Authentication fails
        - No subscriptions are accessible
        - Service principal lacks read access to disks
    """

    print("🔐 Validating Azure credentials...")

    try:
        session = create_azure_session()
        subscription_ids = session.list_subscription_ids()
    except ClientAuthenticationError as e:
        raise PermissionError("Azure authentication failed") from e

    if not subscription_ids:
        raise PermissionError(
            "No accessible Azure subscriptions found. "
            "Ensure the service principal has at least Reader role on one subscription."
        )

    print("✅ Azure credentials valid")
    print(f"📦 Accessible subscriptions: {len(subscription_ids)}")

    # Validate permissions using first subscription
    subscription_id = subscription_ids[0]
    print(f"🔍 Checking read permissions on subscription {subscription_id}")

    try:
        compute_client = ComputeManagementClient(
            credential=session.credential,
            subscription_id=subscription_id,
        )

        # Required permission: Microsoft.Compute/disks/read
        disks = compute_client.disks.list()
        next(disks, None)  # Try to fetch at least one disk

    except HttpResponseError as e:
        raise PermissionError(
            "Missing required Azure permission: Microsoft.Compute/disks/read. "
            "Ensure the service principal has Reader role on the subscription."
        ) from e

    print("✅ Required Azure permissions validated")
    print("🎉 Azure environment is ready for CleanCloud")
