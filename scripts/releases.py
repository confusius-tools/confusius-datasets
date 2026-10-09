"""Generate manifests, publish verified S3 releases, and update the latest catalog."""

import argparse
import configparser
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory


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
    catalog_path(release)
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


def catalog_path(release: Path) -> Path:
    category = release.parent.parent
    publish = category.parent
    if publish.name != "publish" or category.name not in {"datasets", "templates"}:
        raise ValueError("Expected publish/{datasets,templates}/<recipe>/<version>/")
    if not all(
        re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", value)
        for value in (release.parent.name, release.name)
    ):
        raise ValueError("Invalid recipe or version name")
    destination = publish / "last_versions.conf"
    if destination.is_symlink():
        raise ValueError("Latest-version catalog must not be a symlink")
    return destination


def read_manifest(release: Path) -> dict:
    manifest_path = release / "manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("Generate the release manifest first")
    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(entries, dict) or not entries or not all(
        isinstance(path, str) and path not in {"", ".", "manifest.json"}
        and Path(path).as_posix() == path
        and not Path(path).is_absolute() and ".." not in Path(path).parts
        and isinstance(info, dict) and type(info.get("size")) is int
        and info["size"] >= 0 and isinstance(info.get("sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", info["sha256"])
        for path, info in entries.items()
    ):
        raise ValueError("Release manifest must contain relative paths, sizes, and SHA-256 hashes")
    return entries


def latest(release: Path) -> None:
    destination = catalog_path(release)
    read_manifest(release)
    category = release.parent.parent
    name, version = release.parent.name, release.name
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


def verify_files(root: Path, entries: dict, *, local: bool = False) -> None:
    """Check the exact inventory and streamed hashes, rejecting symlinks.

    Offline self-check: matching data passes; corruption and extra files fail.

    >>> with TemporaryDirectory() as directory:
    ...     root = Path(directory)
    ...     data = root / "data.bin"
    ...     _ = data.write_bytes(b"abc")
    ...     entries = {"data.bin": {"size": 3, "sha256": hashlib.sha256(b"abc").hexdigest()}}
    ...     verify_files(root, entries)
    ...     _ = data.write_bytes(b"bad")
    ...     try:
    ...         verify_files(root, entries)
    ...     except ValueError as error:
    ...         print(error)
    ...     _ = data.write_bytes(b"abc")
    ...     _ = (root / "extra").write_bytes(b"")
    ...     try:
    ...         verify_files(root, entries)
    ...     except ValueError as error:
    ...         print(error)
    SHA-256 mismatch: data.bin
    File inventory differs: missing=[], extra=['extra']
    """
    files = set()
    for path in root.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError(f"Not a regular file or directory: {path}")
        if path.is_file():
            files.add(path.relative_to(root).as_posix())
    if local:
        files.discard("manifest.json")
    if files != entries.keys():
        raise ValueError(
            f"File inventory differs: missing={sorted(entries.keys() - files)}, "
            f"extra={sorted(files - entries.keys())}"
        )
    for name, expected in entries.items():
        path = root / name
        if path.stat().st_size != expected["size"]:
            raise ValueError(f"Size mismatch: {name}")
        with path.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        if digest != expected["sha256"]:
            raise ValueError(f"SHA-256 mismatch: {name}")


def aws(*args: str) -> str:
    return subprocess.run(
        ["aws", "--region", "us-west-2", "--output", "json", *args],
        check=True, capture_output=True, text=True,
    ).stdout


def remote_exists(bucket: str, key: str) -> bool:
    response = json.loads(aws(
        "s3api", "list-objects-v2", "--bucket", bucket,
        "--prefix", key, "--max-keys", "1",
    ))
    return any(item["Key"] == key for item in response.get("Contents", []))


def publish(release: Path, *, upload: bool = False) -> None:
    destination = catalog_path(release)
    entries = read_manifest(release)
    verify_files(release, entries, local=True)
    manifest_path = release / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    bucket = "confusius-datasets"
    prefix = release.relative_to(destination.parent).as_posix()
    manifest_key = f"{prefix}/manifest.json"
    remote = f"s3://{bucket}/{prefix}/"
    published = remote_exists(bucket, manifest_key)
    with TemporaryDirectory(prefix="confusius-publish-") as directory:
        temporary = Path(directory)
        downloaded_manifest = temporary / "manifest.json"
        if published:
            aws(
                "s3api", "get-object", "--bucket", bucket, "--key", manifest_key,
                str(downloaded_manifest), "--no-sign-request",
            )
            if downloaded_manifest.read_bytes() != manifest_bytes:
                raise ValueError("Published manifest differs; use a new release version")
            print("Already published: files will not be overwritten; verify and promote only.")
        if not upload:
            if not published:
                print(aws(
                    "s3", "sync", str(release) + "/", remote,
                    "--exclude", "manifest.json", "--dryrun",
                ), end="")
            print("Preview only. Use --upload to verify and publish the manifest and catalog.")
            return
        # shortcut: one publisher at a time; add locking before concurrent publication.
        if not published:
            print(aws(
                "s3", "sync", str(release) + "/", remote, "--exclude", "manifest.json",
            ), end="")
        downloaded = temporary / "files"
        downloaded.mkdir()
        print(aws(
            "s3", "sync", remote, str(downloaded) + "/",
            "--exclude", "manifest.json", "--no-sign-request",
        ), end="")
        verify_files(downloaded, entries)
        print("Release files verified through anonymous download.")
        if not published:
            aws(
                "s3api", "put-object", "--bucket", bucket, "--key", manifest_key,
                "--body", str(manifest_path), "--content-type", "application/json",
                "--if-none-match", "*",
            )
            aws(
                "s3api", "get-object", "--bucket", bucket, "--key", manifest_key,
                str(downloaded_manifest), "--no-sign-request",
            )
            if downloaded_manifest.read_bytes() != manifest_bytes:
                raise ValueError("Uploaded manifest differs; catalog was not promoted")
        downloaded_catalog = temporary / "last_versions.conf"
        if remote_exists(bucket, "last_versions.conf"):
            aws(
                "s3api", "get-object", "--bucket", bucket, "--key", "last_versions.conf",
                str(downloaded_catalog),
            )
            catalog_text = downloaded_catalog.read_text(encoding="utf-8")
        else:
            catalog_text = ""
        write_atomic(destination, catalog_text)
        latest(release)
        aws(
            "s3api", "put-object", "--bucket", bucket, "--key", "last_versions.conf",
            "--body", str(destination), "--content-type", "text/plain",
        )
        aws(
            "s3api", "get-object", "--bucket", bucket, "--key", "last_versions.conf",
            str(downloaded_catalog), "--no-sign-request",
        )
        if downloaded_catalog.read_bytes() != destination.read_bytes():
            raise ValueError("Uploaded catalog differs; check for another publisher")
        print(f"Published and promoted: {remote}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("manifest", "latest", "publish"))
    parser.add_argument("release", type=Path, help="Versioned release directory")
    parser.add_argument("--upload", action="store_true", help="Publish to S3 instead of previewing")
    args = parser.parse_args()
    if args.upload and args.command != "publish":
        parser.error("--upload is only valid with publish")
    if args.release.is_symlink() or not args.release.is_dir():
        parser.error("Release must be an existing directory, not a symlink")
    release = args.release.resolve()
    try:
        if args.command == "publish":
            publish(release, upload=args.upload)
        else:
            (manifest if args.command == "manifest" else latest)(release)
    except subprocess.CalledProcessError as error:
        parser.exit(1, f"AWS CLI failed: {error.stderr.strip()}\n")
    except (OSError, ValueError, configparser.Error) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
