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
just                                            # List recipes.
just pereira-2025 /path/to/source               # Prepare recordings.
just pereira-2025 /path/to/source --dry-run     # Preview conversion.
just khallaf-2026                               # Download from Edmond.
just template-huang-2025                        # Export a bundled template.
```

Outputs go to:

- Recordings: `publish/datasets/<recipe-directory-name>/<version>/`
- Templates: `publish/templates/<recipe-directory-name>/<version>/`

The version comes from each recipe's `pyproject.toml`. Recording converters and
staging scripts accept `--out` to override the destination. Landemard copies an
existing BIDS tree unchanged into a fresh destination.

## 2. Generate a release manifest

After a recipe finishes, review its output and generate its file inventory:

```bash
export RELEASE=publish/datasets/pereira-2025-bids/1.0.0
just manifest "$RELEASE"
```

This writes `manifest.json`, mapping relative paths to byte sizes and SHA-256
hashes. The shared [release script](scripts/releases.py) streams file contents,
excludes the manifest itself, rejects empty releases, symlinks, obvious temporary
or credential files, and old conversion logs, then writes the manifest atomically.
For dataset releases it also adds `manifest.json` to `.bidsignore`, preserving
existing rules, and includes the updated `.bidsignore` in the manifest. Templates
do not need a `.bidsignore`.
It does not check scientific correctness or whether recordings are missing.

Keep conversion-specific checks in the recipe tests; review orientation/alignment
when changing a recipe. Preserve licenses, attribution, and provenance. Do not
change release files after generating the manifest or run these commands while a
recipe is writing output.

Published versions are immutable. Bump the recipe's project version and update its
lockfile for a new release; never rerun into an already published version.

## 3. Upload to S3

Install the [AWS CLI](https://aws.amazon.com/cli/) and configure an upload profile
for `s3://confusius-datasets` in US West (Oregon), `us-west-2`. Upload one prepared
release at a time, preserving its path under `publish/`. Review the dry run:

```bash
export BUCKET=s3://confusius-datasets
export AWS_REGION=us-west-2
export REMOTE="$BUCKET/${RELEASE#publish/}"
aws s3 sync "$RELEASE/" "$REMOTE/" --exclude manifest.json --dryrun
```

Repeat without `--dryrun` after review. Verify uploaded contents against the
manifest and check anonymous access, then upload the manifest:

```bash
aws s3 cp "$RELEASE/manifest.json" "$REMOTE/manifest.json"
```

After the manifest upload is verified, explicitly mark this version as latest.
If a catalog already exists in S3, first download it to preserve other entries:
`aws s3 cp "$BUCKET/last_versions.conf" publish/last_versions.conf`.

```bash
just latest "$RELEASE"
aws s3 cp publish/last_versions.conf "$BUCKET/last_versions.conf"
```

`last_versions.conf` has separate `[datasets]` and `[templates]` sections mapping
recipe names to versions. The update command requires a manifest and preserves
other catalog entries; it does not check S3 or automatically promote local folders.
Use one publisher at a time to avoid overwriting another publisher's catalog changes.

Do not use `--delete` or wrap releases in ZIP/TAR archives. Uploading to S3 is not
atomic; publish the catalog last, only after release files and the manifest are verified.

## Licensing

[LICENSE](LICENSE) covers code only. Data retains its per-recipe license; cite the
original papers and datasets, and ConfUSIus when using its tooling.
