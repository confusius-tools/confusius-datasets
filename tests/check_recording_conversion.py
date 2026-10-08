"""Check public recording converters against explicit NIfTI reference outputs.

Run with the selected recipe's locked environment, for example:
`uv run --locked --python 3.13 --directory recipes/pereira-2025-bids
python ../../tests/check_recording_conversion.py pereira-2025-bids`.
"""

import argparse
import importlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import nibabel as nib
import numpy as np

MODULES = {
    "pereira-2025-bids": "pereira_2025_bids.converter",
    "pepe-mariani-2026-bids": "pepe_mariani_2026_bids.converter",
    "cybis-pereira-2026-bids": "cybis_pereira_2026_bids.convert",
}
"""Installed recipe modules exposing the public `convert` function."""

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("recipe", choices=MODULES)
recipe = parser.parse_args().recipe
convert = importlib.import_module(MODULES[recipe]).convert

with TemporaryDirectory() as directory:
    src = Path(directory) / "source"
    out = Path(directory) / "converted"
    if recipe == "pereira-2025-bids":
        relative = Path("sub-test/ses-test/sub-test_ses-test_task-rest_pwd.nii.gz")
        destination = relative.parent / "fusi" / relative.name
        shape = (1, 3, 4, 2)
    elif recipe == "pepe-mariani-2026-bids":
        relative = Path(
            "rawdata/sub-test/ses-test/fusi/sub-test_ses-test_task-rest_pose-vol_pwd.nii.gz"
        )
        destination = Path(*relative.parts[1:]).with_name(
            relative.name.replace("_pose-vol", "")
        )
        shape = (2, 3, 4, 2)
    else:
        relative = Path("sub-test/ses-test/fus/sub-test_ses-test_task-rest_pwd.nii.gz")
        destination = Path(
            *("fusi" if part == "fus" else part for part in relative.parts)
        )
        shape = (2, 3, 4, 2)

    data = np.arange(np.prod(shape), dtype=np.float32).reshape(shape)
    affine = np.diag([0.1, 0.2, 0.3, 1.0])
    image = nib.Nifti1Image(data, affine)
    image.set_qform(affine, 1)
    image.set_sform(affine, 2)
    image.header.set_xyzt_units(
        "meter" if recipe == "cybis-pereira-2026-bids" else "mm", "sec"
    )
    source_file = src / relative
    source_file.parent.mkdir(parents=True)
    nib.save(image, source_file)
    original_bytes = source_file.read_bytes()
    sidecar = source_file.with_suffix("").with_suffix(".json")
    sidecar.write_text(json.dumps({"RepetitionTime": 1.0}))
    metadata = b"participant_id\nsub-test\n"
    (src / "participants.tsv").write_bytes(metadata)

    convert(src=src, out=out)
    result = nib.load(out / destination)
    expected = (
        data.transpose(2, 1, 0, 3)
        if recipe != "cybis-pereira-2026-bids"
        else data.transpose(0, 2, 1, 3)[:, ::-1]
    )
    np.testing.assert_array_equal(np.asanyarray(result.dataobj), expected)
    if recipe != "cybis-pereira-2026-bids":
        permutation = np.eye(4)[[2, 1, 0, 3]]
        expected_affine = affine @ permutation
        if recipe == "pepe-mariani-2026-bids":
            expected_affine = np.eye(4)[[0, 2, 1, 3]] @ expected_affine
        np.testing.assert_allclose(result.affine, expected_affine)
        assert int(result.header["qform_code"]) == 1
        assert int(result.header["sform_code"]) == 2
    assert result.header.get_xyzt_units()[0] == "mm"
    assert (out / "participants.tsv").read_bytes() == metadata
    assert source_file.read_bytes() == original_bytes
    output_sidecar = (out / destination).with_suffix("").with_suffix(".json")
    expected_repetition_time = 2.4 if recipe == "pepe-mariani-2026-bids" else 1.0
    assert (
        json.loads(output_sidecar.read_text())["RepetitionTime"]
        == expected_repetition_time
    )
    if recipe == "pepe-mariani-2026-bids":
        np.testing.assert_allclose(result.header.get_zooms()[3], 2.4)
    print(f"PASS: {recipe} values, layout, metadata, units, and source preservation")
