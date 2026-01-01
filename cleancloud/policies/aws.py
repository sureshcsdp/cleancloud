from .common import UntaggedThreshold, MinAgeThreshold

AWS_POLICIES = {
    "old_ebs_snapshots": MinAgeThreshold(
        min_age_days=90,
    ),

    "untagged_resources": UntaggedThreshold(
        min_age_days=7,
    ),
}
