"""Stage Landemard BIDS data and update the legacy angio datatype to susi."""

import argparse
import csv
import json
import shutil
import tomllib
from pathlib import Path

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
        payload = json.loads(text, object_hook=_rewrite_references)
        if payload != json.loads(text):
            sidecar.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src", type=Path, help="Existing BIDS tree.")
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT,
        help=f"Output BIDS root (default: {DEFAULT_OUT}).",
    )
    args = parser.parse_args()
    destination = args.out.expanduser()
    shutil.copytree(args.src.expanduser(), destination)
    update_susi(destination)
    print(destination)
