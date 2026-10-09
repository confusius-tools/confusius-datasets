from __future__ import annotations

import csv
import json
import re
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
FUSI_REPETITION_TIME = 2.4
CHUNK_DELAY_TIME = 2.0
VOLUME_DELAY_TIME = 0.2
CHUNK_SPACING = 1.0
CHUNK_THICKNESS = 0.4
_CHUNK_RE = re.compile(r"_(?:pose|chunk)-(\d+)_")


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
    parts = rel.parts[1:] if rel.parts and rel.parts[0] == "rawdata" else rel.parts
    dest = Path(*("susi" if part == "angio" and
                   (i == 0 or parts[i - 1].startswith(("sub-", "ses-"))) else part
                   for i, part in enumerate(parts)))
    name = dest.name.replace("_pose-vol", "").replace("_chunk-vol", "")
    return dest.with_name(name.replace("_pose-", "_chunk-"))


def _permutation(order: list[int]) -> np.ndarray:
    p = np.eye(4)
    p[:3, :3] = 0
    for new_axis, old_axis in enumerate(order):
        p[old_axis, new_axis] = 1
    return p


def _world_transform() -> np.ndarray:
    s = np.eye(4)
    s[:3, :3] = [[1, 0, 0], [0, 0, 1], [0, 1, 0]]
    return s


def _is_fusi_recording(rel: Path) -> bool:
    name = rel.name
    return "task-" in name and "_pwd" in name and not {"angio", "susi"}.intersection(rel.parts)


def _chunk_index(rel: Path) -> int | None:
    match = _CHUNK_RE.search(rel.name)
    return int(match.group(1)) if match else None


def _chunk_group(rel: Path) -> Path:
    return rel.with_name(_CHUNK_RE.sub("_chunk-X_", rel.name))


def _needs_chunk_delay_time(rel: Path) -> bool:
    return _chunk_index(rel) is not None and (
        rel.parts[0] == "rawdata"
        or (len(rel.parts) > 1 and rel.parts[:2] == ("derivatives", "registered"))
    )


def _needs_volume_delay_time(rel: Path) -> bool:
    return (
        len(rel.parts) > 1
        and rel.parts[:2] == ("derivatives", "preprocessed")
        and ("_pose-vol_" in rel.name or "_chunk-vol_" in rel.name)
    )


def _chunk_base_x(files: list[Path], src: Path) -> dict[Path, float]:
    groups: dict[Path, list[tuple[int, float]]] = {}
    for path in files:
        rel = path.relative_to(src)
        chunk = _chunk_index(rel)
        if chunk is None or not _is_fusi_recording(rel):
            continue
        img = cast(nib.Nifti1Image, nib.load(path))
        if len(img.shape) == 4 and img.shape[0] == 1:
            groups.setdefault(_chunk_group(rel), []).append((chunk, float(img.affine[0, 3])))
    return {group: min(values)[1] for group, values in groups.items()}


def _convert_nifti(src: Path, dest: Path, rel: Path, chunk_base_x: float | None) -> None:
    img = cast(nib.Nifti1Image, nib.load(src))
    shape = img.shape
    if len(shape) not in (3, 4):
        raise ValueError(f"Expected 3D or 4D NIfTI, got {shape}: {src}")

    order = [2, 1, 0]
    data = np.asanyarray(img.dataobj).transpose(*order, *range(3, len(shape)))
    affine = _world_transform() @ img.affine @ _permutation(order)

    header = img.header.copy()
    header.set_data_shape(data.shape)
    header.set_xyzt_units("mm", "sec" if len(shape) == 4 else "unknown")
    if len(shape) == 4 and _is_fusi_recording(rel):
        zooms = list(header.get_zooms())
        zooms[3] = FUSI_REPETITION_TIME
        chunk = _chunk_index(rel)
        if shape[0] == 1 and chunk is not None:
            zooms[2] = CHUNK_THICKNESS
            affine[:, 2] = 0
            affine[2, 2] = -CHUNK_THICKNESS
            if chunk_base_x is not None:
                delta = float(img.affine[0, 3]) - chunk_base_x
                affine[0, 3] = chunk_base_x
                affine[2, 3] += delta * 1000 if abs(delta) < 0.01 else delta
            else:
                affine[2, 3] -= chunk * CHUNK_SPACING
        header.set_zooms(zooms)
    out = nib.Nifti1Image(data, affine, header)
    out.set_qform(affine, int(img.header["qform_code"]))
    out.set_sform(affine, int(img.header["sform_code"]))
    nib.save(out, dest)


def _normalize_pwd_sidecar(payload: dict) -> dict:
    renames = {
        "ProbeElevationWidth": "ProbeFocalWidth",
        "ProbeElevationAperture": "ProbeAperture",
        "ProbeElevationFocus": "ProbeFocalDepth",
        "PlaneWaveElevationAngles": "PlaneWaveAngles",
        "UltrafastSamplingFrequency": "CompoundSamplingFrequency",
    }
    for old, new in renames.items():
        if old in payload:
            payload[new] = payload.pop(old)

    filters = payload.get("ClutterFilters")
    if isinstance(filters, list):
        values = []
        for item in filters:
            if isinstance(item, str):
                values.append(item)
            elif isinstance(item, dict) and item.get("FilterType") == "Fixed-threshold SVD":
                low = item.get("LowThreshold")
                high = item.get("HighThreshold")
                values.append(f"Fixed-threshold SVD [{low}-{high}]")
        payload["ClutterFilters"] = values
    return payload


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
            payload[key] = _dest_rel(Path(value)).as_posix()
        elif isinstance(value, list):
            payload[key] = [_dest_rel(Path(path)).as_posix() for path in value]
    return payload


