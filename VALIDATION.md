# Migration validation

## Scope

These are baseline checks for the imported recipes, not certification of complete
published datasets. Nothing has been uploaded to S3, and no source repository,
original recording, or existing generated dataset has been modified.

## Import preservation

The initial commit `cf86df30bd1c676f8c492a834df9f6173e14cf12` contains all 184 tracked
recipe files from the commits recorded in the
[initial import record](https://github.com/confusius-tools/confusius-datasets/blob/cf86df30bd1c676f8c492a834df9f6173e14cf12/IMPORTS.md).
File names, bytes, Git blob hashes, and file modes were checked against the original
checkouts.
Generated dataset directories were excluded. Three existing README trailing-space
lines were intentionally retained in that snapshot.

## Locked environments

All seven recipes now pass `uv sync --locked --python 3.13` on this Linux host.

| Recipe | Locked ConfUSIus | Conversion check |
| --- | --- | --- |
| `nunez-elizalde-2022-bids` | `0.0.1a23` | Conversion CLI starts; real recording conversion remains to be checked |
| `landemard-2026-bids` | `0.4.0` | Environment installs; no conversion is required, but the staged dataset remains to be validated |
| `cybis-pereira-2026-bids` | `0.5.0.dev0` at Git commit `00133de125972bdd273c0bbb66ac1b1cfc56cefc` | Synthetic NIfTI reference check passes |
| `pereira-2025-bids` | Not required by this converter | Synthetic NIfTI reference check and inherited checks pass |
| `pepe-mariani-2026-bids` | Not required by this converter | Synthetic NIfTI reference check passes |
| `pepe-mariani-2026-template` | `0.0.1a25` | Export using bundled inputs passes |
| `huang-2025-template` | `0.2.0` | Export using bundled input and cached Allen 50 um atlas passes |

### Huang lockfile repair

The imported Huang `pyproject.toml` names the project `huang-2025-template`, but its
lockfile still named the root package `huang-2026-template`. This caused
`uv sync --locked` to fail before installation. The root package name was corrected
in the new repository only; all dependency versions and hashes remain unchanged.
The same locked installation then passed. The original checkout is unchanged.

## Runnable reference checks

Run these from the repository root:

```bash
for recipe in recipes/*; do
  uv sync --locked --python 3.13 --directory "$recipe"
done

for recipe in pereira-2025-bids pepe-mariani-2026-bids cybis-pereira-2026-bids; do
  uv run --locked --python 3.13 --directory "recipes/$recipe" \
    python ../../tests/check_recording_conversion.py "$recipe"
done

for recipe in huang-2025-template pepe-mariani-2026-template; do
  uv run --locked --python 3.13 --directory "recipes/$recipe" \
    python ../../tests/check_template_export.py "$recipe"
done

uv run --locked --python 3.13 --directory recipes/pereira-2025-bids \
  python tests/test_converter.py
```

The recording checks exercise the public `convert` entry points with small,
deterministic inputs. They compare voxel values against explicit permutations and
check destination paths, metadata copying, units, and source preservation. Pereira
and Pepe Mariani also compare output affines to reference matrices and preserve
qform/sform codes. The Pepe Mariani check verifies the repetition-time correction.
These checks do not cover every acquisition, chunk-timing case, derivative, or
metadata variant in the full releases.

The template checks compare all exported voxel values with the intended source
permutations and confirm the source files are unchanged. Huang also matches the
cached Allen atlas coordinates. Export files are written to temporary directories
and removed after the checks. The Huang source has no qform/sform codes and emits an
expected warning before its output geometry is assigned from the atlas.

Both actual template exports were separately loaded using the current ConfUSIus
checkout (`0.8.0.dev0`): `validate_voxeldata` passed, and voxel values matched the
NIfTI arrays. Local baseline exports are retained under the gitignored
`work/validation/` directory. This confirms current-loader compatibility, not an
independent anatomical validation of the Pepe Mariani registration.

The new check scripts pass Ruff formatting and lint checks in the locked Pereira
environment. The imported converter source was not reformatted or upgraded.

## Before publication

- Validate a real Nunez-Elizalde conversion and the complete staged datasets.
- Standardize destination arguments for the template exporters.
- Reject incomplete or stale conversion outputs during release finalization.
- Include licenses, attribution, sanitized provenance, sizes, and SHA-256 hashes.
- Resolve the Huang filename discrepancy: the recipe exports `huang-2025-...`,
  while the current ConfUSIus OSF fetcher expects `huang-2026-...`.
- Obtain the bucket name and region, verify upload credentials and public reads,
  and confirm redistribution rights and accepted license restrictions.
- Migrate consumers before retiring OSF upload code or archiving source repositories.
