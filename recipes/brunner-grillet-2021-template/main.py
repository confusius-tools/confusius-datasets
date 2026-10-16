from __future__ import annotations

import tomllib
from pathlib import Path

import confusius as cf
import numpy as np
import pooch
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parent
with (ROOT / "pyproject.toml").open("rb") as source:
    VERSION = tomllib.load(source)["project"]["version"]
OUTPUTS = ROOT.parents[1] / "publish" / "templates" / ROOT.name / VERSION
CACHE = ROOT.parents[1] / "work" / ROOT.name

SOURCE_URL = "https://zenodo.org/records/4905862/files/allen_brain_atlas.mat?download=1"
SOURCE_HASH = "md5:ea1d5f60589350487a5aa574b6c954f0"
OUTPUT_VASCULAR = OUTPUTS / "brunner-grillet-2021-fusi-template.nii.gz"


def export_vascular(source_path: Path | None = None) -> Path:
    if source_path is None:
        source_path = Path(pooch.retrieve(
            url=SOURCE_URL,
            known_hash=SOURCE_HASH,
            fname="allen_brain_atlas.mat",
            path=CACHE,
        ))
    source = loadmat(source_path, simplify_cells=True)["atlas"]
    if source["Direction"] != "DV.AP.LR":
        raise ValueError(f"Unexpected atlas direction: {source['Direction']!r}")
    if not np.array_equal(source["VoxelSize"], [50, 50, 50]):
        raise ValueError(f"Unexpected atlas voxel size: {source['VoxelSize']!r}")

    # The MAT has no world affine; reorder DV/AP/LR to the Allen AP/DV/LR grid.
    data = source["Vascular"].transpose(1, 0, 2)
    atlas = cf.datasets.fetch_brainglobe_atlas("allen_mouse_50um")
    reference = atlas["reference"]
    if data.shape != reference.shape:
        raise ValueError(f"Template shape {data.shape} differs from Allen grid {reference.shape}")
    transformed = cf.create_voxeldata(
        data, dims=("k", "j", "i"),
        voxel_to_world=reference.fusi.affine.voxel_to_world,
        units=reference.fusi.affine.units,
    )

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    cf.save(transformed, OUTPUT_VASCULAR)
    return OUTPUT_VASCULAR


def main() -> None:
    out = export_vascular()
    loaded = cf.load(out)
    print(out)
    print(f"dims={loaded.dims} shape={loaded.shape}")


if __name__ == "__main__":
    main()
