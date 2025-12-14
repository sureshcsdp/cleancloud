import pytest

from cleancloud.providers.azure.session import create_azure_session


@pytest.mark.e2e
@pytest.mark.azure
def test_azure_auth_and_list_subscriptions():

    session = create_azure_session()
    subs = session.list_subscription_ids()

    assert isinstance(subs, list)
    assert len(subs) >= 1
