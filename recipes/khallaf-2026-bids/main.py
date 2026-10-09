"""Download Khallaf 2026 and update the legacy angio datatype to susi."""

import argparse
import csv
import json
import subprocess
import tomllib
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

URL = "https://edmond.mpg.de/api/access/datafile/343674"
"""Original Edmond fUSI archive URL."""

ROOT = Path(__file__).resolve().parent
with (ROOT / "pyproject.toml").open("rb") as source:
    VERSION = tomllib.load(source)["project"]["version"]
DEFAULT_OUT = ROOT.parents[1] / "publish" / "datasets" / ROOT.name / VERSION

def _susi_reference(path: str) -> str:
    parts = path.split("/")
    if parts[0] in ("sourcedata", "code"):
        return path
    return "/".join("susi" if p == "angio" and
                    (i == 0 or parts[i - 1].startswith(("sub-", "ses-"))) else p
                    for i, p in enumerate(parts))


def _rewrite_references(payload: dict) -> dict:
    for key in ("IntendedFor", "Sources", "RawSources"):
        value = payload.get(key)
        if isinstance(value, str):
            payload[key] = _susi_reference(value)
        elif isinstance(value, list):
            payload[key] = [_susi_reference(path) for path in value]
    return payload


def update_susi(root: Path) -> None:
    folders = [p for p in root.rglob("angio") if p.is_dir()
               and p.parent.name.startswith(("sub-", "ses-"))
               and not {"sourcedata", "code"}.intersection(p.relative_to(root).parts)]
    for folder in folders:
        if folder.with_name("susi").exists():
            raise FileExistsError(f"Both angio and susi exist: {folder.parent}")
    for folder in folders:
        folder.rename(folder.with_name("susi"))
    for scans in root.rglob("*_scans.tsv"):
        if {"sourcedata", "code"}.intersection(scans.relative_to(root).parts):
            continue
        with scans.open(newline="") as source:
            rows = list(csv.reader(source, delimiter="\t"))
        column = rows[0].index("filename")
        changed = False
        for row in rows[1:]:
            old = row[column]
            row[column] = _susi_reference(old)
            changed |= row[column] != old
        if changed:
            with scans.open("w", newline="") as output:
                csv.writer(output, delimiter="\t", lineterminator="\n").writerows(rows)
    for sidecar in root.rglob("*.json"):
        if {"sourcedata", "code"}.intersection(sidecar.relative_to(root).parts):
            continue
        text = sidecar.read_text()
        if "angio/" not in text:
            continue
        payload = json.loads(text, object_hook=_rewrite_references)
        if payload != json.loads(text):
            sidecar.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "work",
        help="Download cache directory (not release output).",
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT,
        help=f"Output dataset directory (default: {DEFAULT_OUT}).",
    )
    args = parser.parse_args()
    data_dir = args.data_dir.expanduser().resolve()
    destination = args.out.expanduser().resolve()
    if destination.exists():
        raise FileExistsError(f"Use a fresh destination: {destination}")
    data_dir.mkdir(parents=True, exist_ok=True)
    archive = data_dir / "khallaf-2026.zip"
    if not archive.exists():
        part = archive.with_suffix(".zip.part")
        subprocess.run(
            [
                "curl",
                "--fail",
                "--location",
                "--retry",
                "3",
                "--continue-at",
                "-",
                "--output",
                str(part),
                URL,
            ],
            check=True,
        )
        part.replace(archive)

    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent) as directory, ZipFile(archive) as source:
        for name in source.namelist():
            if Path(name).is_absolute() or ".." in Path(name).parts:
                raise ValueError(f"Unsafe ZIP member path: {name!r}")
        source.extractall(directory)
        extracted = Path(directory) / "naked_mole_rat_fusi_dataset"
        if not extracted.is_dir():
            raise ValueError("Archive is missing naked_mole_rat_fusi_dataset/.")
        update_susi(extracted)
        extracted.rename(destination)
    archive.unlink()
    print(destination)
