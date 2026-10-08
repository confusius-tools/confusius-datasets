from pathlib import Path

import numpy as np

from pereira_2025_bids.converter import _dest_rel, _permutation


def test_dest_rel_adds_fusi_datatype():
    rel = Path("sub-r1/ses-a/sub-r1_ses-a_task-rest_pwd.nii.gz")
    assert _dest_rel(rel) == Path("sub-r1/ses-a/fusi/sub-r1_ses-a_task-rest_pwd.nii.gz")


def test_permutation_maps_new_voxels_to_old_voxels():
    old_affine = np.diag([1, 2, 3, 1])
    new_affine = old_affine @ _permutation([2, 1, 0])
    np.testing.assert_array_equal(
        new_affine,
        np.array([[0, 0, 1, 0], [0, 2, 0, 0], [3, 0, 0, 0], [0, 0, 0, 1]]),
    )


if __name__ == "__main__":
    test_dest_rel_adds_fusi_datatype()
    test_permutation_maps_new_voxels_to_old_voxels()
