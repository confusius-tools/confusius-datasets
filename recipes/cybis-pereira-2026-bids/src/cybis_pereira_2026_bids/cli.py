"""CLI entry point for converting the Cybis Pereira BIDS dataset."""

from __future__ import annotations

import argparse
import logging
import sys
import tomllib
from pathlib import Path

from rich.console import Console

from .convert import convert as _convert

console = Console()
RECIPE = Path(__file__).resolve().parents[2]
with (RECIPE / "pyproject.toml").open("rb") as source:
    VERSION = tomllib.load(source)["project"]["version"]
DEFAULT_OUT = RECIPE.parents[1] / "publish" / "datasets" / RECIPE.name / VERSION


def _build_convert_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cybis-convert",
        description="Convert fUSI NIfTI files into BIDS orientation.",
    )
    p.add_argument(
        "--src",
        type=Path,
        required=True,
        help="Source BIDS root to walk for .nii/.nii.gz files",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Target BIDS root (default: {DEFAULT_OUT}; same relative paths as --src)",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files (default: skip)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="List planned conversions without writing anything",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return p


def convert_main(argv: list[str] | None = None) -> None:
    args = _build_convert_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    src = args.src.expanduser().resolve()
    if not src.is_dir():
        console.print(f"[red]Error:[/] {src} is not a directory.", style="bold")
        sys.exit(1)

    console.print(
        f"Converting [cyan]{src}[/] -> [cyan]{args.out}[/]"
        + (" [dim](dry-run)[/]" if args.dry_run else "")
    )

    summary = _convert(
        src=src,
        out=args.out,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
    )

    console.print(
        f"[green]Done.[/] planned={summary.planned} "
        f"copied={summary.copied} converted={summary.converted} "
        f"skipped={summary.skipped}" + (" [dim](dry-run)[/]" if summary.dry_run else "")
    )
