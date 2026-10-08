"""Download the complete Khallaf 2026 fUSI dataset from Edmond."""

import argparse
from pathlib import Path

from confusius.datasets import fetch_khallaf_2026

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "work",
        help="Parent directory for the downloaded khallaf-2026-bids tree.",
    )
    args = parser.parse_args()
    print(fetch_khallaf_2026(data_dir=args.data_dir, sourcedata=True))
