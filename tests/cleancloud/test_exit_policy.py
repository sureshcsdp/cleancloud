from dataclasses import dataclass

from cleancloud.policy.exit_policy import determine_exit_code


@dataclass
class FakeResult:
    confidence: str


def test_exit_policy_no_issues():
    results = []
    assert determine_exit_code(results) == 0


def test_exit_policy_low_only():
    results = [FakeResult(confidence="Low")]
    assert determine_exit_code(results) == 0


def test_exit_policy_medium_only():
    results = [FakeResult(confidence="Medium")]
    assert determine_exit_code(results) == 0


def test_exit_policy_high_only():
    results = [FakeResult(confidence="High")]
    # Default behavior: report-only (don't fail)
    assert determine_exit_code(results) == 0
    # With explicit flag: fail on HIGH
    assert determine_exit_code(results, fail_on_confidence="HIGH") == 2


def test_exit_policy_mixed_low_medium():
    results = [
        FakeResult(confidence="Low"),
        FakeResult(confidence="Medium"),
    ]
    assert determine_exit_code(results) == 0


def test_exit_policy_mixed_medium_high():
    results = [
        FakeResult(confidence="Medium"),
        FakeResult(confidence="High"),
    ]
    # Default behavior: report-only (don't fail)
    assert determine_exit_code(results) == 0
    # With explicit flag: fail on HIGH
    assert determine_exit_code(results, fail_on_confidence="HIGH") == 2
    # With explicit flag: fail on MEDIUM or higher
    assert determine_exit_code(results, fail_on_confidence="MEDIUM") == 2


def test_exit_policy_all_levels():
    results = [
        FakeResult(confidence="Low"),
        FakeResult(confidence="Medium"),
        FakeResult(confidence="High"),
    ]
    # Default behavior: report-only (don't fail)
    assert determine_exit_code(results) == 0
    # With explicit flag: fail on HIGH
    assert determine_exit_code(results, fail_on_confidence="HIGH") == 2
    # With explicit flag: fail on MEDIUM or higher
    assert determine_exit_code(results, fail_on_confidence="MEDIUM") == 2
    # With explicit flag: fail on LOW or higher (all findings)
    assert determine_exit_code(results, fail_on_confidence="LOW") == 2
    # With fail_on_findings: fail on any finding
    assert determine_exit_code(results, fail_on_findings=True) == 2
