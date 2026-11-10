# Sample beamformed IQ

- `sub-ALD019_task-awake_acq-ref25_iq.zarr`: 2D+t beamformed IQ recording
  from subject ALD019, awake acquisition ref25. The Zarr v3 store contains
  complex64 IQ data with dimensions `(time, k, j, i)` and a singleton `k`
  dimension, along with acquisition and spatial metadata.

The recording originates from Landemard et al. (2026),
[Brainwide blood volume reflects opposing neural populations](https://doi.org/10.1038/s41586-026-10350-9).
The associated dataset is [doi:10.5522/04/31376338](https://doi.org/10.5522/04/31376338).
To obtain the original IQ recording, contact the first author, Agnès Landemard.

Data license: [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
Please cite the original dataset and paper.
