"""Download and unpack the complete Khallaf 2026 fUSI archive from Edmond."""

import argparse
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

URL = "https://edmond.mpg.de/api/access/datafile/343674"
"""Original Edmond fUSI archive URL."""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "work",
        help="Parent directory for the downloaded khallaf-2026-bids tree.",
    )
    data_dir = parser.parse_args().data_dir.expanduser().resolve()
    destination = data_dir / "khallaf-2026-bids"
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

    with TemporaryDirectory(dir=data_dir) as directory, ZipFile(archive) as source:
        for name in source.namelist():
            if Path(name).is_absolute() or ".." in Path(name).parts:
                raise ValueError(f"Unsafe ZIP member path: {name!r}")
        source.extractall(directory)
        extracted = Path(directory) / "naked_mole_rat_fusi_dataset"
        if not extracted.is_dir():
            raise ValueError("Archive is missing naked_mole_rat_fusi_dataset/.")
        extracted.rename(destination)
    archive.unlink()
    print(destination)
