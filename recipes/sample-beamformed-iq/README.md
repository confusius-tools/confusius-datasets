# Sample beamformed IQ

Stage a sample 2D+t beamformed IQ recording from the Landemard *et al.* (2026) article
"Brainwide blood volume reflects opposing neural populations" for release on S3. The
recipe copies the Zarr store unchanged into a fresh versioned release; it does not
upload or generate an index.

The sample is a Zarr v3 conversion of the ALD019 awake ref25 recording used in the
ConfUSIus paper's Figure 2. It contains complex64 IQ data with dimensions `(time, k, j,
i)` and a singleton `k` dimension. Acquisition and spatial metadata are stored in the
Zarr attributes. To obtain the original IQ recording, contact the first author, Agnès
Landemard.

## References

- Original dataset: [doi:10.5522/04/31376338](https://doi.org/10.5522/04/31376338)
- Paper: [doi:10.1038/s41586-026-10350-9](https://doi.org/10.1038/s41586-026-10350-9)
- Original analysis code: [github.com/agneslandemard/fusi_analyses](https://github.com/agneslandemard/fusi_analyses)

## Usage

Place `sub-ALD019_task-awake_acq-ref25_iq.zarr` in `work/sample-beamformed-iq/` (ignored
by Git), then run from the repository root:

```bash
just sample-beamformed-iq
```

Or provide a source path with `just sample-beamformed-iq /path/to/store.zarr`. From this
recipe directory, use `uv run --locked main.py /path/to/store.zarr`. The default
destination is `<repository>/publish/datasets/sample-beamformed-iq/<version>/`, using
the version from `pyproject.toml` (initially `1.0.0`). `--out` overrides it; existing
destinations are rejected. If staging fails, remove the incomplete release before
retrying. See the root README for S3 publication.

The store is approximately 79 GiB; allow space for the staged copy and the
publisher's additional verification download.

## Licensing

- **Code license:** [BSD-3-Clause](https://github.com/confusius-tools/confusius-datasets/blob/main/LICENSE)
- **Data license:** [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

Cite the original dataset and paper when using or redistributing the recording.
