# Pereira 2025 fUSI-BIDS re-export

This repository contains a fUSI-BIDS re-export of the Pereira *et al.* dataset
*"Induction of hemodynamic traveling waves by glial-related vasomotion in a rat
model of neuroinflammation: implications for functional neuroimaging"*.

The source tree is already BIDS-like. This re-export applies only the layout and
NIfTI-axis changes needed for fUSI-BIDS and ConfUSIus-compatible streaming:

- fUSI runs are placed under the `fusi` datatype folder;
- NIfTI files are rewritten in ConfUSIus axis convention: `[time]`, `z` stacking,
  `y` depth, `x` lateral, with singleton 2D slices on the `z` axis;
- `qform`/`sform` affines are updated for the voxel-axis permutation.

## References

- Original dataset (Zenodo): [doi:10.5281/zenodo.15194839](https://doi.org/10.5281/zenodo.15194839)
- Historical BIDS mirror (OSF): [osf.io/pqa65](https://osf.io/pqa65/)
- Paper: [doi:10.1016/j.ebiom.2025.105777](https://doi.org/10.1016/j.ebiom.2025.105777)
- ConfUSIus convention: [confusius.tools](https://confusius.tools)

## Outputs

- Raw fUSI: `sub-*/ses-*/fusi/*_pwd.nii.gz` (+ JSON sidecars).
- Events: `task-stim_events.tsv`.
- Dataset tables: `participants.tsv/json`, `sub-*/sub-*_sessions.tsv`.

All NIfTI files are written in ConfUSIus convention (`[time]`, `z` stacking,
`y` depth, `x` lateral).

## Usage

Without `--out`, the converter writes to
`<repository>/publish/datasets/pereira-2025-bids/<version>/`, using this recipe's
`pyproject.toml` version (initially `1.0.0`). `--out` overrides that location.

Re-export the source tree:

```bash
uv run pereira-convert --src /path/to/source --out /path/to/output_bids --dry-run
uv run pereira-convert --src /path/to/source --out /path/to/output_bids
```

Useful option: `--overwrite`. See the [root README](../../README.md) for release
validation and S3 publication; this recipe does not upload or generate an index.

## Licensing

- **Code license:** BSD-3-Clause (`LICENSE`)
- **Data license:** see `licenses/DATA_LICENSE.md`
