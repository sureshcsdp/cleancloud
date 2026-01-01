"""
Configuration loader for CleanCloud.

Priority (highest to lowest):
1. CLI arguments
2. cleancloud.yaml (current directory)
3. ~/.cleancloud/config.yaml (user home)
4. Default values (config/defaults.py)
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from cleancloud.config.defaults import DEFAULT_CONFIG


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """
    Deep merge two dictionaries.

    Override values take precedence over base values.
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def _load_yaml_file(path: Path) -> Optional[Dict]:
    """Load YAML config file if it exists."""
    if not path.exists():
        return None

    try:
        with open(path, "r") as f:
            content = yaml.safe_load(f)
            return content if content else {}
    except Exception as e:
        # Log warning but don't fail
        print(f"Warning: Failed to load {path}: {e}")
        return None


def load_config(
        config_file: Optional[str] = None,
        cli_overrides: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Load configuration from multiple sources.

    Args:
        config_file: Explicit config file path (from --config flag)
        cli_overrides: Direct overrides from CLI flags

    Returns:
        Merged configuration dictionary
    """
    # Start with defaults
    config = DEFAULT_CONFIG.copy()

    # Layer 1: User home config (~/.cleancloud/config.yaml)
    home_config_path = Path.home() / ".cleancloud" / "config.yaml"
    home_config = _load_yaml_file(home_config_path)
    if home_config:
        config = _deep_merge(config, home_config)

    # Layer 2: Current directory config (./cleancloud.yaml)
    cwd_config_path = Path.cwd() / "cleancloud.yaml"
    cwd_config = _load_yaml_file(cwd_config_path)
    if cwd_config:
        config = _deep_merge(config, cwd_config)

    # Layer 3: Explicit config file (--config path/to/config.yaml)
    if config_file:
        explicit_config = _load_yaml_file(Path(config_file))
        if explicit_config:
            config = _deep_merge(config, explicit_config)
        else:
            raise FileNotFoundError(f"Config file not found: {config_file}")

    # Layer 4: CLI overrides (highest priority)
    if cli_overrides:
        config = _deep_merge(config, cli_overrides)

    return config


def get_rule_config(
        config: Dict[str, Any],
        provider: str,
        rule_name: str,
) -> Dict[str, Any]:
    """
    Get configuration for a specific rule.

    Args:
        config: Full configuration dictionary
        provider: Provider name (aws, azure, gcp)
        rule_name: Rule name (old_ebs_snapshots, unattached_disks, etc)

    Returns:
        Rule-specific configuration
    """
    return (
        config.get("rules", {})
        .get(provider, {})
        .get(rule_name, {})
    )


# Example usage in rules:
# from cleancloud.config.loader import get_rule_config
#
# rule_config = get_rule_config(config, "aws", "old_ebs_snapshots")
# days_old = rule_config.get("days_old", 365)  # Fallback to 365