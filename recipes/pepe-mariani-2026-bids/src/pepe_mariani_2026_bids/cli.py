from __future__ import annotations

import argparse
import os
import tomllib
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from rich.console import Console

from .converter import convert

CONSOLE = Console()
RECIPE = Path(__file__).resolve().parents[2]
with (RECIPE / "pyproject.toml").open("rb") as source:
    VERSION = tomllib.load(source)["project"]["version"]
DEFAULT_OUT = RECIPE.parents[1] / "publish" / "datasets" / RECIPE.name / VERSION


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert Pepe and Mariani fUSI recordings to fUSI-BIDS.",
    )
    parser.add_argument("--src", type=Path, required=True, help="Source dataset root.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"Output BIDS root (default: {DEFAULT_OUT}).")
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing outputs."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Plan conversion without writing files."
    )
    return parser


def build_upload_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Upload the Pepe and Mariani fUSI-BIDS dataset to OSF and write "
            "dataset_index.json."
        ),
    )
    parser.add_argument(
        "--bids-dir", type=Path, help="Local BIDS root. Skipped with --index-only."
    )
    parser.add_argument(
        "--project", default=None, help="OSF project ID, or OSF_PROJECT env var."
    )
    parser.add_argument("--token", default=None, help="OSF token, or OSF_TOKEN env var.")
    parser.add_argument(
        "--index-only",
        action="store_true",
        help="Only regenerate/upload dataset_index.json.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = convert(
        src=args.src, out=args.out, overwrite=args.overwrite, dry_run=args.dry_run
    )
    CONSOLE.print(
        f"[green]Done.[/] planned={summary.planned_files} "
        f"copied={summary.copied_files} converted={summary.converted_niftis} "
        f"skipped={summary.skipped_files}"
        + (" [dim](dry-run)[/]" if summary.dry_run else "")
    )


def upload_main() -> None:
    from .upload import generate_index_with_retry, upload_dataset, upload_index

    load_dotenv()
    args = build_upload_parser().parse_args()
    token = args.token or os.environ.get("OSF_TOKEN")
    project = args.project or os.environ.get("OSF_PROJECT")
    if not token:
        CONSOLE.print("[bold red]Error:[/] pass --token or set OSF_TOKEN.")
        raise SystemExit(1)
    if not project:
        CONSOLE.print("[bold red]Error:[/] pass --project or set OSF_PROJECT.")
        raise SystemExit(1)

    CONSOLE.rule("[bold blue]OSF Upload Workflow")
    CONSOLE.print(f"[bold]Project[/]: [cyan]{project}[/]")

    index: dict[str, dict[str, Any]] | None = None
    if not args.index_only:
        if args.bids_dir is None:
            CONSOLE.print(
                "[bold red]Error:[/] --bids-dir is required unless --index-only is set."
            )
            raise SystemExit(1)
        CONSOLE.rule("[bold blue]Step 1/3: Upload Dataset Files")
        index = upload_dataset(args.bids_dir, token, project)

    CONSOLE.rule("[bold blue]Step 2/3: Build Dataset Index")
    if args.index_only or index is None:
        index = generate_index_with_retry(token, project)
    CONSOLE.print(f"[green]Index contains {len(index)} files.[/]")

    CONSOLE.rule("[bold blue]Step 3/3: Upload Dataset Index")
    upload_index(index, token, project)
    CONSOLE.rule("[bold green]Upload Finished")
