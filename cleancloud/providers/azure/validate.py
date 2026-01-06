from typing import List, Optional

import click


def validate_subscription_params(
    subscriptions: Optional[List[str]], all_subscriptions: bool
) -> None:
    """Validate Azure subscription parameters.

    Default behavior (no flags): scan all subscriptions
    --subscription <id>: scan specific subscription(s)
    --all-subscriptions: explicit all (same as default)
    """

    # Both flags specified - this is redundant but acceptable
    if subscriptions and all_subscriptions:
        click.echo("⚠️  Warning: --all-subscriptions flag is redundant with --subscription")
        click.echo("   Will scan the specified subscriptions only")
        click.echo()
