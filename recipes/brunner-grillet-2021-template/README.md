# fUSI vascular template from Brunner, Grillet *et al.*, 2021

Download and export an Allen-aligned vascular template for ConfUSIus from the
original MATLAB atlas distributed with Brunner, Grillet *et al.* (2021).

## Source dataset

- Paper: Brunner, Grillet *et al.* (2021), DOI: [10.1038/s41596-021-00548-8](https://doi.org/10.1038/s41596-021-00548-8).
- Dataset: Macé and Montaldo, *Whole-brain visually evoked activity maps in head-fixed
  awake mice*, [Zenodo record 4905862](https://zenodo.org/records/4905862)
  (June 2021 metadata update), DOI: `10.5281/zenodo.4905862`.
- Input: [`allen_brain_atlas.mat`](https://zenodo.org/records/4905862/files/allen_brain_atlas.mat?download=1),
  MD5 `ea1d5f60589350487a5aa574b6c954f0`.
- Data license: **CC BY 4.0**, as specified by the Zenodo record.

The upstream file description identifies the atlas as adapted from Allen Mouse
Common Coordinate Framework v3, with a micro-Doppler vascular reference.

No input data is bundled in Git. The first run
downloads the approximately 72.5 MB MAT file to `<repository>/work/brunner-grillet-2021-template/`;
subsequent runs reuse the cache after checksum verification.

## Transform

The recipe reads only `atlas.Vascular`, checks `atlas.Direction == "DV.AP.LR"`
and `atlas.VoxelSize == [50, 50, 50]` (µm), then reorders the array:

```python
data = atlas["Vascular"].transpose(1, 0, 2)
# (160, 264, 228), DV/AP/LR → (264, 160, 228), AP/DV/LR
```

It assigns the affine and units from ConfUSIus's BrainGlobe `allen_mouse_50um`
reference, after checking the shapes match. The MAT file does **not** contain a
world-coordinate affine. This is an explicit Allen-grid assignment, not a
registration or a bregma-centered transform. Vascular voxel values are unchanged.

Histology, regional labels, region metadata, and boundary lines also present in
the MAT file are not exported by this recipe.

## Usage

From the repository root:

```bash
just template-brunner-grillet-2021
```

Or directly:

```bash
uv run --locked --project recipes/brunner-grillet-2021-template python recipes/brunner-grillet-2021-template/main.py
```

Output:

```text
publish/templates/brunner-grillet-2021-template/1.0.0/brunner-grillet-2021-fusi-template.nii.gz
```

The version is read from this recipe's `pyproject.toml` (initially `1.0.0`).

Load the result with ConfUSIus:

```python
import confusius as cf

template = cf.load("publish/templates/brunner-grillet-2021-template/1.0.0/brunner-grillet-2021-fusi-template.nii.gz")
```

Run the offline recipe tests:

```bash
uv run --locked --project recipes/brunner-grillet-2021-template python -m unittest discover -s recipes/brunner-grillet-2021-template -p 'test_*.py'
```

## Licensing and citation

- **Code:** BSD-3-Clause (`LICENSE`).
- **Data:** CC BY 4.0 ([license and attribution](licenses/DATA_LICENSE.md)).

Cite Brunner, Grillet *et al.* (2021), the Macé and Montaldo Zenodo dataset, and Wang
*et al.* (2020) for the Allen CCF reference framework. Note that this derivative
reorders axes and assigns the Allen 50 µm coordinate grid without changing
vascular voxel values.
