"""Mirror a BIDS tree and convert fUSI NIfTI files into canonical orientation.

Two phases:

1. Copy files under ``src`` to ``out``, updating legacy datatype paths and references.
2. Re-open every ``.nii`` / ``.nii.gz`` at ``out`` and apply the fUSI
   axis/coordinate transform in place.
"""

from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

import confusius as cf
import numpy as np
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Column

__all__ = ["ConversionSummary", "convert"]

console = Console()


@dataclass
class ConversionSummary:
    planned: int
    copied: int
    converted: int
    skipped: int
    dry_run: bool


def _is_nifti(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith(".nii") or name.endswith(".nii.gz")


def _discover(src: Path) -> list[Path]:
    return sorted(p for p in src.rglob("*") if p.is_file())


def _rewrite_path(rel: Path) -> Path:
    """Update legacy datatype folders and the ``_fus`` suffix."""
    if rel.parts and rel.parts[0] in ("sourcedata", "code"):
        return rel
    parts = ["susi" if p == "angio" and
             (i == 0 or rel.parts[i - 1].startswith(("sub-", "ses-"))) else
             "fusi" if p == "fus" else p for i, p in enumerate(rel.parts)]
    name = parts[-1]
    dot = name.find(".")
    stem = name if dot == -1 else name[:dot]
    exts = "" if dot == -1 else name[dot:]
    if stem.endswith("_fus"):
        stem = stem[:-4] + "_fusi"
    parts[-1] = stem + exts
    return Path(*parts)


def _rewrite_references(payload: dict) -> dict:
    for old, new in {
        "ProbeCentralFrequency": "ProbeCenterFrequency",
        "UltrasoundTransmitFrequency": "TransmitFrequency",
        "UltrasoundPulseRepetitionFrequency": "PulseRepetitionFrequency",
        "ProbeVoltage": "TransmitVoltage",
    }.items():
        if old in payload:
            payload[new] = payload.pop(old)
    payload.pop("PowerDopplerIntegrationStride", None)
    for key in ("IntendedFor", "Sources", "RawSources"):
        value = payload.get(key)
        if isinstance(value, str):
            payload[key] = _rewrite_path(Path(value)).as_posix()
        elif isinstance(value, list):
            payload[key] = [_rewrite_path(Path(path)).as_posix() for path in value]
    return payload


def _transform(pwd):
    """Permute voxels and preserve the source's distinct qform/sform scaling.

    >>> source = cf.create_voxeldata(np.arange(24).reshape(4, 2, 3), dims=("k", "j", "i"), spacing=(.001, .002, .003), origin=(0, 0, 0), attrs={"affines": {"world_to_qform": np.eye(4)}})
    >>> transformed = _transform(source)
    >>> np.array_equal(transformed, np.asarray(source).transpose(1, 0, 2)[:, ::-1, :])
    True
    """
    permutation = np.eye(4)
    permutation[:3, :3] = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
    permutation[0, 3] = pwd.sizes["k"] - 1
    world = np.eye(4)
    world[:3, :3] = [[0, 1000, 0], [-1000, 0, 0], [0, 0, 1000]]
    source_affines = pwd.attrs["affines"]
    voxel_to_world = pwd.fusi.affine.voxel_to_world
    qform = world @ source_affines["world_to_qform"] @ voxel_to_world @ permutation
    affines = {"world_to_qform": np.eye(4)}
    if "world_to_sform" in source_affines:
        world[:3] /= 1000
        sform = world @ source_affines["world_to_sform"] @ voxel_to_world @ permutation
        affines["world_to_sform"] = sform @ np.linalg.inv(qform)
    attrs = dict(pwd.attrs)
    attrs["affines"] = affines
    if attrs.get("clutter_filters") is not None:
        attrs["clutter_filters"] = ["svd:remove_first_60_components"]
    dims = ("time", "j", "k", "i") if "time" in pwd.dims else ("j", "k", "i")
    data = np.asarray(pwd.transpose(*dims).isel(k=slice(None, None, -1)))
    return cf.create_voxeldata(
        data,
        dims=("time", "k", "j", "i") if "time" in pwd.dims else ("k", "j", "i"),
        time=pwd.coords["time"] if "time" in pwd.dims else None,
        voxel_to_world=qform,
        attrs=attrs,
        name=pwd.name,
    )


def _progress_columns():
    return [
        SpinnerColumn(),
        TextColumn(
            "[progress.description]{task.description}",
            table_column=Column(max_width=32, no_wrap=True, overflow="ellipsis"),
        ),
        BarColumn(bar_width=None),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    ]


def convert(
    *,
    src: Path,
    out: Path,
    overwrite: bool = False,
    dry_run: bool = False,
) -> ConversionSummary:
    src = src.expanduser().resolve()
    out = out.expanduser().resolve()

    if not src.is_dir():
        raise NotADirectoryError(f"src is not a directory: {src}")

    for folder in src.rglob("angio"):
        if (folder.is_dir() and folder.parent.name.startswith(("sub-", "ses-"))
                and not {"sourcedata", "code"}.intersection(folder.relative_to(src).parts)
                and folder.with_name("susi").exists()):
            raise FileExistsError(f"Both angio and susi exist: {folder.parent}")
    files = _discover(src)
    planned = len(files)

    if planned == 0:
        console.print(f"[yellow]No files found under {src}.[/]")
        return ConversionSummary(
            planned=0, copied=0, converted=0, skipped=0, dry_run=dry_run
        )

    # Phase 1: mirror src -> out.
    copied = 0
    skipped = 0
    nifti_dests: list[Path] = []

    with Progress(*_progress_columns(), console=console) as progress:
        task = progress.add_task("Copying", total=planned)
        for path in files:
            rel = path.relative_to(src)
            rel_out = _rewrite_path(rel)
            dest = out / rel_out
            progress.update(task, description=f"Copying {rel_out}")

            if dest.exists() and not overwrite:
                skipped += 1
                if _is_nifti(dest):
                    # Already-present nifti — do not re-convert; leave as-is.
                    pass
                progress.advance(task)
                continue

            if dry_run:
                console.log(f"[dim]dry-run copy:[/] {rel} -> {rel_out}")
                copied += 1
                if _is_nifti(path):
                    nifti_dests.append(dest)
                progress.advance(task)
                continue

            dest.parent.mkdir(parents=True, exist_ok=True)
            if rel.parts[0] in ("sourcedata", "code"):
                shutil.copy2(path, dest)
            elif path.name.endswith("_scans.tsv"):
                with path.open(newline="") as source:
                    rows = list(csv.reader(source, delimiter="\t"))
                filename_column = rows[0].index("filename")
                for row in rows[1:]:
                    row[filename_column] = _rewrite_path(Path(row[filename_column])).as_posix()
                with dest.open("w", newline="") as output:
                    csv.writer(output, delimiter="\t", lineterminator="\n").writerows(rows)
                shutil.copystat(path, dest)
            elif path.suffix == ".json":
                payload = json.loads(path.read_text(), object_hook=_rewrite_references)
                dest.write_text(json.dumps(payload, indent=2) + "\n")
                shutil.copystat(path, dest)
            else:
                shutil.copy2(path, dest)
            copied += 1
            if _is_nifti(dest):
                nifti_dests.append(dest)
            progress.advance(task)

    # Phase 2: convert NIfTI files in place at the destination.
    converted = 0
    if nifti_dests:
        with Progress(*_progress_columns(), console=console) as progress:
            task = progress.add_task("Converting", total=len(nifti_dests))
            for dest in nifti_dests:
                rel = dest.relative_to(out)
                progress.update(task, description=f"Converting {rel}")

                if dry_run:
                    console.log(f"[dim]dry-run convert:[/] {rel}")
                    converted += 1
                    progress.advance(task)
                    continue

                pwd = cf.load(dest)
                pwd = _transform(pwd)
                cf.save(pwd, dest)
                converted += 1
                progress.advance(task)

    return ConversionSummary(
        planned=planned,
        copied=copied,
        converted=converted,
        skipped=skipped,
        dry_run=dry_run,
    )
