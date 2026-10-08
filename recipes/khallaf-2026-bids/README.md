# Khallaf 2026 fUSI-BIDS download

Download the naked mole-rat fUSI dataset from Khallaf *et al.* (2026),
"A queen odour mediates reproductive suppression in a eusocial mammal".
The published tree is already BIDS/fUSI-BIDS; this recipe does not convert or
modify its data, metadata, geometry, or filenames.

## Source

- Dataset: [Edmond, DOI 10.17617/3.7QCU1F](https://doi.org/10.17617/3.7QCU1F).
- Archive: `fUSI dataset.zip`, Dataverse file ID `343674` (approximately 19.5 GB).
- Paper: [DOI 10.1038/s41586-026-10772-5](https://doi.org/10.1038/s41586-026-10772-5).
- Data license: [CC0 1.0](licenses/DATA_LICENSE.md).

The recipe reuses ConfUSIus's public `fetch_khallaf_2026` function. Its dependency
is pinned to a pre-S3 Git commit so future ConfUSIus downloader changes cannot
redirect this recipe to our own mirror.

## Usage

From this recipe directory:

```bash
uv run --locked main.py
```

The default destination is `<repository>/work/khallaf-2026-bids/`, outside Git.
To choose a different **parent** directory:

```bash
uv run --locked main.py --data-dir /path/to/staging
# Writes /path/to/staging/khallaf-2026-bids/.
```

The fetcher extracts individual files via HTTP range requests, without retaining
the outer ZIP. No subject, session, run, derivative, or reconstruction filter is
applied. `sourcedata=True` explicitly includes the original Iconeus files, which
the public fetcher excludes by default. Already-cached files are reused, so an
interrupted download can be resumed by rerunning the command.

This mirrors only the fUSI archive, not the other experimental datasets in the
Edmond record. Any nested archives are retained as published. The local
`dataverse_zip_index.json` is download-cache metadata, not a release manifest;
exclude it when preparing a finalized S3 release. Downloading is separate from
release validation and publication, and this recipe never uploads to S3.

## Licensing

The repository's BSD-3-Clause [code license](../../LICENSE) applies to this recipe.
The data retains CC0 1.0. Cite the original paper and dataset when using the data.
