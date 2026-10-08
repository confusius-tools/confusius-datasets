# Khallaf 2026 fUSI-BIDS download

Download and unpack the complete naked mole-rat fUSI archive from Edmond,
including all derivatives and original Iconeus acquisitions. No conversion,
filtering, or ConfUSIus dependency.

## Usage

Requires `curl` and `uv`. From the repository root:

```bash
just khallaf-2026
```

Or from this recipe directory:

```bash
uv run --locked main.py --data-dir /path/to/staging
```

The default output is `<repository>/work/khallaf-2026-bids/`. `--data-dir` selects
its parent directory. Use a fresh output folder; existing datasets are never
overwritten.

`curl` retries and resumes interrupted downloads. Python's standard library
extracts the ZIP into a temporary directory, checks ZIP member CRCs during
extraction, and rejects unsafe paths. The completed dataset is then renamed into
place, and the downloaded ZIP is deleted. Failed extraction retains the ZIP for
retry. Allow space for both the approximately 19.5 GB archive and its extracted
contents. Nested archives are kept as published; this recipe does not upload.

## Source and license

- Dataset: [Edmond, DOI 10.17617/3.7QCU1F](https://doi.org/10.17617/3.7QCU1F).
- Archive: `fUSI dataset.zip`, file ID `343674`.
- Paper: [Khallaf et al. (2026), DOI 10.1038/s41586-026-10772-5](https://doi.org/10.1038/s41586-026-10772-5).
- Data: [CC0 1.0](licenses/DATA_LICENSE.md); cite the original dataset and paper.
- Code: repository [BSD-3-Clause license](../../LICENSE).

Only the fUSI archive is mirrored, not the other experiments in the Edmond record.
