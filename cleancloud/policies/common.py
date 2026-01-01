from dataclasses import dataclass


@dataclass(frozen=True)
class MinAgeThreshold:
    min_age_days: int

@dataclass(frozen=True)
class AgeThresholds:
    medium_days: int
    high_days: int

@dataclass(frozen=True)
class UntaggedThreshold:
    min_age_days: int
