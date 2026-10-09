import tomllib
from pathlib import Path

import confusius as cf
import numpy as np
import SimpleITK as sitk
import xarray as xr

ROOT = Path(__file__).resolve().parent
INPUTS_ROOT = ROOT / "inputs"
PUBLISHED_PARAMS_ROOT = INPUTS_ROOT / "published_params"
REGISTRATION_ROOT = INPUTS_ROOT / "registration"
with (ROOT / "pyproject.toml").open("rb") as source:
    VERSION = tomllib.load(source)["project"]["version"]
OUTPUTS_ROOT = ROOT.parents[1] / "publish" / "templates" / ROOT.name / VERSION

FUSI_PATH = (
    PUBLISHED_PARAMS_ROOT
    / "source-BI_space-fUSI_desc-GillianTemplate_res-110umx100umx100um_feature.nii.gz"
)
COMPOSITE_PATH = (
    REGISTRATION_ROOT / "transform_Affine_AllenPIRRAS100um-2-fUSIPIRRAS_Composite.h5"
)
OUTPUT_TEMPLATE_PATH = OUTPUTS_ROOT / "pepe-mariani-2026-fusi-template.nii.gz"

# Extracted from the original moving image used to estimate the HDF5 registration.
A_ALLEN_PIRRAS = np.array(
    [
        [0.0, -1.0, 0.0, 0.0],
        [0.0, 0.0, -1.0, 0.0],
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
)

# ConfUSIus stores world coordinates in component order (S, A, R) for an RAS NIfTI,
# while ITK uses LPS (x, y, z). This matrix converts between those conventions.
Q_CONFUSIUS_WORLD_TO_LPS = np.array(
    [
        [0, 0, -1, 0],
        [0, -1, 0, 0],
        [1, 0, 0, 0],
        [0, 0, 0, 1],
    ]
)


def composite_to_4x4(transform: "sitk.Transform") -> np.ndarray:
    """Flatten a linear SimpleITK transform into a 4x4 affine.

    Parameters
    ----------
    transform : sitk.Transform
        Linear transform read from the ANTs HDF5 file.

    Returns
    -------
    numpy.ndarray
        Homogeneous affine in ITK's LPS world frame.
    """
    if isinstance(transform, sitk.CompositeTransform):
        out = np.eye(4)
        for idx in range(transform.GetNumberOfTransforms()):
            out = out @ composite_to_4x4(transform.GetNthTransform(idx))
        return out

    linear = np.asarray(transform.GetMatrix()).reshape(3, 3)  # type: ignore
    translation = np.asarray(transform.GetTranslation())  # type: ignore
    try:
        center = np.asarray(transform.GetCenter())  # type: ignore
    except AttributeError:
        center = np.zeros(3)

    out = np.eye(4)
    out[:3, :3] = linear
    out[:3, 3] = translation + center - linear @ center
    return out


def build_template_to_atlas_affine(fusi: xr.DataArray) -> np.ndarray:
    """Build the native template to BrainGlobe-atlas affine.

    Parameters
    ----------
    fusi : xarray.DataArray
        Published template loaded with ConfUSIus.

    Returns
    -------
    numpy.ndarray
        Affine mapping native template voxel indices to atlas world coordinates.
    """
    transform = sitk.ReadTransform(str(COMPOSITE_PATH))
    t_lps = composite_to_4x4(transform)
    t_world = np.linalg.inv(Q_CONFUSIUS_WORLD_TO_LPS) @ t_lps @ Q_CONFUSIUS_WORLD_TO_LPS

    # AllenPIRRAS phys (R, I, P) -> BrainGlobe phys by permuting component order only.
    r_reorient = np.array(
        [
            [0, 0, 1, 0],
            [0, 1, 0, 0],
            [1, 0, 0, 0],
            [0, 0, 0, 1],
        ],
        dtype=float,
    )

    a_fusi = (
        fusi.attrs["affines"]["world_to_sform"] @ fusi.fusi.affine.voxel_to_world
    )
    return r_reorient @ np.linalg.inv(A_ALLEN_PIRRAS) @ t_world @ a_fusi


def make_native_allen_oriented_template(
    fusi: xr.DataArray,
    template_to_atlas: np.ndarray,
) -> xr.DataArray:
    """Convert the native template into a ConfUSIus-style coronal layout.

    >>> source = cf.create_voxeldata(np.arange(24).reshape(4, 2, 3), dims=("k", "j", "i"), spacing=(1, 1, 1))
    >>> result = make_native_allen_oriented_template(source, np.eye(4))
    >>> np.array_equal(result, np.asarray(source).transpose(2, 1, 0))
    True
    >>> np.allclose(result.fusi.affine.voxel_to_world[:3, :3], np.eye(3)[::-1])
    True

    Parameters
    ----------
    fusi : xarray.DataArray
        Published template loaded with ConfUSIus.
    template_to_atlas : numpy.ndarray
        Affine mapping native template voxel indices to BrainGlobe atlas world space.

    Returns
    -------
    xarray.DataArray
        Reoriented template carrying the full voxel-to-atlas transform.
    """
    # Coronal voxel layout: k<-old i, j<-old j, i<-old k.
    new_to_old = np.eye(4)
    new_to_old[:3, :3] = [[0, 0, 1], [0, 1, 0], [1, 0, 0]]
    return cf.create_voxeldata(
        np.asarray(fusi).transpose(2, 1, 0),
        dims=("k", "j", "i"),
        voxel_to_world=template_to_atlas @ new_to_old,
        units=fusi.fusi.affine.units,
        # The registration contains shear, which only sform can encode exactly.
        attrs={"sform_code": 1, "qform_code": 0},
        name="fusi_template_native_allen_oriented",
    )


def export_template() -> Path:
    """Export the ConfUSIus-loadable template.

    Returns
    -------
    pathlib.Path
        Path to the written output NIfTI file.
    """
    OUTPUTS_ROOT.mkdir(parents=True, exist_ok=True)

    fusi = cf.load(str(FUSI_PATH))
    if "time" in fusi.dims:
        fusi = fusi.squeeze("time", drop=True)

    template_to_atlas = build_template_to_atlas_affine(fusi)
    exported = make_native_allen_oriented_template(fusi, template_to_atlas)
    cf.save(exported, OUTPUT_TEMPLATE_PATH)
    return OUTPUT_TEMPLATE_PATH


def main() -> None:
    output_path = export_template()
    loaded = cf.load(str(output_path))
    print(output_path)
    print(f"dims={loaded.dims} shape={loaded.shape}")


if __name__ == "__main__":
    main()
