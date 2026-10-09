"""Run with the Huang recipe environment; no atlas download or file writes."""

import importlib
import sys
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "recipes/huang-2025-template"))
recipe = importlib.import_module("main")
expected_warning = (
    "Both sform_code and qform_code are 0 in the NIfTI header. "
    "Coordinates will be computed from the voxel dimensions only."
)
template = Mock()
template.dims = ("z", "y", "x")
atlas = Mock()
atlas.reference.coords = {}


def load(path):
    warnings.warn(expected_warning, UserWarning)
    warnings.warn("Unrelated input warning", UserWarning)
    return template


with (
    TemporaryDirectory() as directory,
    patch.object(recipe.cf.atlas.Atlas, "from_brainglobe", return_value=atlas),
    patch.object(recipe.cf, "load", side_effect=load),
    patch.object(recipe.cf, "save"),
    patch.object(recipe, "OUTPUTS", Path(directory)),
    patch.object(recipe, "OUTPUT_VASCULAR", Path(directory) / "template.nii.gz"),
):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        recipe.export_vascular()
        assert [str(w.message) for w in caught] == ["Unrelated input warning"]
        warnings.warn(expected_warning, UserWarning)
        assert str(caught[-1].message) == expected_warning

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        recipe.export_vascular(Path(directory) / "custom.nii")
        assert [str(w.message) for w in caught] == [
            expected_warning, "Unrelated input warning",
        ]

print("PASS: only the bundled Huang input's expected warning is suppressed")
