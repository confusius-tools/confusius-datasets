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
    source = "source with 'quotes' and spaces"
    expected = []
    for name, command in {
        "nunez-elizalde-2022": "nunez-convert",
        "cybis-pereira-2026": "cybis-convert",
        "pereira-2025": "pereira-convert",
        "pepe-mariani-2026": "pepe-mariani-convert",
    }.items():
        subprocess.run(
            ["just", name, source, "--dry-run", "--out", "custom output"],
            cwd=root, env=environment, check=True,
        )
        expected.append([
            "run", "--locked", "--project", f"recipes/{name}-bids", command,
            "--src", source, "--dry-run", "--out", "custom output",
        ])
    for runner, recipe, args in (
        ("landemard-2026", "landemard-2026-bids", [source]),
        ("khallaf-2026", "khallaf-2026-bids", ["--data-dir", source]),
        ("template-pepe-mariani-2026", "pepe-mariani-2026-template", []),
        ("template-huang-2025", "huang-2025-template", []),
    ):
        subprocess.run(["just", runner, *args], cwd=root, env=environment, check=True)
        expected.append([
            "run", "--locked", "--project", f"recipes/{recipe}",
            "python", f"recipes/{recipe}/main.py", *args,
        ])
    assert [json.loads(line) for line in log.read_text().splitlines()] == expected
    failed = subprocess.run(
        ["just", "template-huang-2025"], cwd=root,
        env={**environment, "CHECK_UV_FAIL": "1"}, capture_output=True,
    )
    assert failed.returncode != 0

print("PASS: eight just runners, quoted paths, forwarded flags, and failure propagation")
