# fUSI vascular template from Huang *et al.*, 2025

Export a ConfUSIus-loadable vascular template aligned to the Allen atlas from the
published OpenfUSAnalyzer (OfUSA) mouse atlas template.

## Source dataset

The input vascular atlas is bundled with the
[OfUSA software](https://github.com/YunAnGitHub/OpenfUS_Analyzer_OfUSA), described in:

- Huang, Y.-A. *et al.* (2025). *OfUSA: OpenfUS Analyzer, a versatile open-source
  framework for the analysis and visualization of functional ultrasound imaging data
  across animal models*.
  DOI: `10.1101/2025.09.16.676515`.

The source template data is distributed under **CC BY-NC-SA 4.0**. The exported template
in this project is a transformed derivative and should be reused under compatible terms
with attribution.

## Inputs

This repository contains the input file required to build the exported template:

- `inputs/OFUSA_Atlas_Mouse_Vascular.nii`

## Transform

```python
template = cf.load(...)
atlas = cf.datasets.fetch_brainglobe_atlas("allen_mouse_50um")
template = cf.create_voxeldata(
    template.values.transpose(1, 2, 0),
    dims=("k", "j", "i"),
    voxel_to_world=atlas["reference"].fusi.affine.voxel_to_world,
)
```

The bundled NIfTI has no orientation transform in its header. The exporter
suppresses that specific warning for this input because it explicitly assigns the
Allen grid after reordering axes; other warnings remain visible.

## Output

Running the export writes:

- `<repository>/publish/templates/huang-2025-template/<version>/huang-2025-space-allen50_desc-vascular.nii.gz`

`<version>` is read from this recipe's `pyproject.toml` (initially `1.0.0`).

## Usage

Export the template:

```bash
uv run main.py
```

Use it later with ConfUSIus:

```python
import confusius as cf

template = cf.load("../../publish/templates/huang-2025-template/1.0.0/huang-2025-space-allen50_desc-vascular.nii.gz")
atlas = cf.datasets.fetch_brainglobe_atlas("allen_mouse_50um")
```

## Licensing

- **Code license:** BSD-3-Clause (`LICENSE`)
- **Data license:** CC BY-NC-SA 4.0 (`licenses/DATA_LICENSE.md`)

## Citation notes

At minimum cite:
1. Huang *et al.* (2025) / OpenfUSAnalyzer for the vascular template.
2. Wang *et al.* (2020) for the Allen CCF reference framework.
