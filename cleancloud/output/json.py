import json
from pathlib import Path
from typing import Any, Dict


def write_json(data: Dict[str, Any], output_file: Path):
    """
    Writes JSON output.
    Expected shape:
    {
      "summary": {...},
      "findings": List[Finding]
    }
    """
    serialised = {
        "summary": data["summary"],
        "findings": [f.to_dict() for f in data["findings"]],
    }

    with output_file.open("w") as f:
        json.dump(serialised, f, indent=2)
