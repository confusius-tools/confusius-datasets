# ConfUSIus datasets

Conversion and publication recipes for the curated functional ultrasound imaging
(fUSI) datasets and templates distributed through [ConfUSIus](https://confusius.tools).
This repository contains tooling and supplemental recipe inputs, not the generated
dataset collection.

## Recipes

| Recipe | Content | Data license |
| --- | --- | --- |
| [Nunez-Elizalde 2022](recipes/nunez-elizalde-2022-bids/) | Convert recordings, metadata, events, and alignment derivatives to fUSI-BIDS | CC BY 4.0 |
| [Landemard 2026](recipes/landemard-2026-bids/) | Stage an existing fUSI-BIDS dataset; no conversion required | CC BY-NC 4.0 |
| [Cybis Pereira 2026](recipes/cybis-pereira-2026-bids/) | Re-export recordings and derivatives with layout and orientation changes | CC BY 4.0 |
| [Pereira 2025](recipes/pereira-2025-bids/) | Re-export 2D recordings with layout and orientation changes | CC BY 4.0 |
| [Pepe Mariani 2026 recordings](recipes/pepe-mariani-2026-bids/) | Re-export recordings with layout, geometry, metadata, and timing corrections | CC BY 4.0 |
| [Pepe Mariani 2026 template](recipes/pepe-mariani-2026-template/) | Export an Allen-aligned fUSI template | CC BY 4.0 |
| [Huang 2025 template](recipes/huang-2025-template/) | Export an Allen-aligned vascular template | CC BY-NC-SA 4.0 |

Each recipe documents its original publication, source data, supplemental inputs,
and conversion procedure. See [IMPORTS.md](IMPORTS.md) for source repositories and
exact imported commits.

## Running a recipe

Recipes retain independent Python environments and lockfiles. Run commands from
inside the corresponding recipe directory, using the instructions in its README:

```bash
cd recipes/pereira-2025-bids
uv sync --locked
uv run --locked pereira-convert --src /path/to/source --out /path/to/output_bids
```

Keep original recordings outside this repository. Recipe inputs already tracked in
Git are retained for reproducibility; do not commit downloaded datasets, generated
outputs, virtual environments, or credentials.

## S3 migration status

The initial import preserves recipe files byte-for-byte, including the legacy OSF
upload code. Import verification does not establish that each converter runs with
current ConfUSIus. AWS publication is not yet configured, and the existing OSF
copies remain the download source for ConfUSIus.

The planned publication layout is:

```text
publish/
├── README.md
└── data/
    └── <dataset-id>/
        └── <version>/
            ├── <dataset files>
            ├── LICENSE
            ├── release.json
            └── dataset_index.json
```

`publish/` is gitignored and will mirror `s3://<bucket>/` exactly. Dataset identifiers
match the recipe directory names. Releases are versioned independently of the
ConfUSIus package and are immutable after publication.

Migration proceeds in this order:

1. Import the seven recipes unchanged and record their provenance (complete).
2. Validate conversion behavior in the locked environments.
3. Standardize output paths and add shared release finalization and checksums.
4. Publish and verify one small template using the AWS CLI.
5. Publish the remaining datasets and migrate ConfUSIus fetchers to public HTTPS.
6. Update documentation, the tutorial, and the AWS Registry entry.
7. Archive the original repositories and remove legacy OSF upload tooling here.

Conversion and upload remain separate actions. Publish only validated releases,
upload their indexes last, and do not use `aws s3 sync --delete`. No `latest/` data
copy is planned. The bucket name, region, and tested releases will be documented
before publication.

Khallaf 2026 is not part of this initial seven-recipe migration; its existing
ConfUSIus Dataverse fetcher remains unchanged.

## Licensing and attribution

The root [LICENSE](LICENSE) applies to code, not to the dataset collection. Imported
recipe licenses and copyright notices are preserved in their original locations.
Data and supplemental inputs retain their respective source terms; see each
recipe's `licenses/DATA_LICENSE.md` and source documentation. Do not apply a single
code or data license to the entire collection.

Cite the original publications and datasets when using their data, and ConfUSIus
when using its access tooling. Non-commercial and share-alike restrictions must be
preserved where applicable. Confirm redistribution rights for supplemental inputs
and AWS acceptance of restricted licenses before publishing releases.
