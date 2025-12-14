import os
from typing import List, Optional

from azure.identity import ClientSecretCredential
from azure.mgmt.resource import SubscriptionClient


class AzureSession:
    """
    Represents an authenticated Azure session.

    Attributes:
        credential: Azure credential object for API calls
        default_subscription_id: Optional subscription ID to scan
    """

    def __init__(
        self, credential: ClientSecretCredential, default_subscription_id: Optional[str] = None
    ):
        self.credential = credential
        self.default_subscription_id = default_subscription_id

    def list_subscription_ids(self) -> List[str]:
        """
        List all accessible Azure subscription IDs for this credential.
        If default_subscription_id is provided, return only that.
        """
        if self.default_subscription_id:
            return [self.default_subscription_id]

        sub_client = SubscriptionClient(self.credential)
        subscriptions = sub_client.subscriptions.list()
        subscription_ids = [sub.subscription_id for sub in subscriptions]

        return subscription_ids


def create_azure_session(
    subscription_id: Optional[str] = None,
) -> AzureSession:
    """
    Authenticate to Azure using environment variables (non-interactive, CI/CD friendly).

    Required environment variables:
        - AZURE_CLIENT_ID
        - AZURE_TENANT_ID
        - AZURE_CLIENT_SECRET

    Optional:
        - AZURE_SUBSCRIPTION_ID (overrides subscription discovery)
    """
    client_id = os.environ.get("AZURE_CLIENT_ID")
    tenant_id = os.environ.get("AZURE_TENANT_ID")
    client_secret = os.environ.get("AZURE_CLIENT_SECRET")

    if not all([client_id, tenant_id, client_secret]):
        raise EnvironmentError(
            "Missing Azure environment variables for authentication. "
            "Set AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET."
        )

    # Allow subscription_id override via env var
    subscription_env = os.environ.get("AZURE_SUBSCRIPTION_ID")
    default_sub = subscription_id or subscription_env

    credential = ClientSecretCredential(
        client_id=client_id,
        client_secret=client_secret,
        tenant_id=tenant_id,
    )

    return AzureSession(credential=credential, default_subscription_id=default_sub)
