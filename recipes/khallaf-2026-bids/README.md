# Khallaf 2026 fUSI-BIDS conversion

Download and unpack the complete naked mole-rat fUSI archive from Edmond,
including all derivatives and original Iconeus acquisitions. Rename legacy
`angio/` datatype folders to `susi/` and update scan-table and JSON path references.
No image conversion, filtering, or ConfUSIus dependency; source-only files stay unchanged.

## Usage

Requires `curl` and `uv`. From the repository root:

```bash
just khallaf-2026
```

Or from this recipe directory:

```bash
uv run --locked main.py --out /path/to/release --data-dir /path/to/cache
```

The default output is `<repository>/publish/datasets/khallaf-2026-bids/<version>/`,
where `<version>` comes from this recipe's `pyproject.toml` (initially `1.0.0`).
`--out` overrides it. `--data-dir` now selects only the download cache (default:
`<repository>/work/`), not the output parent. Use a fresh output folder; existing
datasets are never overwritten.

`curl` retries and resumes interrupted downloads. Python's standard library
extracts the ZIP into a temporary directory, checks ZIP member CRCs during
extraction, and rejects unsafe paths. Datatype folders and references are updated
in the temporary tree before the completed dataset is renamed into place and the
ZIP is deleted. Failed extraction or conversion retains the ZIP for retry. Allow space for both the approximately 19.5 GB archive and its extracted
contents. Nested archives are kept as published; this recipe does not upload.

## Source and license

- Dataset: [Edmond, DOI 10.17617/3.7QCU1F](https://doi.org/10.17617/3.7QCU1F).
- Archive: `fUSI dataset.zip`, file ID `343674`.
- Paper: [Khallaf et al. (2026), DOI 10.1038/s41586-026-10772-5](https://doi.org/10.1038/s41586-026-10772-5).
- Data: [CC0 1.0](licenses/DATA_LICENSE.md); cite the original dataset and paper.
- Code: repository [BSD-3-Clause license](../../LICENSE).

Only the fUSI archive is mirrored, not the other experiments in the Edmond record.
