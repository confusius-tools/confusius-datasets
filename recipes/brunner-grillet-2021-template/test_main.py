from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import confusius as cf
import numpy as np
from scipy.io import savemat

import main


class ExportVascularTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source_path = self.root / "atlas.mat"
        self.output = self.root / "output" / main.OUTPUT_VASCULAR.name
        self.vascular = np.arange(24, dtype=np.float32).reshape(2, 3, 4) / 24
        self.source = {
            "Vascular": self.vascular,
            "Direction": "DV.AP.LR",
            "VoxelSize": np.array([50, 50, 50], dtype=np.uint8),
        }
        self.affine = np.diag([0.05, 0.05, 0.05, 1.0])
        reference = cf.create_voxeldata(
            np.zeros((3, 2, 4)), dims=("k", "j", "i"),
            voxel_to_world=self.affine, units="mm",
        )
        for target, value in [
            ("OUTPUTS", self.output.parent),
            ("OUTPUT_VASCULAR", self.output),
        ]:
            patcher = patch.object(main, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(
            main.cf.datasets, "fetch_brainglobe_atlas",
            return_value={"reference": reference},
        )
        self.fetch = patcher.start()
        self.addCleanup(patcher.stop)

    def write_source(self) -> None:
        savemat(self.source_path, {"atlas": self.source})

    def test_export_preserves_values_dtype_and_allen_affine(self) -> None:
        self.write_source()
        self.assertEqual(main.export_vascular(self.source_path), self.output)
        self.assertEqual(self.output.name, "brunner-grillet-2021-fusi-template.nii.gz")
        result = cf.load(self.output)
        np.testing.assert_array_equal(result.values, self.vascular.transpose(1, 0, 2))
        self.assertEqual(result.dtype, np.float32)
        self.assertEqual(result.dims, ("k", "j", "i"))
        np.testing.assert_allclose(result.fusi.affine.voxel_to_world, self.affine)
        self.assertEqual(result.fusi.affine.units, "mm")
        self.fetch.assert_called_once_with("allen_mouse_50um")

    def test_default_source_is_checksum_verified_zenodo_download(self) -> None:
        self.write_source()
        with patch.object(main.pooch, "retrieve", return_value=str(self.source_path)) as retrieve:
            main.export_vascular()
        retrieve.assert_called_once_with(
            url=main.SOURCE_URL,
            known_hash="md5:ea1d5f60589350487a5aa574b6c954f0",
            fname="allen_brain_atlas.mat",
            path=main.CACHE,
        )

    def test_rejects_unexpected_metadata(self) -> None:
        for field, value, message in [
            ("Direction", "AP.DV.LR", "direction"),
            ("VoxelSize", [100, 100, 100], "voxel size"),
        ]:
            with self.subTest(field=field):
                original = self.source[field]
                self.source[field] = value
                self.write_source()
                with self.assertRaisesRegex(ValueError, message):
                    main.export_vascular(self.source_path)
                self.assertFalse(self.output.exists())
                self.source[field] = original

    def test_rejects_shape_mismatch(self) -> None:
        self.source["Vascular"] = np.zeros((2, 3, 5), dtype=np.float32)
        self.write_source()
        with self.assertRaisesRegex(ValueError, "differs from Allen grid"):
            main.export_vascular(self.source_path)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
