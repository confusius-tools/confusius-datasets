"""Generate release manifests and explicitly update the latest-version catalog."""

import argparse
import configparser
import hashlib
import io
import json
import re
from pathlib import Path
from tempfile import NamedTemporaryFile


def write_atomic(path: Path, text: str) -> None:
    temporary = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as output:
            temporary = Path(output.name)
            output.write(text)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def manifest(release: Path) -> None:
    paths = []
    for path in sorted(release.rglob("*")):
        relative = path.relative_to(release)
        if path.is_symlink():
            raise ValueError(f"Symlink in release: {relative}")
        if any(
            part in {
                ".git", ".aws", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache",
                "credentials", "id_rsa", "id_ed25519", "conversion_manifest.tsv",
            }
            or part.startswith(".env")
            or part.lower().endswith((".tmp", ".part", ".partial", ".pem", ".key", "~"))
            for part in relative.parts
        ):
            raise ValueError(f"Temporary, credential, or stale file in release: {relative}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f"Not a regular file: {relative}")
        if relative == Path("manifest.json"):
            continue
        paths.append(path)
    if not paths or paths == [release / ".bidsignore"]:
        raise ValueError("Release has no data files")
    if release.parent.parent.name == "datasets":
        bidsignore = release / ".bidsignore"
        if bidsignore.exists():
            rules = bidsignore.read_text(encoding="utf-8")
        else:
            rules = ""
            paths.append(bidsignore)
        if "manifest.json" not in (line.strip() for line in rules.splitlines()):
            if rules and not rules.endswith("\n"):
                rules += "\n"
            write_atomic(bidsignore, rules + "manifest.json\n")
    files = {}
    for path in paths:
        with path.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        files[path.relative_to(release).as_posix()] = {"size": path.stat().st_size, "sha256": digest}
    destination = release / "manifest.json"
    write_atomic(destination, json.dumps(files, indent=2, sort_keys=True) + "\n")
    print(destination)


def latest(release: Path) -> None:
    category = release.parent.parent
    publish = category.parent
    name, version = release.parent.name, release.name
    if publish.name != "publish" or category.name not in {"datasets", "templates"}:
        raise ValueError("Expected publish/{datasets,templates}/<recipe>/<version>/")
    if not all(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", value) for value in (name, version)):
        raise ValueError("Invalid recipe or version name")
    manifest_path = release / "manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("Generate the release manifest before updating latest")
    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(entries, dict) or not entries or not all(
        isinstance(path, str) and path != "manifest.json"
        and not Path(path).is_absolute() and ".." not in Path(path).parts
        and isinstance(info, dict) and type(info.get("size")) is int
        and info["size"] >= 0 and isinstance(info.get("sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", info["sha256"])
        for path, info in entries.items()
    ):
        raise ValueError("Release manifest must contain relative paths, sizes, and SHA-256 hashes")
    destination = publish / "last_versions.conf"
    if destination.is_symlink():
        raise ValueError("Latest-version catalog must not be a symlink")
    # shortcut: assumes one publisher; use conditional updates if concurrent publishing is needed.
    catalog = configparser.ConfigParser(interpolation=None)
    catalog.optionxform = str
    if destination.exists():
        with destination.open(encoding="utf-8") as source:
            catalog.read_file(source)
    if not catalog.has_section(category.name):
        catalog.add_section(category.name)
    catalog.set(category.name, name, version)
    output = io.StringIO()
    catalog.write(output)
    write_atomic(destination, output.getvalue())
    print(destination)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("manifest", "latest"))
    parser.add_argument("release", type=Path, help="Versioned release directory")
    args = parser.parse_args()
    if args.release.is_symlink() or not args.release.is_dir():
        parser.error("Release must be an existing directory, not a symlink")
    release = args.release.resolve()
    try:
        (manifest if args.command == "manifest" else latest)(release)
    except (OSError, ValueError, configparser.Error) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