def _copy_metadata(src: Path, dest: Path, rel: Path) -> None:
    """Normalize legacy scan headers and resolve omitted datatype folders.

    >>> from tempfile import TemporaryDirectory
    >>> with TemporaryDirectory() as directory:
    ...     root = Path(directory)
    ...     (root / "fusi").mkdir()
    ...     _ = (root / "fusi/sub-x_pose-0_pwd.nii.gz").write_bytes(b"")
    ...     source = root / "sub-x_scans.tsv"
    ...     _ = source.write_text("scan_id\\tacq_time\\nsub-x_pose-0_pwd.nii.gz\\t2023-01-01\\nsub-x_pose-0_pwd.nii.gz 2023-01-01T12:00:00\\t\\n")
    ...     output = root / "out/sub-x_scans.tsv"
    ...     _copy_metadata(source, output, Path(source.name))
    ...     print([line.split() for line in output.read_text().splitlines()])
    [['filename', 'acq_time'], ['fusi/sub-x_chunk-0_pwd.nii.gz', '2023-01-01'], ['fusi/sub-x_chunk-0_pwd.nii.gz', '2023-01-01T12:00:00']]
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    if rel.parts[0] in ("sourcedata", "code"):
        shutil.copy2(src, dest)
        return
    if rel.name.endswith("_scans.tsv"):
        with src.open(newline="") as source:
            rows = list(csv.reader(source, delimiter="\t"))
        filename_column = rows[0].index("filename" if "filename" in rows[0] else "scan_id")
        legacy_header = rows[0][filename_column] == "scan_id"
        rows[0][filename_column] = "filename"
        for row in rows[1:]:
            if (legacy_header and rows[0] == ["filename", "acq_time"]
                    and len(row) in {1, 2} and (len(row) == 1 or not row[1])):
                # Some source rows put the timestamp in the filename cell.
                match = re.fullmatch(
                    r"(\S+\.nii(?:\.gz)?) (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", row[0]
                )
                if match:
                    row[:] = match.groups()
            reference = Path(row[filename_column])
            if legacy_header and len(reference.parts) == 1:
                matches = [path for path in src.parent.rglob(reference.name) if path.is_file()]
                if not matches:
                    # shortcut: retain sidecar-only scan references; reconcile missing images before publication.
                    stem = reference.with_suffix("") if reference.suffix == ".gz" else reference
                    matches = [path for path in src.parent.rglob(stem.with_suffix(".json").name) if path.is_file()]
                if len(matches) != 1:
                    raise ValueError(f"Expected one scan or sidecar matching {reference} in {src.parent}, found {len(matches)}")
                reference = matches[0].parent.relative_to(src.parent) / reference.name
            row[filename_column] = _dest_rel(reference).as_posix()
        with dest.open("w", newline="") as output:
            csv.writer(output, delimiter="\t", lineterminator="\n").writerows(rows)
        shutil.copystat(src, dest)
        return
    if rel == Path("dataset_description.json"):
        text = src.read_text()
        # Original file has one trailing comma; normalize JSON so the BIDS root
        # is valid without otherwise changing values.
        payload = json.loads(text.replace("\n    },\n  ]", "\n    }\n  ]"),
                             object_hook=_rewrite_references)
        dest.write_text(json.dumps(payload, indent=2) + "\n")
        shutil.copystat(src, dest)
        return
    if rel == Path("pwd.json"):
        payload = _normalize_pwd_sidecar(json.loads(src.read_text(), object_hook=_rewrite_references))
        dest.write_text(json.dumps(payload, indent=2) + "\n")
        shutil.copystat(src, dest)
        return
    if rel.suffix == ".json" and _is_fusi_recording(rel):
        payload = json.loads(src.read_text(), object_hook=_rewrite_references)
        payload["RepetitionTime"] = FUSI_REPETITION_TIME
        if _needs_chunk_delay_time(rel):
            payload["DelayTime"] = CHUNK_DELAY_TIME
        elif _needs_volume_delay_time(rel):
            payload["DelayTime"] = VOLUME_DELAY_TIME
        dest.write_text(json.dumps(payload, indent=2) + "\n")
        shutil.copystat(src, dest)
        return
    if rel.suffix == ".json":
        payload = json.loads(src.read_text(), object_hook=_rewrite_references)
        dest.write_text(json.dumps(payload, indent=2) + "\n")
        shutil.copystat(src, dest)
        return
    shutil.copy2(src, dest)


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
    chunk_base_x = _chunk_base_x([p for p in files if _is_nifti(p)], src)
    niftis: list[tuple[Path, Path]] = []
    copied = skipped = 0

    with Progress(*_progress_columns(), console=CONSOLE) as progress:
        task = progress.add_task("Copying metadata", total=len(files))
        for path in files:
            rel = path.relative_to(src)
            dest = out / _dest_rel(rel)
            progress.update(task, description=f"Planning {dest.name}")

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
                _copy_metadata(path, dest, rel)
            else:
                CONSOLE.log(f"[dim]dry-run copy:[/] {rel} -> {dest.relative_to(out)}")
            progress.advance(task)

    converted = 0
    if niftis:
        with Progress(*_progress_columns(), console=CONSOLE) as progress:
            task = progress.add_task("Converting NIfTIs", total=len(niftis))
            for path, dest in niftis:
                progress.update(task, description=f"Converting {dest.name}")
                converted += 1
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    rel_src = path.relative_to(src)
                    _convert_nifti(path, dest, rel_src, chunk_base_x.get(_chunk_group(rel_src)))
                progress.advance(task)

    return ConversionSummary(
        planned_files=len(files),
        copied_files=copied,
        converted_niftis=converted,
        skipped_files=skipped,
        dry_run=dry_run,
    )
