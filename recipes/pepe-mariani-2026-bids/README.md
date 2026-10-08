# Pepe Mariani 2026 fUSI-BIDS re-export

This repository contains a fUSI-BIDS re-export of the Pepe, Mariani *et al.* (2026)
dataset acquired for the article "Structural and dynamic embedding of the mouse
functional connectome revealed by functional ultrasound imaging (fUSI)."

The source tree is already BIDS-like. This re-export applies only the layout,
metadata, timing, and NIfTI-axis changes needed for fUSI-BIDS and
ConfUSIus-compatible streaming:

- the source `rawdata/` contents are moved to the BIDS root;
- NIfTI files are rewritten in ConfUSIus axis convention: `[time]`, `z` stacking,
  `y` depth, `x` lateral;
- the filename entity `_pose-<index>` is renamed to `_chunk-<index>`, while
  `_pose-vol` is removed from whole-volume files;
- `qform`/`sform` affines are updated for the voxel-axis permutation;
- missing NIfTI `xyzt_units` are set to millimeters and, for 4D files, seconds;
- fUSI `RepetitionTime` and NIfTI `pixdim[4]` are set to `2.4` s; chunk-wise
  `DelayAfterTrigger` values are preserved for slice timing, raw/registered
  chunk sidecars get `DelayTime = 2.0` s, and preprocessed volume sidecars get
  `DelayTime = 0.2` s;
- chunk-wise fUSI files use 0.4 mm singleton `z` thickness and `z` origins for
  1 mm inter-chunk placement; concatenated volume files use 1 mm `z` voxel
  spacing;
- root `pwd.json` metadata fields are updated to the latest fUSI-BIDS names;
- `dataset_description.json` is normalized to valid JSON.

No metadata or values beyond the listed compatibility fixes are intentionally
modified.

## References

- Original dataset (Zenodo): [doi:10.5281/zenodo.20070510](https://doi.org/10.5281/zenodo.20070510)
- Re-exported BIDS dataset (OSF): [osf.io/7yhdc](https://osf.io/7yhdc/)
- Paper: [doi:10.64898/2026.02.05.704055](https://doi.org/10.64898/2026.02.05.704055)
- Original analysis code: [github.com/functional-neuroimaging/PepeMariani_2026](https://github.com/functional-neuroimaging/PepeMariani_2026)
- ConfUSIus convention: [confusius.tools](https://confusius.tools)

## Outputs

- Raw fUSI: `sub-*/ses-*/fusi/*_pwd.nii.gz` (+ JSON sidecars).
- Angiography: `sub-*/ses-*/angio/*_pwd.nii.gz`.
- Derivatives: `derivatives/[registered|preprocessed|Params]/...`.
- Dataset tables: `participants.tsv/json`, `sub-*/sub-*_sessions.tsv`,
  `sub-*/ses-*/*_scans.tsv`.
- Dataset index: `dataset_index.json` at the BIDS root, mapping each
  BIDS-relative path to its OSF file id, size, and MD5 checksum.

All NIfTI files are written in ConfUSIus convention (`[time]`, `z` stacking,
`y` depth, `x` lateral).

## Usage

Re-export the source tree:

```bash
uv run pepe-mariani-convert --src /path/to/source --out /path/to/output_bids --dry-run
uv run pepe-mariani-convert --src /path/to/source --out /path/to/output_bids
```

Sync the new tree to OSF (uploads new and changed files, skips unchanged ones
by MD5) and maintain `dataset_index.json`:

```bash
export OSF_TOKEN=...
export OSF_PROJECT=7yhdc
uv run pepe-mariani-upload --bids-dir /path/to/output_bids
uv run pepe-mariani-upload --index-only      # rebuild and upload only the index
```

Useful options: `--overwrite` (convert); `--index-only` (upload).

## Licensing

- **Code license:** BSD-3-Clause (`LICENSE`)
- **Data license:** see `licenses/DATA_LICENSE.md`
