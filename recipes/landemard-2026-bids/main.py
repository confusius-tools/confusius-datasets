"""Stage an existing Landemard BIDS tree without conversion."""

import argparse
import shutil
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
with (ROOT / "pyproject.toml").open("rb") as source:
    VERSION = tomllib.load(source)["project"]["version"]
DEFAULT_OUT = ROOT.parents[1] / "publish" / "datasets" / ROOT.name / VERSION

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src", type=Path, help="Existing BIDS tree.")
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT,
        help=f"Output BIDS root (default: {DEFAULT_OUT}).",
    )
    args = parser.parse_args()
    shutil.copytree(args.src.expanduser(), args.out.expanduser())
    print(args.out)
