# Landemard 2026 fUSI-BIDS re-export

Stage the dataset from the Landemard *et al.* (2026) article "Brainwide blood
volume reflects opposing neural populations" for release on S3.

This recipe copies the local BIDS tree into a versioned release folder, renames
legacy `angio/` datatype folders to `susi/`, and updates scan-table and JSON path
references. Images and source-only files are unchanged; it does not upload or
generate an index.

## References

- Original dataset: [doi:10.5522/04/31376338](https://doi.org/10.5522/04/31376338)
- Historical BIDS mirror (OSF): [osf.io/dkseb](https://osf.io/dkseb/overview)
- Paper: [doi:10.1038/s41586-026-10350-9](https://doi.org/10.1038/s41586-026-10350-9)
- Original analysis code: [github.com/agneslandemard/fusi_analyses](https://github.com/agneslandemard/fusi_analyses)

## Usage

Stage an existing BIDS tree (from the repository root):

```bash
just landemard-2026 /path/to/landemard_2026_dataset
```

Or from this recipe directory: `uv run --locked main.py /path/to/source`.
The default destination is `<repository>/publish/datasets/landemard-2026-bids/<version>/`,
using the version from `pyproject.toml` (initially `1.0.0`). `--out` overrides it;
existing destinations are rejected. See the root README for S3 publication.

## Licensing

- **Code license:** BSD-3-Clause (`LICENSE`)
- **Data license:** CC BY-NC 4.0 (`licenses/DATA_LICENSE.md`)
