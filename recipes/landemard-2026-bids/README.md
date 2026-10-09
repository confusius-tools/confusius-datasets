# Landemard 2026 fUSI-BIDS re-export

This repository hosts the fUSI-BIDS-formatted re-export of the dataset from the
Landemard *et al.* (2026) article "Brainwide blood volume reflects opposing neural
populations", mirrored on OSF so that ConfUSIus can fetch individual files on demand.

This dataset is already published in fUSI-BIDS, so no conversion step is required: the
local BIDS tree is unzipped and uploaded as-is to OSF and a `dataset_index.json` is
built mapping each BIDS-relative path to its OSF file id, size, and md5.

## References

- Original dataset: [doi:10.5522/04/31376338](https://doi.org/10.5522/04/31376338)
- Re-exported BIDS dataset (OSF): [osf.io/dkseb](https://osf.io/dkseb/overview)
- Paper: [doi:10.1038/s41586-026-10350-9](https://doi.org/10.1038/s41586-026-10350-9)
- Original analysis code: [github.com/agneslandemard/fusi_analyses](https://github.com/agneslandemard/fusi_analyses)
- ConfUSIus package used: [confusius.tools](https://confusius.tools)

## Usage

Stage an existing BIDS tree without conversion (from the repository root):

```bash
just landemard-2026 /path/to/landemard_2026_dataset
```

Or from this recipe directory: `uv run --locked main.py /path/to/source`.
The default destination is `<repository>/publish/datasets/landemard-2026-bids/<version>/`,
using the version from `pyproject.toml` (initially `1.0.0`). `--out` overrides it;
existing destinations are rejected. See the root README for S3 publication.

Legacy OSF upload commands remain available:

```bash
export OSF_TOKEN=...
export OSF_PROJECT=dkseb
uv run landemard-upload --bids-dir /path/to/landemard_2026_dataset
```

Useful options: `--rebuild-index`. Re-upload detects changed files automatically by
comparing local md5s against the index.

## Licensing

- **Code license:** BSD-3-Clause (`LICENSE`)
- **Data license:** CC BY-NC 4.0 (`licenses/DATA_LICENSE.md`)
