# fUSI mouse brain template from Pepe, Mariani *et al.*, 2026 

Export a ConfUSIus-loadable fUSI template aligned to the Allen atlas from the published
Pepe, Mariani *et al.* (2026) template.

## Source dataset

The input template used here comes from the dataset associated with:

- Pepe, C., Mariani, J.-C., Urosevic, M., Gini, S., Stuefer, A., Ricci, F.,
  Galbusera, A., Iurilli, G., and Gozzi, A. (2026). *Structural and dynamic
  embedding of the mouse functional connectome revealed by functional
  ultrasound imaging (fUSI).* DOI: `10.64898/2026.02.05.704055`.

The dataset is available on [Zenodo (10.5281/zenodo.18486493)](https://zenodo.org/records/18486493).
The template is included in the [source ZIP](https://zenodo.org/api/records/18486493/files/2026-02-03_PepeMariani_fUSI-anaesthetised.zip/content).

The published dataset is released under the Creative Commons Attribution 4.0
International License (CC BY 4.0). The template exported by this project is derived
from that dataset and should therefore be reused with appropriate attribution.

## Inputs

This repository contains the two input files required to build the exported
template:

- `inputs/published_params/source-BI_space-fUSI_desc-GillianTemplate_res-110umx100umx100um_feature.nii.gz`
- `inputs/registration/transform_Affine_AllenPIRRAS100um-2-fUSIPIRRAS_Composite.h5`

Notes:

- The template comes from the published dataset:
  `2026-02-03_PepeMariani_fUSI-anaesthetised/derivatives/Params/angio/templates/`.
- The HDF5 transform was communicated by the paper authors.

## Coordinate frames

The export retains the original axis-aligned native/scanner geometry in `qform`
(native voxel spacing and the original export's coordinate origin). The full
Allen atlas alignment, including shear, is stored separately in `sform`.
The form codes are `qform_code = 1` (scanner anatomical) and `sform_code = 5`
(other standard template space, here Allen).
No image interpolation is performed; only the voxel axes are reordered.

Load with `coordinate_affine="qform"` for registration in scanner space.
`template.affines["world_to_sform"]` then maps scanner world coordinates into
Allen atlas world coordinates. Loading with `coordinate_affine="sform"` instead
expresses the same voxel data directly in Allen space.

## Output

Running the export writes:

- `<repository>/publish/templates/pepe-mariani-2026-template/<version>/pepe-mariani-2026-fusi-template.nii.gz`

`<version>` is read from this recipe's `pyproject.toml` (initially `1.0.0`).

## Usage

Export the template:

```bash
uv run main.py
```

Use it later with ConfUSIus:

```python
import confusius as cf

template = cf.load(
    "../../publish/templates/pepe-mariani-2026-template/1.0.0/pepe-mariani-2026-fusi-template.nii.gz",
    coordinate_affine="qform",
)
atlas = cf.datasets.fetch_brainglobe_atlas("allen_mouse_100um")
resampled_atlas = atlas.atlas.resample_like(
    template, template.affines["world_to_sform"]
)
```

Run the geometry regression checks from this recipe directory:

```bash
uv run --locked python -m doctest main.py
```

## Licensing

- **Code license:** BSD-3-Clause (`LICENSE`)
- **Data license:** CC BY 4.0 (`licenses/DATA_LICENSE.md`)
