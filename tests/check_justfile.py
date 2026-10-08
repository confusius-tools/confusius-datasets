"""Check all just runners with a stub uv; never download or convert real data."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

repository = Path(__file__).resolve().parents[1]

with TemporaryDirectory() as directory:
    root = Path(directory)
    shutil.copy2(repository / "justfile", root / "justfile")
    binary = root / "bin"
    binary.mkdir()
    uv = binary / "uv"
    uv.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "if os.environ.get('CHECK_UV_FAIL'): sys.exit(11)\n"
        "with open(os.environ['CHECK_UV_LOG'], 'a') as log:\n"
        "    log.write(json.dumps(sys.argv[1:]) + '\\n')\n"
    )
    uv.chmod(0o755)
    log = root / "uv.jsonl"
    environment = {
        **os.environ,
        "PATH": f"{binary}:{os.environ['PATH']}",
        "CHECK_UV_LOG": str(log),
    }
    source = root / "source with 'quotes' and spaces"
    source.mkdir()
    (source / "participants.tsv").write_text("participant_id\nsub-test\n")
    converters = {
        "nunez-elizalde-2022": "nunez-convert",
        "cybis-pereira-2026": "cybis-convert",
        "pereira-2025": "pereira-convert",
        "pepe-mariani-2026": "pepe-mariani-convert",
    }
    expected = []
    for name, command in converters.items():
        subprocess.run(
            ["just", name, str(source), "--dry-run"],
            cwd=root,
            env=environment,
            check=True,
        )
        expected.append(
            [
                "run",
                "--locked",
                "--project",
                f"recipes/{name}-bids",
                command,
                "--src",
                str(source),
                "--out",
                f"work/{name}-bids",
                "--dry-run",
            ]
        )
    subprocess.run(
        ["just", "khallaf-2026", "--data-dir", str(source)],
        cwd=root,
        env=environment,
        check=True,
    )
    expected.append(
        [
            "run",
            "--locked",
            "--project",
            "recipes/khallaf-2026-bids",
            "python",
            "recipes/khallaf-2026-bids/main.py",
            "--data-dir",
            str(source),
        ]
    )
    for name, filename in (
        ("pepe-mariani-2026", "pepe-mariani-2026-fusi-template.nii.gz"),
        ("huang-2025", "huang-2025-space-allen50_desc-vascular.nii.gz"),
    ):
        outputs = root / "recipes" / f"{name}-template" / "outputs"
        outputs.mkdir(parents=True)
        (outputs / filename).write_bytes(b"reference template")
        subprocess.run(
            ["just", f"template-{name}"], cwd=root, env=environment, check=True
        )
        expected.append(
            [
                "run",
                "--locked",
                "--project",
                f"recipes/{name}-template",
                "python",
                f"recipes/{name}-template/main.py",
            ]
        )
        assert (
            root / "work" / f"{name}-template" / filename
        ).read_bytes() == b"reference template"
    assert [json.loads(line) for line in log.read_text().splitlines()] == expected

    subprocess.run(
        ["just", "landemard-2026", str(source)], cwd=root, env=environment, check=True
    )
    assert (root / "work/landemard-2026-bids/participants.tsv").read_bytes() == (
        source / "participants.tsv"
    ).read_bytes()
    invalid = subprocess.run(
        ["just", "landemard-2026", str(root / "missing")],
        cwd=root,
        env=environment,
        capture_output=True,
        check=False,
    )
    assert invalid.returncode != 0

    shutil.rmtree(root / "work/huang-2025-template")
    failed = subprocess.run(
        ["just", "template-huang-2025"],
        cwd=root,
        env={**environment, "CHECK_UV_FAIL": "1"},
        capture_output=True,
        check=False,
    )
    assert failed.returncode != 0
    assert not (root / "work/huang-2025-template").exists()

print(
    "PASS: eight just runners, quoted paths, forwarded flags, staging, and failure propagation"
)
