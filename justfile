set positional-arguments

# List available dataset recipes.
default:
    @just --list

# Convert Nunez-Elizalde recordings; extra arguments go to the converter.
nunez-elizalde-2022 src *args:
    src="$1"; shift; uv run --locked --project recipes/nunez-elizalde-2022-bids nunez-convert --src "$src" --out work/nunez-elizalde-2022-bids "$@"

# Stage the existing Landemard BIDS tree without conversion.
landemard-2026 src:
    test -d "$1"
    mkdir -p work/landemard-2026-bids
    cp -a -- "$1/." work/landemard-2026-bids/

# Download the complete Khallaf fUSI archive from Edmond.
khallaf-2026 *args:
    uv run --locked --project recipes/khallaf-2026-bids recipes/khallaf-2026-bids/main.py "$@"

# Re-export Cybis Pereira recordings; extra arguments go to the converter.
cybis-pereira-2026 src *args:
    src="$1"; shift; uv run --locked --project recipes/cybis-pereira-2026-bids cybis-convert --src "$src" --out work/cybis-pereira-2026-bids "$@"

# Re-export Pereira recordings; extra arguments go to the converter.
pereira-2025 src *args:
    src="$1"; shift; uv run --locked --project recipes/pereira-2025-bids pereira-convert --src "$src" --out work/pereira-2025-bids "$@"

# Re-export Pepe Mariani recordings; extra arguments go to the converter.
pepe-mariani-2026 src *args:
    src="$1"; shift; uv run --locked --project recipes/pepe-mariani-2026-bids pepe-mariani-convert --src "$src" --out work/pepe-mariani-2026-bids "$@"

# Export and stage the Pepe Mariani template from bundled inputs.
template-pepe-mariani-2026:
    uv run --locked --project recipes/pepe-mariani-2026-template recipes/pepe-mariani-2026-template/main.py
    mkdir -p work/pepe-mariani-2026-template
    cp -a -- recipes/pepe-mariani-2026-template/outputs/pepe-mariani-2026-fusi-template.nii.gz work/pepe-mariani-2026-template/

# Export and stage the Huang template from its bundled input.
template-huang-2025:
    uv run --locked --project recipes/huang-2025-template recipes/huang-2025-template/main.py
    mkdir -p work/huang-2025-template
    cp -a -- recipes/huang-2025-template/outputs/huang-2025-space-allen50_desc-vascular.nii.gz work/huang-2025-template/
