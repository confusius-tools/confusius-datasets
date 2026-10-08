# fUSI vascular template from Huang *et al.*, 2025

Export a ConfUSIus-loadable vascular template aligned to the Allen atlas from the
published OpenfUSAnalyzer (OfUSA) mouse atlas template.

## Source dataset

The input template used here comes from:

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
atlas = cf.atlas.Atlas.from_brainglobe("allen_mouse_50um")
template = template.rename({"x": "y", "y": "z", "z": "x"}).transpose("z", "y", "x").assign_coords(atlas.reference.coords)
```

## Output

Running the export writes:

- `outputs/huang-2025-space-allen50_desc-vascular.nii.gz`

## Usage

Export the template:

```bash
uv run main.py
```

Use it later with ConfUSIus:

```python
import confusius as cf
from confusius.atlas.atlas import Atlas

template = cf.load("outputs/huang-2025-space-allen50_desc-vascular.nii.gz")
atlas = Atlas.from_brainglobe("allen_mouse_50um")
```

## Licensing

- **Code license:** BSD-3-Clause (`LICENSE`)
- **Data license:** CC BY-NC-SA 4.0 (`licenses/DATA_LICENSE.md`)

## Citation notes

At minimum cite:
1. Huang *et al.* (2025) / OpenfUSAnalyzer for the vascular template.
2. Wang *et al.* (2020) for the Allen CCF reference framework.
