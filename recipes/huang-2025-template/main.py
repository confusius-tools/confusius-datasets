from __future__ import annotations

from pathlib import Path

import confusius as cf

ROOT = Path(__file__).parent
OUTPUTS = ROOT / "outputs"

SOURCE_VASCULAR = ROOT / "inputs" / "OFUSA_Atlas_Mouse_Vascular.nii"

OUTPUT_VASCULAR = OUTPUTS / "huang-2025-space-allen50_desc-vascular.nii.gz"


def export_vascular(source_path: Path = SOURCE_VASCULAR) -> Path:
    atlas = cf.atlas.Atlas.from_brainglobe("allen_mouse_50um")

    template = cf.load(source_path)
    if "time" in template.dims:
        template = template.squeeze("time", drop=True)

    transformed = (
        template.rename({"x": "y", "y": "z", "z": "x"})
        .transpose("z", "y", "x")
        .assign_coords(atlas.reference.coords)
    )

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    cf.save(transformed, OUTPUT_VASCULAR)
    return OUTPUT_VASCULAR


def main() -> None:
    out = export_vascular()
    loaded = cf.load(out)
    print(out)
    print(f"dims={loaded.dims} shape={loaded.shape}")


if __name__ == "__main__":
    main()
