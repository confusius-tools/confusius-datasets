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
repository root. Recipes that use ConfUSIus temporarily depend on its Git `main`
branch until `0.8.0` is released. Their lockfiles pin the exact commit, and the
`just` commands use `--locked` for reproducible conversions. After the release,
switch those dependencies to `confusius>=0.8.0` and remove their Git source entries.

```bash
just                                            # List recipes.
just pereira-2025 /path/to/source               # Prepare recordings.
just pereira-2025 /path/to/source --dry-run     # Preview conversion.
just khallaf-2026                               # Download and update datatype paths.
just template-huang-2025                        # Export a bundled template.
```

Outputs go to:

- Recordings: `publish/datasets/<recipe-directory-name>/<version>/`
- Templates: `publish/templates/<recipe-directory-name>/<version>/`

The version comes from each recipe's `pyproject.toml`. Recording converters and
staging scripts accept `--out` to override the destination. Landemard copies an
existing BIDS tree into a fresh destination. Landemard and Khallaf update legacy
`angio/` datatype folders to `susi/`, including scan-table and JSON references.
Dataset sidecars use the v0.0.14 frequency/voltage field names and omit the redundant
`PowerDopplerIntegrationStride`. Nunez-generated processing windows are expressed
in milliseconds; acquisition timestamps and frame durations remain in seconds.
Other recipes preserve the units supplied by their source sidecars.

## 2. Generate a release manifest

After a recipe finishes, review its output and generate its file inventory:

```bash
export RELEASE=publish/datasets/pereira-2025-bids/1.0.0
just manifest "$RELEASE"
```

This writes `<release-directory>/manifest.json`, mapping relative paths to byte
sizes and SHA-256 hashes. Each dataset/template version has its own manifest;
pass the version directory, not its parent recipe directory. The shared [release script](scripts/releases.py) streams file contents,
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

Install the [AWS CLI](https://aws.amazon.com/cli/) and authenticate as a publisher
with upload access to `s3://confusius-datasets`. For a console-enabled IAM publisher
with the `SignInLocalDevelopmentAccess` policy, use a local AWS CLI profile of
your choice (the profile name is not an IAM username):

```bash
export AWS_PROFILE=your-publisher-profile
aws login --profile "$AWS_PROFILE" --region us-west-2
```

The shared publishing command targets this bucket in US West (Oregon), `us-west-2`,
and preserves the release's path under `publish/`. Review the preview, then upload:

```bash
just publish "$RELEASE"             # Preview only; no remote or local writes.
just publish "$RELEASE" --upload    # Upload, verify, and mark this version latest.
```

The command checks that local files match their manifest before contacting S3.
It uploads release files, downloads them anonymously into a temporary directory,
and checks the exact inventory, sizes, and SHA-256 hashes. Allow enough temporary
disk space for another copy of the release; verification downloads every file.
Only after verification does it upload and anonymously verify the manifest.

Finally it fetches the current remote `last_versions.conf`, preserves its other
entries, updates this recipe's version, and uploads and anonymously verifies the
catalog last. The remote catalog is authoritative: if none exists, publication
starts a new catalog rather than using stale local entries. Authentication,
permission, and network errors stop publication; they are not treated as a missing
catalog.

Published release files are never overwritten. If a remote manifest exists and
differs from the local one, publication stops. If it matches, `--upload` only
verifies the existing release and promotes its catalog entry. This also lets you
retry after a catalog update fails. Incomplete uploads without a manifest can be
resumed; unexpected remote files fail verification and are not silently deleted.

`last_versions.conf` has separate `[datasets]` and `[templates]` sections mapping
recipe names to versions. Use one publisher at a time and do not modify local
release files during publication. Uploading to S3 is not atomic; interrupted
uploads can leave files or a manifest present without a catalog entry.

`just latest "$RELEASE"` remains available for local-only catalog edits; it does
not upload or verify S3. Do not use `--delete` or wrap releases in ZIP/TAR archives.

## Licensing

[LICENSE](LICENSE) covers code only. Data retains its per-recipe license; cite the
original papers and datasets, and ConfUSIus when using its tooling.
