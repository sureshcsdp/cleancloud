import json
import os
import subprocess
import tempfile

import pytest


@pytest.mark.e2e
@pytest.mark.azure
def test_cli_azure_scan_json_output():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "out.json")

        result = subprocess.run(
            [
                "cleancloud",
                "scan",
                "--provider",
                "azure",
                "--output",
                "json",
                "--output-file",
                output_file,
            ],
            capture_output=True,
            text=True,
        )

        # CLI should not crash
        assert result.returncode == 0

        # Output file must exist
        assert os.path.exists(output_file)

        # JSON must be valid
        with open(output_file) as f:
            data = json.load(f)

        assert "summary" in data
        assert "findings" in data
        assert isinstance(data["findings"], list)
