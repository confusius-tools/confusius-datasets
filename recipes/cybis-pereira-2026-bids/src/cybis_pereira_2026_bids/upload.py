"""Upload a local BIDS directory to OSF and maintain a dataset index."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import cast

from osfclient.api import OSF
from osfclient.exceptions import UnauthorizedException
from osfclient.models.storage import File, Storage, checksum, file_empty
from requests.exceptions import RequestException
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

BIDS_ROOT_NAME = "cybis-pereira-2026-bids"
INDEX_FILENAME = "dataset_index.json"
CONSOLE = Console()
IndexEntry = dict[str, str | int | None]
DatasetIndex = dict[str, IndexEntry]
_RETRYABLE_KEYWORDS = (
    # OSF intermittently returns 400 on valid upload requests under load;
    # retrying the same request succeeds.
    "status code 400",
    "status code 403",
    "status code 404",
    "status code 408",
    "status code 429",
    "status code 500",
    "status code 502",
    "status code 503",
    "status code 504",
    "connection error",
    "timed out",
)


def _print_retry_message(
    context: str,
    attempt: int,
    max_attempts: int,
    wait_seconds: int,
    exc: Exception,
) -> None:
    CONSOLE.print(
        f"[bold yellow]Retryable OSF error[/] during {context} "
        f"[dim](attempt {attempt}/{max_attempts})[/dim]: {exc}. "
        f"Retrying in [bold]{wait_seconds}s[/]..."
    )


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, AttributeError) and "'NoneType'" in str(exc):
        return True

    # OSF raises UnauthorizedException on any 401, including the transient
    # throttling 401s it hands out during long listing walks. A genuinely bad
    # token simply exhausts the retries and surfaces the same error.
    if isinstance(exc, UnauthorizedException):
        return True

    msg = str(exc).lower()
    if isinstance(exc, RequestException):
        return True
    if not isinstance(exc, RuntimeError):
        return False
    return any(token in msg for token in _RETRYABLE_KEYWORDS)


def _response_error_detail(response) -> str:
    """Format a failed response for error messages.

    Keeps the literal ``status code <n>`` phrase that ``_is_retryable``
    matches on, and appends the response body so real 4xx causes (bad
    filename, malformed request) are distinguishable from transient ones.
    """
    detail = f"status code {response.status_code}"
    try:
        body = response.text.strip()
    except Exception:
        body = ""
    if len(body) > 500:
        body = body[:500] + "... [truncated]"
    if body:
        detail += f", response body: {body}"
    return detail


def _update_existing_file(existing: File, fp) -> None:
    """Overwrite a remote file, replacing ``File.update()`` from osfclient.

    osfclient's version raises without the response body, and its message
    reads ``status code: 400`` (with a colon) so ``_is_retryable`` never
    matched it -- transient update failures were surfacing instead of
    being retried.
    """
    if file_empty(fp):
        response = existing._put(existing._upload_url, data=b"")
    else:
        response = existing._put(existing._upload_url, data=fp)
    if response.status_code != 200:
        raise RuntimeError(
            f"Could not update {existing.path} ({_response_error_detail(response)})."
        )


def _get_storage(token: str, project_id: str) -> Storage:
    osf = OSF(token=token)
    project = osf.project(project_id)
    return project.storage()


def _get_storage_with_retry(
    token: str,
    project_id: str,
    max_attempts: int,
) -> Storage:
    for attempt in range(1, max_attempts + 1):
        try:
            return _get_storage(token, project_id)
        except Exception as exc:
            if attempt >= max_attempts or not _is_retryable(exc):
                raise
            wait_seconds = min(2 ** (attempt - 1), 30)
            time.sleep(wait_seconds)

    raise RuntimeError("Failed to connect to OSF storage after retries.")


def _create_bids_root_folder(storage: Storage) -> Storage:
    folder = storage.create_folder(BIDS_ROOT_NAME, exist_ok=True)
    if isinstance(getattr(folder, "_files_url", None), str):
        return folder

    # osfclient returns a slim WaterButler folder after creating a new folder;
    # re-resolve it through the OSF API so `.files` works for index lookup and
    # conflict handling, matching the object returned when the folder exists.
    for existing in storage.folders:
        if existing.name == BIDS_ROOT_NAME:
            return existing
    return folder


def _local_md5(local_path: Path, cache: dict[Path, str]) -> str:
    md5 = cache.get(local_path)
    if md5 is None:
        md5 = checksum(local_path)
        cache[local_path] = md5
    return md5


def _parse_index_entry(value: object) -> IndexEntry | None:
    if not isinstance(value, dict):
        return None
    value_dict = cast(dict[str, object], value)

    osf_path = value_dict.get("osf_path")
    if not isinstance(osf_path, str):
        return None

    raw_size = value_dict.get("size")
    size: int | None = (
        raw_size
        if isinstance(raw_size, int) and not isinstance(raw_size, bool)
        else None
    )

    raw_md5 = value_dict.get("md5")
    md5: str | None = raw_md5 if isinstance(raw_md5, str) else None

    return {"osf_path": osf_path, "size": size, "md5": md5}


def _load_remote_index(bids_root_folder: Storage) -> DatasetIndex:
    """Download and parse ``dataset_index.json`` (a single request).

    Returns an empty index if the file does not exist yet. Network errors are
    allowed to propagate so the caller can retry them. Unlike a missing file,
    a transient failure must not be silently read as "nothing is on OSF".
    """
    index_file: File | None = None
    for remote_file in bids_root_folder.files:
        if remote_file.name == INDEX_FILENAME:
            index_file = remote_file
            break

    if index_file is None:
        return {}

    response = index_file._get(index_file._download_url)
    if response.status_code != 200:
        raise RuntimeError(
            f"Could not download {INDEX_FILENAME} ({_response_error_detail(response)})."
        )
    payload = response.json()

    if not isinstance(payload, dict):
        return {}

    index: DatasetIndex = {}
    for key, value in payload.items():
        entry = _parse_index_entry(value)
        if entry is None:
            msg = (
                "Invalid dataset_index.json schema: expected each entry to be "
                "an object with {'osf_path': str, 'size': int | null, "
                "'md5': str | null}."
            )
            raise RuntimeError(msg)
        index[str(key)] = entry

    return index


def _backfill_md5_from_remote(storage: Storage, index: DatasetIndex) -> int:
    """Fill missing ``md5`` values in ``index`` from the remote file listing.

    OSF returns each file's md5 inline in the storage listing, so this is a
    single directory walk with no per-file requests and no file downloads. It
    is slow (OSF caps requests at 1/second) but only needed once, to populate
    hashes into an index written before md5 tracking existed. Returns the
    number of entries whose md5 was filled in.
    """
    prefix = BIDS_ROOT_NAME + "/"
    filled = 0
    for remote_file in storage.files:
        materialized = remote_file.path.lstrip("/")
        if not materialized.startswith(prefix):
            continue
        rel_path = materialized[len(prefix) :]
        if not rel_path or rel_path == INDEX_FILENAME:
            continue

        entry = index.get(rel_path)
        if entry is None or isinstance(entry.get("md5"), str):
            continue

        md5 = (getattr(remote_file, "hashes", None) or {}).get("md5")
        if not isinstance(md5, str):
            continue

        entry["md5"] = md5
        if not entry.get("osf_path"):
            entry["osf_path"] = remote_file.osf_path
        filled += 1

    return filled


def _ensure_parent_folder(
    rel_dir: str,
    folder_cache: dict[str, Storage],
) -> tuple[str, Storage]:
    if rel_dir in ("", "."):
        return "", folder_cache[""]

    current = ""
    for part in rel_dir.split("/"):
        parent = current
        current = f"{current}/{part}" if current else part
        if current not in folder_cache:
            folder_cache[current] = folder_cache[parent].create_folder(
                part,
                exist_ok=True,
            )
    return current, folder_cache[current]


def _short_path(path: str, max_len: int = 72) -> str:
    if len(path) <= max_len:
        return path
    return "..." + path[-(max_len - 3) :]


def _file_from_osf_path(session, osf_path: str | None) -> File | None:
    if not osf_path:
        return None
    file_id = osf_path.strip("/")
    if not file_id:
        return None

    response = session.get(f"https://api.osf.io/v2/files/{file_id}/")
    if response.status_code != 200:
        return None

    payload = response.json().get("data")
    if not isinstance(payload, dict):
        return None
    return File(payload, session)


def _file_from_folder_name(folder: Storage, filename: str) -> File | None:
    files_url = getattr(folder, "_files_url", None)
    if not isinstance(files_url, str):
        return None

    response = folder.session.get(files_url, params={"filter[name]": filename})
    if response.status_code != 200:
        return None

    data = response.json().get("data")
    if not isinstance(data, list):
        return None

    for item in data:
        attrs = item.get("attributes", {})
        if attrs.get("kind") == "file" and attrs.get("name") == filename:
            return File(item, folder.session)
    return None


def _get_folder_file_map(
    folder_key: str,
    folder: Storage,
    folder_file_cache: dict[str, dict[str, File]],
) -> dict[str, File]:
    cached = folder_file_cache.get(folder_key)
    if cached is None:
        cached = {remote_file.name: remote_file for remote_file in folder.files}
        folder_file_cache[folder_key] = cached
    return cached


def _upload_file_once(
    folder: Storage,
    folder_key: str,
    filename: str,
    local_path: Path,
    *,
    folder_file_cache: dict[str, dict[str, File]],
    local_md5_cache: dict[Path, str],
    known_osf_path: str | None,
    known_md5: str | None,
) -> tuple[str, str | None]:
    with open(local_path, "rb") as fp:
        # When the index already records this file's osf_path and md5,
        # reaching here means the local hash differs -- the file genuinely
        # changed. Update it directly instead of streaming the whole body once
        # just to receive a 409 and then stream it again. Requires a known md5
        # so we do not skip the remote-hash recheck below for entries whose
        # hash is unknown. Falls through to the create path if the file can no
        # longer be resolved (e.g. deleted since the index was read).
        if known_osf_path is not None and known_md5 is not None:
            existing = _file_from_osf_path(folder.session, known_osf_path)
            if existing is not None:
                # Compare against the LIVE remote hash, not the index one. A
                # previous attempt may have committed server-side even though
                # the client saw an error; updating again would stack another
                # file version on OSF (observed to corrupt a file record when
                # two such commits raced).
                remote_md5 = (existing.hashes or {}).get("md5")
                if remote_md5 and remote_md5 == _local_md5(local_path, local_md5_cache):
                    return "skipped", existing.osf_path
                fp.seek(0)
                _update_existing_file(existing, fp)
                return "uploaded", existing.osf_path

        if file_empty(fp):
            response = folder._put(
                folder._new_file_url,
                params={"name": filename},
                data=b"",
            )
        else:
            response = folder._put(
                folder._new_file_url,
                params={"name": filename},
                data=fp,
            )

        if response.status_code in (200, 201):
            folder_file_cache.pop(folder_key, None)
            payload = response.json().get("data", {})
            osf_path = payload.get("attributes", {}).get("path")
            if isinstance(osf_path, str):
                return "uploaded", osf_path
            return "uploaded", None

        if response.status_code != 409:
            raise RuntimeError(
                f"Could not upload {local_path} ({_response_error_detail(response)})."
            )

        existing = _get_folder_file_map(folder_key, folder, folder_file_cache).get(
            filename
        )
        if existing is None and known_osf_path is not None:
            existing = _file_from_osf_path(folder.session, known_osf_path)
        if existing is None:
            existing = _file_from_folder_name(folder, filename)

        if existing is None:
            return "skipped", known_osf_path

        local_md5 = _local_md5(local_path, local_md5_cache)

        remote_md5 = (existing.hashes or {}).get("md5")
        if remote_md5 and local_md5 == remote_md5:
            return "skipped", existing.osf_path

        fp.seek(0)
        _update_existing_file(existing, fp)
        return "uploaded", existing.osf_path


def _upload_index_once(bids_root_folder: Storage, index_bytes: bytes) -> None:
    response = bids_root_folder._put(
        bids_root_folder._new_file_url,
        params={"name": INDEX_FILENAME},
        data=index_bytes,
    )

    if response.status_code in (200, 201):
        return

    if response.status_code != 409:
        raise RuntimeError(
            f"Could not upload {INDEX_FILENAME} ({_response_error_detail(response)})."
        )

    existing = _file_from_folder_name(bids_root_folder, INDEX_FILENAME)
    if existing is None:
        raise RuntimeError(
            f"Could not resolve existing {INDEX_FILENAME} after conflict."
        )

    update_response = existing._put(existing._upload_url, data=index_bytes)
    if update_response.status_code != 200:
        raise RuntimeError(
            f"Could not update {INDEX_FILENAME} ({_response_error_detail(update_response)})."
        )


def _serialize_index(index: DatasetIndex) -> bytes:
    return json.dumps(index, indent=2, sort_keys=True).encode()


def _generate_index(storage: Storage) -> DatasetIndex:
    """Walk remote OSF files and build the dataset index."""
    prefix = BIDS_ROOT_NAME + "/"
    index: DatasetIndex = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Scanning OSF storage...[/]", total=None)
        for remote_file in storage.files:
            materialized = remote_file.path.lstrip("/")
            if materialized.startswith(prefix):
                rel_path = materialized[len(prefix) :]
                if rel_path and rel_path != INDEX_FILENAME:
                    size = getattr(remote_file, "size", None)
                    if not isinstance(size, int) or isinstance(size, bool):
                        size = None
                    md5 = (getattr(remote_file, "hashes", None) or {}).get("md5")
                    if not isinstance(md5, str):
                        md5 = None
                    index[rel_path] = {
                        "osf_path": remote_file.osf_path,
                        "size": size,
                        "md5": md5,
                    }
                    progress.advance(task)

    return index


def generate_index_with_retry(
    token: str,
    project_id: str,
    max_attempts: int = 5,
) -> DatasetIndex:
    """Build the dataset index by scanning OSF storage with retries."""
    for attempt in range(1, max_attempts + 1):
        storage = _get_storage_with_retry(token, project_id, max_attempts=max_attempts)
        try:
            return _generate_index(storage)
        except Exception as exc:
            if attempt >= max_attempts or not _is_retryable(exc):
                raise
            wait_seconds = min(2 ** (attempt - 1), 30)
            _print_retry_message(
                context="dataset index scan",
                attempt=attempt,
                max_attempts=max_attempts,
                wait_seconds=wait_seconds,
                exc=exc,
            )
            time.sleep(wait_seconds)
            continue

    raise RuntimeError(
        f"Failed to build OSF dataset index after {max_attempts} retries."
    )


def upload_dataset(
    bids_dir: Path,
    token: str,
    project_id: str,
) -> DatasetIndex:
    """Sync a local BIDS directory to OSF: upload new and changed files.

    Files are uploaded under the ``cybis-pereira-2026-bids/`` folder in the
    project's OSF storage, regardless of the local directory name.

    Parameters
    ----------
    bids_dir : pathlib.Path
        Local BIDS root directory.
    token : str
        OSF personal access token.
    project_id : str
        OSF project ID.

    Returns
    -------
    index : dict[str, dict[str, str | int | None]]
        Incrementally updated mapping suitable for ``dataset_index.json``
        upload, containing OSF path, file size in bytes, and MD5 checksum.

    Notes
    -----
    The remote ``dataset_index.json`` (a single fast download) is the source of
    truth for what is already on OSF and its MD5s. A file is skipped, with no
    network transfer, when its local MD5 matches the recorded one; otherwise it
    is uploaded. An index written before md5 tracking existed
    is upgraded once by scanning the remote listing to backfill hashes (slow--OSF
    caps requests at 1/second--but only needed once). The index is
    re-uploaded after every written file, so an interrupted run resumes without
    re-uploading files that already made it to OSF. Use ``--index-only`` to
    rebuild the index from a fresh authoritative scan of remote storage.
    """
    bids_dir = Path(bids_dir)
    all_files = sorted(path for path in bids_dir.rglob("*") if path.is_file())
    max_attempts = 5
    storage = _get_storage_with_retry(token, project_id, max_attempts=max_attempts)
    bids_root_folder = _create_bids_root_folder(storage)
    folder_cache: dict[str, Storage] = {"": bids_root_folder}
    folder_file_cache: dict[str, dict[str, File]] = {}
    local_md5_cache: dict[Path, str] = {}

    def reconnect() -> None:
        nonlocal storage, bids_root_folder, folder_cache, folder_file_cache
        storage = _get_storage_with_retry(token, project_id, max_attempts=max_attempts)
        bids_root_folder = _create_bids_root_folder(storage)
        folder_cache = {"": bids_root_folder}
        folder_file_cache = {}

    def persist_index(context: str) -> None:
        """Best-effort re-upload of the remote index so runs are resumable."""
        try:
            _upload_index_once(bids_root_folder, _serialize_index(index))
        except Exception as exc:
            if not _is_retryable(exc):
                raise
            try:
                reconnect()
                _upload_index_once(bids_root_folder, _serialize_index(index))
            except Exception as exc2:
                CONSOLE.print(
                    f"[yellow]Warning:[/] could not persist index after "
                    f"{context}: {exc2}"
                )

    # Load the published index (one request) -- fast, and the source of truth
    # for the hash comparison. Retryable so a transient error is not misread as
    # an empty remote.
    index: DatasetIndex = {}
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        progress.add_task("[cyan]Loading dataset_index.json from OSF...[/]", total=None)
        for attempt in range(1, max_attempts + 1):
            try:
                index = _load_remote_index(bids_root_folder)
                break
            except Exception as exc:
                if attempt >= max_attempts or not _is_retryable(exc):
                    raise
                time.sleep(min(2 ** (attempt - 1), 30))
                reconnect()

    if index:
        CONSOLE.print(f"[green]Loaded {len(index)} entries from the remote index.[/]")
    else:
        CONSOLE.print("[yellow]No remote index found; uploading everything.[/]")

    # One-time upgrade: an index written before md5 tracking has no hashes, so
    # the skip-check cannot work until they are backfilled. Scan the remote
    # listing (which carries md5s) once and persist the upgraded index.
    missing = [k for k, v in index.items() if not isinstance(v.get("md5"), str)]
    if missing:
        CONSOLE.print(
            f"[yellow]{len(missing)} of {len(index)} entries lack md5.[/] "
            "Backfilling from the OSF listing (one-time, ~1 request/second)..."
        )
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            transient=True,
        ) as progress:
            progress.add_task("[cyan]Scanning OSF storage for hashes...[/]", total=None)
            for attempt in range(1, max_attempts + 1):
                try:
                    filled = _backfill_md5_from_remote(storage, index)
                    break
                except Exception as exc:
                    if attempt >= max_attempts or not _is_retryable(exc):
                        raise
                    time.sleep(min(2 ** (attempt - 1), 30))
                    reconnect()
        CONSOLE.print(f"[green]Backfilled md5 for {filled} entries.[/]")
        # Save immediately so the slow scan is not lost if the run is
        # interrupted before any file upload.
        persist_index("md5 backfill")

    uploaded = 0
    skipped = 0
    failed: dict[str, str] = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task(
            "[cyan]Uploading files to OSF...[/]",
            total=len(all_files),
        )

        for local_path in all_files:
            rel = local_path.relative_to(bids_dir)
            rel_path = rel.as_posix()
            rel_dir = rel.parent.as_posix()
            filename = rel.name

            entry = index.get(rel_path)
            entry_osf_path = entry.get("osf_path") if entry else None
            known_osf_path = entry_osf_path if isinstance(entry_osf_path, str) else None
            known_md5 = entry.get("md5") if entry else None
            known_md5 = known_md5 if isinstance(known_md5, str) else None

            progress.update(
                task,
                description=(
                    f"[cyan]Uploading[/] ({uploaded} up / {skipped} skip): "
                    f"[white]{_short_path(rel_path)}[/]"
                ),
            )

            # Decide from the index: skip files whose local hash matches the
            # recorded one, upload the rest (new files and changed files).
            if (
                entry is not None
                and known_md5 is not None
                and _local_md5(local_path, local_md5_cache) == known_md5
            ):
                entry["size"] = local_path.stat().st_size
                skipped += 1
                progress.advance(task)
                continue

            for attempt in range(1, max_attempts + 1):
                try:
                    folder_key, parent_folder = _ensure_parent_folder(
                        rel_dir, folder_cache
                    )
                    status, osf_path = _upload_file_once(
                        parent_folder,
                        folder_key,
                        filename,
                        local_path,
                        folder_file_cache=folder_file_cache,
                        local_md5_cache=local_md5_cache,
                        known_osf_path=known_osf_path,
                        known_md5=known_md5,
                    )
                except Exception as exc:
                    if attempt >= max_attempts or not _is_retryable(exc):
                        # A single stubborn file must not abort the whole
                        # sync; record it and keep uploading the rest.
                        failed[rel_path] = str(exc)
                        CONSOLE.print(
                            f"[bold red]Failed[/] (giving up on this file): "
                            f"{rel_path}: {exc}"
                        )
                        break

                    wait_seconds = min(2 ** (attempt - 1), 30)
                    progress.update(
                        task,
                        description=(
                            f"[yellow]Retry {attempt}/{max_attempts - 1}[/] "
                            f"for [white]{local_path.name}[/] "
                            f"in [bold]{wait_seconds}s[/]..."
                        ),
                    )
                    time.sleep(wait_seconds)
                    reconnect()
                    continue

                if status == "uploaded":
                    uploaded += 1
                else:
                    skipped += 1

                if osf_path is None:
                    existing = _get_folder_file_map(
                        folder_key,
                        parent_folder,
                        folder_file_cache,
                    ).get(filename)
                    if existing is not None:
                        osf_path = existing.osf_path

                file_md5 = _local_md5(local_path, local_md5_cache)
                if osf_path is not None:
                    index[rel_path] = {
                        "osf_path": osf_path,
                        "size": local_path.stat().st_size,
                        "md5": file_md5,
                    }
                elif rel_path in index:
                    index[rel_path]["size"] = local_path.stat().st_size
                    index[rel_path]["md5"] = file_md5

                # Persist the index after each written file so an interrupted
                # run resumes from here instead of re-uploading everything.
                persist_index(rel_path)
                break

            progress.advance(task)

    CONSOLE.print(
        "[bold green]Upload complete[/]: "
        f"[green]{uploaded} uploaded[/], [yellow]{skipped} skipped[/]"
        + (f", [red]{len(failed)} failed[/]." if failed else ".")
    )
    if failed:
        CONSOLE.print("[bold red]Files that could not be uploaded:[/]")
        for rel_path, reason in failed.items():
            CONSOLE.print(f"  [red]-[/] {rel_path}: {reason}")
    return index


def upload_index(
    index: DatasetIndex,
    token: str,
    project_id: str,
) -> None:
    """Upload ``dataset_index.json`` to OSF.

    Always overwrites any existing index file.

    Parameters
    ----------
    index : dict[str, dict[str, str | int | None]]
        Index dict as returned by `generate_index`.
    token : str
        OSF personal access token.
    project_id : str
        OSF project ID.
    """
    max_attempts = 5
    index_bytes = _serialize_index(index)

    for attempt in range(1, max_attempts + 1):
        try:
            storage = _get_storage_with_retry(
                token,
                project_id,
                max_attempts=max_attempts,
            )
            bids_root_folder = _create_bids_root_folder(storage)
            _upload_index_once(bids_root_folder, index_bytes)
        except Exception as exc:
            if attempt >= max_attempts or not _is_retryable(exc):
                raise
            wait_seconds = min(2 ** (attempt - 1), 30)
            _print_retry_message(
                context="dataset index upload",
                attempt=attempt,
                max_attempts=max_attempts,
                wait_seconds=wait_seconds,
                exc=exc,
            )
            time.sleep(wait_seconds)
            continue
        else:
            return
