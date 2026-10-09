"""Run in the Nunez recipe environment; convert one synthetic irregular run."""

import json
import sys
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import confusius as cf
import h5py
import nibabel as nib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "recipes/nunez-elizalde-2022-bids/src"))
from nunez_elizalde_2022_bids import converter

save = cf.save


def save_with_unrelated_warning(*args, **kwargs):
    save(*args, **kwargs)
    warnings.warn("Unrelated save warning", UserWarning)


with TemporaryDirectory() as directory:
    root = Path(directory)
    times = np.array([11.01, 11.31, 11.701, 12.001])
    source = root / "source.h5"
    with h5py.File(source, "w") as h5:
        h5["times"] = times
        h5["data"] = np.arange(24, dtype=np.float32).reshape(4, 2, 3)
    plan = converter.RunPlan(
        subject="test", date="2020-01-01", block=1, task="spontaneous",
        task_description="Test", slice_index=0, run_number=None,
        slice_position_mm=0.0, source_hdf=source,
        reference_nifti=root / "reference.nii.gz", output_nifti=root / "test_pwd.nii.gz",
    )
    metadata = SimpleNamespace(
        slice_positions_mm=[0.0, 1.0], depth_mm=None, transmit_frequency_hz=None,
        compound_sampling_frequency_hz=None, plane_wave_angles_deg=None,
        probe_voltage_v=None,
    )
    with (
        patch.object(converter, "_load_reference_axes", return_value=(np.arange(3) * 0.1, np.arange(2) * 0.1)),
        patch.object(converter, "_load_events_for_run", return_value=(None, {})),
        patch.object(cf, "save", side_effect=save_with_unrelated_warning),
        warnings.catch_warnings(record=True) as caught,
    ):
        warnings.simplefilter("always")
        result = converter._convert_run(plan, metadata=metadata, overwrite=False)
        assert result["status"] == "converted"
        assert [str(w.message) for w in caught] == ["Unrelated save warning"]
        warnings.warn("Coordinate 'time' has non-uniform sampling. Exact timings are saved in the JSON sidecar as VolumeTiming,", UserWarning)
        assert len(caught) == 2
    sidecar = json.loads((root / "test_pwd.json").read_text())
    np.testing.assert_array_equal(sidecar["VolumeTiming"], times)
    assert "RepetitionTime" not in sidecar
    image = nib.load(plan.output_nifti)
    assert image.shape[-1] == len(times)
    assert float(image.header["pixdim"][4]) == 0.0

print("PASS: irregular timings preserved; only the expected save warning is suppressed")
