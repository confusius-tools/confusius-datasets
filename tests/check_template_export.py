"""Check public template exporters in their own locked environments.

Run from the repository root with the selected recipe environment:
`uv run --locked --python 3.13 --directory recipes/huang-2025-template
python ../../tests/check_template_export.py huang-2025-template`.
"""

import argparse
import hashlib
import importlib
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import confusius as cf
import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "recipe", choices=("huang-2025-template", "pepe-mariani-2026-template")
)
name = parser.parse_args().recipe
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "recipes" / name))
recipe = importlib.import_module("main")

with TemporaryDirectory() as directory:
    destination = Path(directory)
    if name == "huang-2025-template":
        source_path = recipe.SOURCE_VASCULAR
        recipe.OUTPUTS = destination
        recipe.OUTPUT_VASCULAR = (
            destination / "huang-2025-space-allen50_desc-vascular.nii.gz"
        )
        export = recipe.export_vascular
        permutation = (1, 2, 0)
    else:
        source_path = recipe.FUSI_PATH
        recipe.OUTPUTS_ROOT = destination
        recipe.OUTPUT_TEMPLATE_PATH = (
            destination / "pepe-mariani-2026-fusi-template.nii.gz"
        )
        export = recipe.export_template
        permutation = (2, 1, 0)

    original_hash = hashlib.sha256(source_path.read_bytes()).digest()
    source = cf.load(source_path)
    if "time" in source.dims:
        source = source.squeeze("time", drop=True)
    output = export()
    assert output.parent == destination
    loaded = cf.load(output)
    np.testing.assert_allclose(
        np.asarray(loaded), np.asarray(source).transpose(permutation)
    )
    assert hashlib.sha256(source_path.read_bytes()).digest() == original_hash
    if name == "huang-2025-template":
        atlas = cf.atlas.Atlas.from_brainglobe("allen_mouse_50um")
        for axis in ("z", "y", "x"):
            np.testing.assert_allclose(
                loaded.coords[axis], atlas.reference.coords[axis]
            )
    print(f"PASS: {name} voxel permutation, NIfTI round trip, and source preservation")
