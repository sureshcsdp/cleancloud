from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Optional, Tuple

import click

from cleancloud.core.finding import Finding
from cleancloud.output.progress import advance
from cleancloud.providers.azure.rules.ebs_snapshots_old import find_old_snapshots
from cleancloud.providers.azure.rules.public_ip_unused import find_unused_public_ips
from cleancloud.providers.azure.rules.unattached_managed_disks import (
    find_unattached_managed_disks,
)
from cleancloud.providers.azure.rules.untagged_resources import (
    find_untagged_resources as find_azure_untagged_resources,
)
from cleancloud.providers.azure.session import create_azure_session
from cleancloud.providers.azure.validate import validate_subscription_params


def scan_azure_with_region_selection(
    region: Optional[str],
    subscriptions: Optional[List[str]] = None,
    all_subscriptions: bool = False,
) -> Tuple[str, List[Finding], List[str]]:
    # Validate subscription parameters
    validate_subscription_params(subscriptions, all_subscriptions)

    click.echo("🔍 Authenticating to Azure")
    click.echo()

    session = create_azure_session()
    all_accessible_subscriptions = session.list_subscription_ids()

    if not all_accessible_subscriptions:
        raise PermissionError("No accessible Azure subscriptions found")

    # Determine which subscriptions to scan
    if subscriptions:
        # Specific subscription(s) requested
        subscription_ids = subscriptions
        subscription_selection_mode = "explicit"

        # Validate that requested subscriptions are accessible
        inaccessible = set(subscription_ids) - set(all_accessible_subscriptions)
        if inaccessible:
            click.echo(f"⚠️  Warning: {len(inaccessible)} subscription(s) not accessible:")
            for sub_id in sorted(inaccessible)[:5]:
                click.echo(f"   • {sub_id}")
            if len(inaccessible) > 5:
                click.echo(f"   ... and {len(inaccessible) - 5} more")
            click.echo()

            # Only scan accessible ones
            subscription_ids = [s for s in subscription_ids if s in all_accessible_subscriptions]

            if not subscription_ids:
                raise PermissionError("None of the specified subscriptions are accessible")

        click.echo(f"✓ Scanning {len(subscription_ids)} specified subscription(s)")
    else:
        # Default: scan all accessible subscriptions
        subscription_ids = all_accessible_subscriptions
        subscription_selection_mode = "all"
        click.echo(f"✓ Found {len(subscription_ids)} accessible subscription(s)")

    click.echo()

    findings = scan_azure_subscriptions(
        subscription_ids,
        session.credential,
        region,
    )

    click.echo()

    # Return subscription info (not region info)
    subscriptions_scanned = subscription_ids

    return subscription_selection_mode, findings, subscriptions_scanned


AZURE_RULES: List[Callable] = [
    find_unattached_managed_disks,
    find_old_snapshots,
    find_azure_untagged_resources,
    find_unused_public_ips,
]


def scan_azure_subscriptions(
    subscription_ids: List[str],
    credential,
    region_filter: Optional[str],
) -> List[Finding]:
    all_findings: List[Finding] = []

    with click.progressbar(
        length=len(subscription_ids),
        label="Scanning Azure subscriptions",
        show_eta=True,
        show_percent=True,
    ) as bar:
        with ThreadPoolExecutor(max_workers=min(4, len(subscription_ids))) as executor:
            futures = {
                executor.submit(
                    _scan_azure_subscription,
                    subscription_id=sub_id,
                    credential=credential,
                    region_filter=region_filter,
                ): sub_id
                for sub_id in subscription_ids
            }

            for future in as_completed(futures):
                sub_id = futures[future]
                try:
                    all_findings.extend(future.result())
                except Exception as e:
                    click.echo(f"⚠️ Subscription {sub_id} failed: {e}")
                finally:
                    advance(bar)

    return all_findings


def _scan_azure_subscription(
    subscription_id: str,
    credential,
    region_filter: Optional[str],
) -> List[Finding]:
    findings: List[Finding] = []

    with click.progressbar(
        length=len(AZURE_RULES),
        label=f"Scanning Azure rules in subscription {subscription_id}",
        show_eta=True,
        show_percent=True,
    ) as bar:
        with ThreadPoolExecutor(max_workers=min(4, len(AZURE_RULES))) as executor:
            futures = [
                executor.submit(
                    rule,
                    subscription_id=subscription_id,
                    credential=credential,
                    region_filter=region_filter,
                )
                for rule in AZURE_RULES
            ]

            for future in as_completed(futures):
                try:
                    rule_findings = future.result()
                    findings.extend(rule_findings)
                except Exception as e:
                    # Trust-first: never fail whole scan
                    click.echo(f"⚠️ Azure rule failed in subscription {subscription_id}: {e}")
                finally:
                    advance(bar)

    return findings
