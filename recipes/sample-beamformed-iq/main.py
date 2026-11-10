"""Stage the Landemard 2026 sample beamformed IQ Zarr store."""

import argparse
import json
import shutil
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
NAME = "sub-ALD019_task-awake_acq-ref25_iq.zarr"
with (ROOT / "pyproject.toml").open("rb") as source:
    VERSION = tomllib.load(source)["project"]["version"]
DEFAULT_SRC = REPO / "work" / ROOT.name / NAME
DEFAULT_OUT = REPO / "publish" / "datasets" / ROOT.name / VERSION


def stage(src: Path, out: Path) -> None:
    if out.resolve().is_relative_to(src.resolve()):
        raise ValueError("Release directory must be outside the input store")
    metadata = json.loads((src / "zarr.json").read_text())
    if metadata.get("zarr_format") != 3 or metadata.get("node_type") != "group":
        raise ValueError(f"Expected a Zarr v3 group: {src}")
    if src.is_symlink() or any(path.is_symlink() for path in src.rglob("*")):
        raise ValueError(f"Zarr store contains a symlink: {src}")
    out.mkdir(parents=True, exist_ok=False)
    shutil.copytree(src, out / NAME)
    shutil.copy2(ROOT / "DATA_README.md", out / "README.md")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "src", type=Path, nargs="?", default=DEFAULT_SRC,
        help=f"Input Zarr store (default: {DEFAULT_SRC}).",
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT,
        help=f"Output dataset directory (default: {DEFAULT_OUT}).",
    )
    args = parser.parse_args()
    stage(args.src.expanduser(), args.out.expanduser())
    print(args.out)
