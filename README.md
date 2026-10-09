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

## Source downloads

These are the original inputs, not the converted AWS releases. Download and unpack
before running a recipe, except Khallaf (downloaded automatically) and the templates
(inputs already bundled). Links below identify the specific source files used.

| Dataset | Source record | Download |
| --- | --- | --- |
| Nunez-Elizalde 2022 | [Figshare](https://doi.org/10.6084/m9.figshare.19316228) | [dataset.zip](https://ndownloader.figshare.com/files/34307132) |
| Landemard 2026 | [UCL Figshare](https://doi.org/10.5522/04/31376338) | [Subject ZIPs and root metadata](#landemard-source-files) |
| Khallaf 2026 | [Edmond](https://doi.org/10.17617/3.7QCU1F) | [fUSI dataset.zip](https://edmond.mpg.de/api/access/datafile/343674) |
| Cybis Pereira 2026 | [Zenodo record 15476373](https://zenodo.org/records/15476373) | [dataset.zip](https://zenodo.org/api/records/15476373/files/dataset.zip/content) |
| Pereira 2025 | [Zenodo record 15194839](https://zenodo.org/records/15194839) | [rawdata.zip](https://zenodo.org/api/records/15194839/files/rawdata.zip/content) |
| Pepe Mariani 2026 recordings | [Zenodo record 20070510](https://zenodo.org/records/20070510) | [2026-02-03_PepeMariani_fUSI-anaesthetised.zip](https://zenodo.org/api/records/20070510/files/2026-02-03_PepeMariani_fUSI-anaesthetised.zip/content) |

### Landemard source files

Extract these five archives into one BIDS root, alongside the root metadata below;
pass that directory to `just landemard-2026`:

- [sub-ALD001.zip](https://ndownloader.figshare.com/files/63929310)
- [sub-ALD002.zip](https://ndownloader.figshare.com/files/63929292)
- [sub-ALD009.zip](https://ndownloader.figshare.com/files/63929304)
- [sub-ALD010.zip](https://ndownloader.figshare.com/files/63929301)
- [sub-ALD019.zip](https://ndownloader.figshare.com/files/63929295)
- Root metadata: [dataset_description.json](https://ndownloader.figshare.com/files/63929163),
  [participants.json](https://ndownloader.figshare.com/files/63929166),
  [participants.tsv](https://ndownloader.figshare.com/files/63929172),
  [README.txt](https://ndownloader.figshare.com/files/63929169).

Additional analysis `.npz` downloads are available from the source record.

### Bundled template inputs

- Huang 2025: [OFUSA_Atlas_Mouse_Vascular.nii](recipes/huang-2025-template/inputs/OFUSA_Atlas_Mouse_Vascular.nii).
- Pepe Mariani 2026: [source template](recipes/pepe-mariani-2026-template/inputs/published_params/source-BI_space-fUSI_desc-GillianTemplate_res-110umx100umx100um_feature.nii.gz)
  from [Zenodo record 18486493](https://zenodo.org/records/18486493)
  ([source archive](https://zenodo.org/api/records/18486493/files/2026-02-03_PepeMariani_fUSI-anaesthetised.zip/content)),
  plus the [registration transform supplied by the authors](recipes/pepe-mariani-2026-template/inputs/registration/transform_Affine_AllenPIRRAS100um-2-fUSIPIRRAS_Composite.h5).

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

Each recipe writes directly to its versioned release directory:

- Recordings: `publish/datasets/<recipe-directory-name>/<version>/`
- Templates: `publish/templates/<recipe-directory-name>/<version>/`

The version comes from its own `pyproject.toml` (initially `1.0.0`). This default
lives in the Python scripts, so direct runs use the same location regardless of
working directory. Recording converters and staging scripts accept `--out` to
override it. See the linked READMEs for source inputs. Landemard copies an existing
BIDS tree into a fresh destination; templates use bundled inputs.

`uv run` creates and syncs each environment automatically; no separate `uv sync`
is needed. Recipe `.python-version` files select Python 3.13. `--locked` prevents
silent lockfile changes; update dependencies explicitly with `uv lock` when needed.
You can also run commands directly inside a recipe directory, e.g.
`uv run --locked pereira-convert --src /path/to/source --out /path/to/output`.
Keep original recordings and credentials out of Git.

## 2. Validate releases

No aggregation copy is needed: recipes already write to their versioned release
directories. Bump a recipe's project version and update its lockfile before
preparing a new release. Existing `work/` and old `publish/data/` outputs are not
migrated automatically; move or remove old outputs before syncing `publish/` to S3.
Khallaf keeps its download archive in `work/`, separate from release data.

`work/` and `publish/` are gitignored. Preserve each dataset's layout, license,
attribution, and source provenance. Exclude download-cache indexes and partial
files. Validate the complete release and add `release.json` plus a
`dataset_index.json` containing relative paths, sizes, and SHA-256 hashes.
**Shared release finalization is not yet implemented; do not publish unvalidated
outputs.** Do not upload while recipes are running. Published versions are
immutable; corrections get a new version. Converters may skip existing files, so
do not rerun into an already published version.

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
