from common import AgeThresholds, UntaggedThreshold

AZURE_POLICIES = {
    "old_snapshots": AgeThresholds(
        medium_days=30,
        high_days=90,
    ),

    "unattached_disks": AgeThresholds(
        medium_days=7,
        high_days=14,
    ),

    "untagged_resources": UntaggedThreshold(
        min_age_days=7,
    ),
}
