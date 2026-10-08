# ConfUSIus Functional Ultrasound Imaging Dataset Collection

Recipes to download or prepare functional ultrasound imaging (fUSI) datasets and
brain templates for [ConfUSIus](https://confusius.tools). Generated data stays out of
Git; finalized releases are published as individual files on Amazon S3.

## Recipes

| Recipe | Data license |
| --- | --- |
| [Nunez-Elizalde 2022](recipes/nunez-elizalde-2022-bids/) | CC BY 4.0 |
| [Landemard 2026](recipes/landemard-2026-bids/) | CC BY-NC 4.0 |
| [Khallaf 2026](recipes/khallaf-2026-bids/) | CC0 1.0 |
| [Cybis Pereira 2026](recipes/cybis-pereira-2026-bids/) | CC BY 4.0 |
| [Pereira 2025](recipes/pereira-2025-bids/) | CC BY 4.0 |
| [Pepe Mariani 2026 recordings](recipes/pepe-mariani-2026-bids/) | CC BY 4.0 |
| [Pepe Mariani 2026 template](recipes/pepe-mariani-2026-template/) | CC BY 4.0 |
| [Huang 2025 template](recipes/huang-2025-template/) | CC BY-NC-SA 4.0 |

## 1. Run recipes

Install [uv](https://docs.astral.sh/uv/) and [just](https://just.systems/). From the
repository root:

```bash
just                                         # List recipes.
just pereira-2025 /path/to/source              # Prepare recordings.
just pereira-2025 /path/to/source --dry-run    # Forward converter options.
just khallaf-2026                             # Download from Edmond.
just template-huang-2025                      # Export a bundled template.
```

Each dataset has a named just recipe and stages its output in `work/<dataset-id>/`
by default. See the linked READMEs for source inputs. Landemard only copies an
existing BIDS tree; templates use bundled inputs.

`uv run` creates and syncs each environment automatically; no separate `uv sync`
is needed. Recipe `.python-version` files select Python 3.13. `--locked` prevents
silent lockfile changes; update dependencies explicitly with `uv lock` when needed.
You can also run commands directly inside a recipe directory, e.g.
`uv run --locked pereira-convert --src /path/to/source --out /path/to/output`.
Keep original recordings and credentials out of Git.

## 2. Aggregate releases

From the repository root, place completed outputs under
`publish/data/<recipe-directory-name>/<version>/`. For example:

```bash
mkdir -p publish/data/pereira-2025-bids/1.0.0
cp -a work/pereira-2025-bids/. publish/data/pereira-2025-bids/1.0.0/
```

`work/` and `publish/` are gitignored. Preserve each dataset's layout, license,
attribution, and source provenance. Exclude download-cache indexes and partial
files. Validate the complete release and add `release.json` plus a
`dataset_index.json` containing relative paths, sizes, and SHA-256 hashes.
**Shared release finalization is not yet implemented; do not publish unvalidated
outputs.** Published versions are immutable; corrections get a new version.

## 3. Upload to S3

Install the [AWS CLI](https://aws.amazon.com/cli/) and configure an upload profile.
Set the actual bucket URI and region, then review the dry run:

```bash
export BUCKET=s3://YOUR-BUCKET
export AWS_REGION=YOUR-REGION
aws s3 sync publish/ "$BUCKET/" --exclude '*/dataset_index.json' --dryrun
```

After validation and review, repeat without `--dryrun`. Verify uploaded file
contents and anonymous access before uploading the checksum indexes last:

```bash
aws s3 cp publish/ "$BUCKET/" --recursive \
  --exclude '*' --include '*/dataset_index.json'
```

Do not use `--delete` or wrap releases in ZIP/TAR archives. Uploading to S3 is not
atomic; advertise a release only after its files and index have been verified.

## Licensing

[LICENSE](LICENSE) covers code only. Data retains its per-recipe license; cite the
original papers and datasets, and ConfUSIus when using its tooling.
