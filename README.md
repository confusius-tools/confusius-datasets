# ConfUSIus Functional Ultrasound Imaging Dataset Collection

Recipes to download or prepare functional ultrasound imaging (fUSI) datasets and brain
templates for [ConfUSIus](https://confusius.tools). Finalized releases are published on
Amazon S3.

## Recipes and sources

Download and unpack the original inputs before running a recipe. Khallaf downloads
automatically; both templates have their inputs bundled. Recipe READMEs provide
input details and provenance.

| Recipe | Original source / download | Data license |
| --- | --- | --- |
| [Nunez-Elizalde 2022](recipes/nunez-elizalde-2022-bids/) | [Figshare](https://doi.org/10.6084/m9.figshare.19316228) · [ZIP](https://ndownloader.figshare.com/files/34307132) | CC BY 4.0 |
| [Landemard 2026](recipes/landemard-2026-bids/) | [UCL Figshare](https://doi.org/10.5522/04/31376338) · [Complete ZIP (v3)](https://rdr.ucl.ac.uk/ndownloader/articles/31376338/versions/3) | CC BY-NC 4.0 |
| [Khallaf 2026](recipes/khallaf-2026-bids/) | [Edmond](https://doi.org/10.17617/3.7QCU1F) · [fUSI ZIP](https://edmond.mpg.de/api/access/datafile/343674) | CC0 1.0 |
| [Cybis Pereira 2026](recipes/cybis-pereira-2026-bids/) | [Zenodo](https://zenodo.org/records/15476373) · [ZIP](https://zenodo.org/api/records/15476373/files/dataset.zip/content) | CC BY 4.0 |
| [Pereira 2025](recipes/pereira-2025-bids/) | [Zenodo](https://zenodo.org/records/15194839) · [ZIP](https://zenodo.org/api/records/15194839/files/rawdata.zip/content) | CC BY 4.0 |
| [Pepe Mariani 2026 recordings](recipes/pepe-mariani-2026-bids/) | [Zenodo](https://zenodo.org/records/20070510) · [ZIP](https://zenodo.org/api/records/20070510/files/2026-02-03_PepeMariani_fUSI-anaesthetised.zip/content) | CC BY 4.0 |
| [Pepe Mariani 2026 template](recipes/pepe-mariani-2026-template/) | [Zenodo](https://zenodo.org/records/18486493) (inputs included) | CC BY 4.0 |
| [Huang 2025 template](recipes/huang-2025-template/) | [OfUSA software](https://github.com/YunAnGitHub/OpenfUS_Analyzer_OfUSA) (input included) | CC BY-NC-SA 4.0 |

Landemard's complete download contains subject ZIPs. Unpack those into one BIDS root
alongside the root metadata, then pass that directory to `just landemard-2026`.

## 1. Run recipes

Install [uv](https://docs.astral.sh/uv/) and [just](https://just.systems/). From the
repository root:

```bash
just                                        # List recipes.
just pereira-2025 /path/to/source            # Prepare recordings.
just pereira-2025 /path/to/source --dry-run   # Preview conversion.
just khallaf-2026                            # Download from Edmond.
just template-huang-2025                     # Export a bundled template.
```

Outputs go to:

- Recordings: `publish/datasets/<recipe-directory-name>/<version>/`
- Templates: `publish/templates/<recipe-directory-name>/<version>/`

The version comes from each recipe's `pyproject.toml`. Recording converters and
staging scripts accept `--out` to override the destination. Landemard copies an
existing BIDS tree unchanged into a fresh destination.

## 2. Validate releases

**Release finalization and checksum-index generation are not implemented yet.
Recipe output is not automatically publish-ready.** Each release needs a
`dataset_index.json` mapping relative file paths to sizes and SHA-256 hashes.
A separate `release.json` is optional.

Preserve each dataset's layout, license, attribution, and provenance. Keep only
completed, validated releases in `publish/`; exclude caches, partial files, and
unrelated old outputs. Do not upload while recipes are running.

Published versions are immutable. Bump the recipe's project version and update its
lockfile for a new release; never rerun into an already published version.

## 3. Upload to S3

After release finalization and validation, install the
[AWS CLI](https://aws.amazon.com/cli/) and configure an upload profile for
`s3://confusius-datasets` in US West (Oregon), `us-west-2`. Review the dry run:

```bash
export BUCKET=s3://confusius-datasets
export AWS_REGION=us-west-2
aws s3 sync publish/ "$BUCKET/" --exclude '*/dataset_index.json' --dryrun
```

Repeat without `--dryrun` after review. Verify uploaded contents and anonymous
access before uploading the checksum indexes last:

```bash
aws s3 cp publish/ "$BUCKET/" --recursive \
  --exclude '*' --include '*/dataset_index.json'
```

Do not use `--delete` or wrap releases in ZIP/TAR archives. Uploading to S3 is not
atomic; advertise a release only after its files and index have been verified.

## Licensing

[LICENSE](LICENSE) covers code only. Data retains its per-recipe license; cite the
original papers and datasets, and ConfUSIus when using its tooling.
