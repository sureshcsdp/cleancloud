from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass(frozen=True)
class IgnoreTagRuleConfig:
    key: str
    value: Optional[str] = None


@dataclass
class TagFilteringConfig:
    enabled: bool
    ignore: List[IgnoreTagRuleConfig]

@dataclass
class ConfidenceDaysConfig:
    """Age thresholds for confidence levels."""
    high: int
    medium: int


@dataclass
class AWSRuleConfig:
    """AWS-specific rule configuration."""
    old_ebs_snapshots: Optional[Dict[str, Any]] = None
    unattached_volumes: Optional[Dict[str, Any]] = None
    infinite_log_retention: Optional[Dict[str, Any]] = None
    untagged_resources: Optional[Dict[str, Any]] = None


@dataclass
class AzureRuleConfig:
    """Azure-specific rule configuration."""
    unattached_disks: Optional[Dict[str, Any]] = None
    old_snapshots: Optional[Dict[str, Any]] = None
    untagged_resources: Optional[Dict[str, Any]] = None
    unused_public_ips: Optional[Dict[str, Any]] = None


@dataclass
class RulesConfig:
    """All rules configuration."""
    aws: Dict[str, Any] = field(default_factory=dict)
    azure: Dict[str, Any] = field(default_factory=dict)
    gcp: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Top-Level Config
# ============================================================================

@dataclass
class CleanCloudConfig:
    tag_filtering: Optional[TagFilteringConfig] = None
    rules: Optional[RulesConfig] = None

    @classmethod
    def empty(cls) -> "CleanCloudConfig":
        return cls(
            tag_filtering=None,
            rules=RulesConfig()
        )


# ============================================================================
# Config Loader
# ============================================================================

def load_config(data: Dict[str, Any]) -> CleanCloudConfig:
    """
    Load and validate CleanCloud configuration.

    Args:
        data: Raw configuration dictionary from YAML

    Returns:
        Validated CleanCloudConfig object

    Raises:
        ValueError: If configuration is invalid
    """
    allowed_top_level = {"version", "tag_filtering", "rules"}
    unknown = set(data.keys()) - allowed_top_level
    if unknown:
        raise ValueError(f"Unknown config fields: {unknown}")

    # Load tag filtering config (existing)
    tag_filtering_config = _load_tag_filtering(data.get("tag_filtering"))

    # Load rules config (new)
    rules_config = _load_rules(data.get("rules"))

    return CleanCloudConfig(
        tag_filtering=tag_filtering_config,
        rules=rules_config,
    )


def _load_tag_filtering(tf: Optional[Dict[str, Any]]) -> Optional[TagFilteringConfig]:
    """Load tag filtering configuration."""
    if not tf:
        return None

    if not isinstance(tf, dict):
        raise ValueError("tag_filtering must be a mapping")

    enabled = tf.get("enabled", True)
    ignore = tf.get("ignore", [])

    if not isinstance(ignore, list):
        raise ValueError("tag_filtering.ignore must be a list")

    rules: List[IgnoreTagRuleConfig] = []
    for entry in ignore:
        if not isinstance(entry, dict):
            raise ValueError("Each ignore entry must be a mapping")

        if "key" not in entry:
            raise ValueError("ignore entry must contain 'key'")

        rules.append(
            IgnoreTagRuleConfig(
                key=str(entry["key"]),
                value=str(entry["value"]) if "value" in entry else None,
            )
        )

    return TagFilteringConfig(
        enabled=bool(enabled),
        ignore=rules,
    )


def _load_rules(rules_data: Optional[Dict[str, Any]]) -> RulesConfig:
    """
    Load rules configuration.

    Validates structure but doesn't enforce specific rule names
    to allow for future extensibility.
    """
    if not rules_data:
        return RulesConfig()

    if not isinstance(rules_data, dict):
        raise ValueError("rules must be a mapping")

    # Validate provider-level structure
    allowed_providers = {"aws", "azure", "gcp"}
    unknown_providers = set(rules_data.keys()) - allowed_providers
    if unknown_providers:
        raise ValueError(f"Unknown providers in rules: {unknown_providers}")

    # Extract provider configs (keep as dicts for flexibility)
    aws_config = rules_data.get("aws", {})
    azure_config = rules_data.get("azure", {})
    gcp_config = rules_data.get("gcp", {})

    # Validate each provider config is a dict
    if not isinstance(aws_config, dict):
        raise ValueError("rules.aws must be a mapping")
    if not isinstance(azure_config, dict):
        raise ValueError("rules.azure must be a mapping")
    if not isinstance(gcp_config, dict):
        raise ValueError("rules.gcp must be a mapping")

    return RulesConfig(
        aws=aws_config,
        azure=azure_config,
        gcp=gcp_config,
    )


# ============================================================================
# Helper Functions
# ============================================================================

def get_rule_config(
        config: CleanCloudConfig,
        provider: str,
        rule_name: str,
) -> Dict[str, Any]:
    """
    Get configuration for a specific rule.

    Args:
        config: CleanCloudConfig object
        provider: Provider name (aws, azure, gcp)
        rule_name: Rule name (old_ebs_snapshots, unattached_disks, etc)

    Returns:
        Rule-specific configuration dictionary (empty dict if not found)
    """
    if not config.rules:
        return {}

    provider_config = getattr(config.rules, provider, {})
    if not isinstance(provider_config, dict):
        return {}

    return provider_config.get(rule_name, {})


def get_confidence_threshold(
        rule_config: Dict[str, Any],
        level: str,
        default: int,
) -> int:
    """
    Get confidence threshold for a specific level.

    Args:
        rule_config: Rule configuration dictionary
        level: Confidence level (high, medium, low)
        default: Default value if not configured

    Returns:
        Age threshold in days
    """
    confidence = rule_config.get("confidence", {})
    return confidence.get(level, default)