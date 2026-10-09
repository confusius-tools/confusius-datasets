import json
import tempfile
import warnings
from pathlib import Path
from unittest.mock import patch

import confusius as cf
import nibabel as nib
import numpy as np

from cybis_pereira_2026_bids.convert import _rewrite_references, convert


def test_clutter_filters_normalized_before_loading():
    payload = {"ClutterFilters": [{"FilterType": "Fixed-threshold SVD", "Threshold": 60}]}
    assert _rewrite_references(payload)["ClutterFilters"] == [
        "svd:remove_first_60_components"
    ]


def test_other_clutter_filters_preserved():
    for filters in (
        ["already_valid"],
        [{"FilterType": "Fixed-threshold SVD", "Threshold": 30}],
    ):
        assert _rewrite_references({"ClutterFilters": filters})["ClutterFilters"] == filters


def test_conversion_preserves_irregular_timing_and_other_warnings():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        src = root / "source"
        folder = src / "sub-rat84" / "ses-20220705" / "fus"
        folder.mkdir(parents=True)
        stem = "sub-rat84_ses-20220705_task-openfield_pwd"
        data = np.arange(48, dtype=np.float32).reshape(3, 2, 2, 4)
        image = nib.Nifti1Image(data, np.diag([0.001, 0.002, 0.003, 1]))
        image.set_qform(image.affine, code=1)
        image.header.set_xyzt_units("meter", "sec")
        nib.save(image, folder / f"{stem}.nii.gz")
        times = [0.4, 0.8, 1.200025, 1.600025]
        (folder / f"{stem}.json").write_text(json.dumps({
            "ClutterFilters": [{"FilterType": "Fixed-threshold SVD", "Threshold": 60}],
            "VolumeTiming": times,
            "FrameAcquisitionDuration": 0.2,
        }))
        save = cf.save

        def save_with_warning(*args, **kwargs):
            warnings.warn("unrelated warning", UserWarning)
            return save(*args, **kwargs)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with patch("cybis_pereira_2026_bids.convert.cf.save", save_with_warning):
                summary = convert(src=src, out=root / "output")
        assert [str(w.message) for w in caught] == ["unrelated warning"]
        assert summary.converted == 1
        output = root / "output" / "sub-rat84" / "ses-20220705" / "fusi"
        sidecar = json.loads((output / f"{stem}.json").read_text())
        assert sidecar["ClutterFilters"] == ["svd:remove_first_60_components"]
        np.testing.assert_allclose(sidecar["VolumeTiming"], times, rtol=0, atol=1e-12)
        result = nib.load(output / f"{stem}.nii.gz")
        assert result.header["pixdim"][4] == 0.0
        np.testing.assert_array_equal(np.sort(result.get_fdata().ravel()), data.ravel())
        original = json.loads((folder / f"{stem}.json").read_text())
        assert original["ClutterFilters"] == [
            {"FilterType": "Fixed-threshold SVD", "Threshold": 60}
        ]
        assert original["VolumeTiming"] == times
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            cf.load(output / f"{stem}.nii.gz")


if __name__ == "__main__":
    test_clutter_filters_normalized_before_loading()
    test_other_clutter_filters_preserved()
    test_conversion_preserves_irregular_timing_and_other_warnings()
