set positional-arguments

# List available dataset recipes.
default:
    @just --list

# Convert Nunez-Elizalde recordings; extra arguments go to the converter.
nunez-elizalde-2022 src *args:
    src="$1"; shift; uv run --locked --project recipes/nunez-elizalde-2022-bids nunez-convert --src "$src" "$@"

# Stage the existing Landemard BIDS tree without conversion.
landemard-2026 src *args:
    uv run --locked --project recipes/landemard-2026-bids python recipes/landemard-2026-bids/main.py "$@"

# Download the complete Khallaf fUSI archive from Edmond.
khallaf-2026 *args:
    uv run --locked --project recipes/khallaf-2026-bids python recipes/khallaf-2026-bids/main.py "$@"

# Re-export Cybis Pereira recordings; extra arguments go to the converter.
cybis-pereira-2026 src *args:
    src="$1"; shift; uv run --locked --project recipes/cybis-pereira-2026-bids cybis-convert --src "$src" "$@"

# Re-export Pereira recordings; extra arguments go to the converter.
pereira-2025 src *args:
    src="$1"; shift; uv run --locked --project recipes/pereira-2025-bids pereira-convert --src "$src" "$@"

# Re-export Pepe Mariani recordings; extra arguments go to the converter.
pepe-mariani-2026 src *args:
    src="$1"; shift; uv run --locked --project recipes/pepe-mariani-2026-bids pepe-mariani-convert --src "$src" "$@"

# Export the Pepe Mariani template from bundled inputs.
template-pepe-mariani-2026:
    uv run --locked --project recipes/pepe-mariani-2026-template python recipes/pepe-mariani-2026-template/main.py

# Export the Huang template from its bundled input.
template-huang-2025:
    uv run --locked --project recipes/huang-2025-template python recipes/huang-2025-template/main.py

# Inventory a completed release and write its SHA-256 manifest.
manifest release:
    uv run --no-project --python 3.13 python scripts/releases.py manifest "$1"

# Preview publication; pass --upload to upload, verify, and promote a release.
publish release *args:
    uv run --no-project --python 3.13 python scripts/releases.py publish "$@"

# Mark a release latest only after its upload has been verified.
latest release:
    uv run --no-project --python 3.13 python scripts/releases.py latest "$1"
