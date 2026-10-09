# Cybis Pereira 2026 fUSI-BIDS re-export

This repository contains a fUSI-BIDS re-export of the dataset from the Cybis Pereira
*et al.* (2026) article *"A vascular code for speed in the spatial navigation system"*.
The original dataset is published on Zenodo as a single ZIP archive. This recipe
prepares individual files for release on S3 so downstream tooling can stream them.

This is a re-export rather than a full conversion. Changes apply to the output
copy, not the source Zenodo tree:

- legacy datatype paths and references are updated (`fus` to `fusi`, `angio` to
  `susi`, and the `_fus` suffix to `_fusi`);
- legacy frequency/voltage metadata fields are renamed and the redundant
  `PowerDopplerIntegrationStride` is removed;
- the legacy fixed-threshold SVD filter object (threshold 60) is represented as
  `ClutterFilters: ["svd:remove_first_60_components"]` before loading;
- NIfTI files are rewritten in the [ConfUSIus](https://confusius.tools) axis
  convention: `[time]`, `z` stacking, `y` depth, `x` lateral.

Irregular source timestamps are preserved in `VolumeTiming`; the NIfTI header's
`pixdim[4]` is zero when it cannot represent them. The expected save warning for
this case is suppressed; other warnings remain visible.

## References

- Original dataset (Zenodo): [zenodo.org/records/15476373](https://zenodo.org/records/15476373)
- Historical BIDS mirror (OSF): [osf.io/2v6f7](https://osf.io/2v6f7/)
- Paper: [doi:10.1016/j.celrep.2025.116791](https://doi.org/10.1016/j.celrep.2025.116791)
- ConfUSIus package used for the re-export: [confusius.tools](https://confusius.tools)

## Outputs

- Raw fUSI: `sub-*/ses-*/fusi/*_pwd.nii.gz` (+ JSON sidecars).
- Motion tracking: `sub-*/ses-*/motion/*_tracksys-DLC_*_motion.tsv/json` and
  `*_tracksys-DLC_*_channels.tsv/json`.
- Derivatives:
  `derivatives/[dlc-videos|glm-speed|glm-angular-speed|decode-speed|interanimal-decode-speed]`.

All NIfTI files are written in [ConfUSIus](https://confusius.tools) convention
(`[time]`, `z` stacking, `y` depth, `x` lateral).

## Usage

Without `--out`, the converter writes to
`<repository>/publish/datasets/cybis-pereira-2026-bids/<version>/`, using this recipe's
`pyproject.toml` version (initially `1.0.0`). `--out` overrides that location.

Re-export the unzipped Zenodo tree:

```bash
uv run cybis-convert --src /path/to/zenodo/unzipped --out /path/to/output_bids --dry-run
uv run cybis-convert --src /path/to/zenodo/unzipped --out /path/to/output_bids
```

Useful option: `--overwrite`. See the [root README](../../README.md) for release
validation and S3 publication; this recipe does not upload or generate an index.

## Licensing

- **Code license:** BSD-3-Clause (`LICENSE`)
- **Data license:** CC BY 4.0 (`licenses/DATA_LICENSE.md`)
