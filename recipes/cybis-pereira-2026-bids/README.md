# Cybis Pereira 2026 fUSI-BIDS re-export

This repository contains a fUSI-BIDS re-export of the dataset from the Cybis Pereira
*et al.* (2026) article *"A vascular code for speed in the spatial navigation system"*. 
The original dataset is published on Zenodo as a single ZIP
archive, which means individual files cannot be fetched on demand. This re-export
hosts the same data unzipped on OSF so that downstream tooling can stream individual
files.

This is a re-export rather than a full conversion. Only two changes are applied to
the Zenodo tree:

- the `fus` datatype folder is renamed to `fusi` (BIDS-BEP for functional
  ultrasound imaging);
- NIfTI files are rewritten in the [ConfUSIus](https://confusius.tools) axis
  convention: `[time]`, `z` stacking, `y` depth, `x` lateral.

No other files, metadata, or values are modified.

## References

- Original dataset (Zenodo): [zenodo.org/records/15476373](https://zenodo.org/records/15476373)
- Re-exported BIDS dataset (OSF): [osf.io/2v6f7](https://osf.io/2v6f7/)
- Paper: [doi:10.1016/j.celrep.2025.116791](https://doi.org/10.1016/j.celrep.2025.116791)
- ConfUSIus package used for the re-export: [confusius.tools](https://confusius.tools)

## Outputs

- Raw fUSI: `sub-*/ses-*/fusi/*_pwd.nii.gz` (+ JSON sidecars).
- Motion tracking: `sub-*/ses-*/motion/*_tracksys-DLC_*_motion.tsv/json` and
  `*_tracksys-DLC_*_channels.tsv/json`.
- Derivatives:
  `derivatives/[dlc-videos|glm-speed|glm-angular-speed|decode-speed|interanimal-decode-speed]`.
- Dataset index: `dataset_index.json` at the BIDS root, mapping each
  BIDS-relative path to its OSF file id and size.

All NIfTI files are written in [ConfUSIus](https://confusius.tools) convention
(`[time]`, `z` stacking, `y` depth, `x` lateral).

## Usage

Re-export the unzipped Zenodo tree:

```bash
uv run cybis-convert --src /path/to/zenodo/unzipped --out /path/to/output_bids --dry-run
uv run cybis-convert --src /path/to/zenodo/unzipped --out /path/to/output_bids
```

Sync the new tree to OSF (uploads new and changed files, skips unchanged ones
by MD5) and maintain `dataset_index.json`:

```bash
export OSF_TOKEN=...
export OSF_PROJECT=2v6f7
uv run cybis-upload --bids-dir /path/to/output_bids
uv run cybis-upload --index-only           # rebuild and upload only the index
```

Useful options: `--overwrite` (convert); `--index-only` (upload).

## Licensing

- **Code license:** BSD-3-Clause (`LICENSE`)
- **Data license:** CC BY 4.0 (`licenses/DATA_LICENSE.md`)
