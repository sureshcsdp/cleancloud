"""
Default configuration values for CleanCloud rules.

These are conservative defaults that prioritize safety over aggressiveness.
Users can override via cleancloud.yaml or CLI flags.
"""

DEFAULT_CONFIG = {
    "rules": {
        "aws": {
            "old_ebs_snapshots": {
                "days_old": 365,  # Conservative: 1 year
                "confidence": {
                    "high": 365,  # 1 year = HIGH confidence
                    "medium": 180,  # 6 months = MEDIUM confidence
                },
            },
            "unattached_volumes": {
                "confidence": {
                    "high": 14,  # 2 weeks unattached = HIGH
                    "medium": 7,  # 1 week = MEDIUM
                },
            },
            "infinite_log_retention": {
                "confidence": {
                    "high": 30,  # Log group >30 days old = HIGH
                },
            },
            "untagged_resources": {
                "min_age_days": 7,  # Ignore resources <7 days old
            },
        },
        "azure": {
            "unattached_disks": {
                "confidence": {
                    "high": 14,  # 2 weeks unattached = HIGH
                    "medium": 7,  # 1 week = MEDIUM
                },
            },
            "old_snapshots": {
                "confidence": {
                    "high": 90,  # 3 months = HIGH
                    "medium": 30,  # 1 month = MEDIUM
                },
            },
            "untagged_resources": {
                "min_age_days": 7,  # Ignore resources <7 days old
            },
            "unused_public_ips": {
                # Public IPs are immediate HIGH confidence (cost + security)
                "confidence": {
                    "high": 0,  # Immediate
                },
            },
        },
    }
}