# Data license

The source dataset, Macé and Montaldo, *Whole-brain visually evoked activity maps
in head-fixed awake mice*, is distributed under **CC BY 4.0**:

- Dataset: https://zenodo.org/records/4905862
- Dataset DOI: https://doi.org/10.5281/zenodo.4905862
- Related paper: Brunner, Grillet *et al.* (2021), https://doi.org/10.1038/s41596-021-00548-8
- License: https://creativecommons.org/licenses/by/4.0/

The Zenodo file description credits the atlas adaptation to Allen Mouse Common
Coordinate Framework v3. Cite Wang *et al.* (2020) for that reference framework.

This recipe exports `atlas.Vascular` from `allen_brain_atlas.mat`, reorders its
axes, and assigns the Allen 50 µm coordinate grid. Vascular voxel values are
unchanged. Redistributed derivatives must preserve attribution, link to the
license, and indicate these changes.
