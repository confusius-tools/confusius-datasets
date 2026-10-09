from __future__ import annotations

import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import nibabel as nib
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

CONSOLE = Console()


@dataclass
class ConversionSummary:
    planned_files: int
    copied_files: int
    converted_niftis: int
    skipped_files: int
    dry_run: bool


def _is_nifti(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith((".nii", ".nii.gz"))


def _dest_rel(rel: Path) -> Path:
    if rel.parts and rel.parts[0] in ("sourcedata", "code"):
        return rel
    rel = Path(*("susi" if p == "angio" and
                 (i == 0 or rel.parts[i - 1].startswith(("sub-", "ses-"))) else p
                 for i, p in enumerate(rel.parts)))
    if (
        len(rel.parts) == 3
        and rel.parts[0].startswith("sub-")
        and rel.parts[1].startswith("ses-")
        and not rel.name.endswith(("_scans.tsv", "_scans.json"))
    ):
        return Path(rel.parts[0], rel.parts[1], "fusi", rel.parts[2])
    return rel


def _rewrite_references(payload: dict) -> dict:
    for key in ("IntendedFor", "Sources", "RawSources"):
        value = payload.get(key)
        if isinstance(value, str):
            payload[key] = _dest_rel(Path(value)).as_posix()
        elif isinstance(value, list):
            payload[key] = [_dest_rel(Path(path)).as_posix() for path in value]
    return payload


def _permutation(order: list[int]) -> np.ndarray:
    p = np.eye(4)
    p[:3, :3] = 0
    for new_axis, old_axis in enumerate(order):
        p[old_axis, new_axis] = 1
    return p


def _convert_nifti_2d(src: Path, dest: Path) -> None:
    img = cast(nib.Nifti1Image, nib.load(src))
    shape = img.shape
    if len(shape) != 4:
        raise ValueError(f"Expected 4D 2D+t NIfTI, got {shape}: {src}")

    singletons = [axis for axis, size in enumerate(shape[:3]) if size == 1]
    if not singletons:
        raise ValueError(f"2D+t fUSI run has no singleton spatial axis: {shape}: {src}")

    # ConfUSIus reads NIfTI spatial axes as x, y, z, so put the singleton slice
    # dimension last in voxel order. Current Pereira files are (z=1, y, x, t),
    # hence the usual order is (old x, old y, old z, time) == (2, 1, 0, 3).
    order = [axis for axis in (2, 1, 0) if axis != singletons[0]] + [singletons[0]]
    data = np.asanyarray(img.dataobj).transpose(*order, 3)
    affine = img.affine @ _permutation(order)

    header = img.header.copy()
    header.set_data_shape(data.shape)
    out = nib.Nifti1Image(data, affine, header)
    out.set_qform(affine, int(img.header["qform_code"]))
    out.set_sform(affine, int(img.header["sform_code"]))
    nib.save(out, dest)


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
    *, src: Path, out: Path, overwrite: bool = False, dry_run: bool = False
) -> ConversionSummary:
    src = src.expanduser().resolve()
    out = out.expanduser().resolve()
    if not src.is_dir():
        raise NotADirectoryError(src)

    for folder in src.rglob("angio"):
        if (folder.is_dir() and folder.parent.name.startswith(("sub-", "ses-"))
                and not {"sourcedata", "code"}.intersection(folder.relative_to(src).parts)
                and folder.with_name("susi").exists()):
            raise FileExistsError(f"Both angio and susi exist: {folder.parent}")
    files = sorted(p for p in src.rglob("*") if p.is_file())
    niftis: list[tuple[Path, Path]] = []
    copied = skipped = 0

    with Progress(*_progress_columns(), console=CONSOLE) as progress:
        task = progress.add_task("Copying metadata", total=len(files))
        for path in files:
            rel = path.relative_to(src)
            dest = out / _dest_rel(rel)
            progress.update(task, description=f"Planning {dest.relative_to(out)}")

            if dest.exists() and not overwrite:
                skipped += 1
                progress.advance(task)
                continue

            if _is_nifti(path):
                niftis.append((path, dest))
                if dry_run:
                    CONSOLE.log(
                        f"[dim]dry-run convert:[/] {rel} -> {dest.relative_to(out)}"
                    )
                progress.advance(task)
                continue

            copied += 1
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                if rel.parts[0] in ("sourcedata", "code"):
                    shutil.copy2(path, dest)
                elif path.name.endswith("_scans.tsv"):
                    with path.open(newline="") as source:
                        rows = list(csv.reader(source, delimiter="\t"))
                    filename_column = rows[0].index("filename")
                    for row in rows[1:]:
                        filename = row[filename_column]
                        row[filename_column] = _dest_rel(Path(filename)).as_posix()
                    with dest.open("w", newline="") as output:
                        csv.writer(output, delimiter="\t", lineterminator="\n").writerows(rows)
                    shutil.copystat(path, dest)
                elif path.suffix == ".json" and "angio/" in path.read_text():
                    payload = json.loads(path.read_text(), object_hook=_rewrite_references)
                    dest.write_text(json.dumps(payload, indent=2) + "\n")
                    shutil.copystat(path, dest)
                else:
                    shutil.copy2(path, dest)
            else:
                CONSOLE.log(f"[dim]dry-run copy:[/] {rel} -> {dest.relative_to(out)}")
            progress.advance(task)

    converted = 0
    if niftis:
        with Progress(*_progress_columns(), console=CONSOLE) as progress:
            task = progress.add_task("Converting NIfTIs", total=len(niftis))
            for path, dest in niftis:
                rel = dest.relative_to(out)
                progress.update(task, description=f"Converting {rel}")
                converted += 1
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    _convert_nifti_2d(path, dest)
                progress.advance(task)

    return ConversionSummary(
        planned_files=len(files),
        copied_files=copied,
        converted_niftis=converted,
        skipped_files=skipped,
        dry_run=dry_run,
    )
