"""Verify the Khallaf recipe requests the complete dataset without network access."""

import runpy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

repository = Path(__file__).resolve().parents[1]
recipe = repository / "recipes" / "khallaf-2026-bids" / "main.py"

with TemporaryDirectory() as directory:
    parent = Path(directory)
    for arguments, expected_parent in (
        (["main.py"], repository / "work"),
        (["main.py", "--data-dir", str(parent)], parent),
    ):
        with (
            patch("sys.argv", arguments),
            patch(
                "confusius.datasets.fetch_khallaf_2026",
                return_value=expected_parent / "khallaf-2026-bids",
            ) as fetch,
        ):
            runpy.run_path(str(recipe), run_name="__main__")
            fetch.assert_called_once_with(data_dir=expected_parent, sourcedata=True)

print("PASS: complete download, default and custom destinations, no network access")
