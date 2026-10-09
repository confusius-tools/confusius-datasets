from __future__ import annotations

import argparse
import tomllib
from pathlib import Path

from rich.console import Console

from .converter import convert

CONSOLE = Console()
RECIPE = Path(__file__).resolve().parents[2]
with (RECIPE / "pyproject.toml").open("rb") as source:
    VERSION = tomllib.load(source)["project"]["version"]
DEFAULT_OUT = RECIPE.parents[1] / "publish" / "datasets" / RECIPE.name / VERSION


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert Pereira fUSI recordings to fUSI-BIDS.",
    )
    parser.add_argument("--src", type=Path, required=True, help="Source BIDS-like root.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"Output BIDS root (default: {DEFAULT_OUT}).")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing outputs.")
    parser.add_argument("--dry-run", action="store_true", help="Plan conversion without writing files.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = convert(src=args.src, out=args.out, overwrite=args.overwrite, dry_run=args.dry_run)
    CONSOLE.print(
        f"[green]Done.[/] planned={summary.planned_files} copied={summary.copied_files} "
        f"converted={summary.converted_niftis} skipped={summary.skipped_files}"
        + (" [dim](dry-run)[/]" if summary.dry_run else "")
    )
