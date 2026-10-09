"""Check release defaults and staging with stdlib only; no real downloads."""

import argparse
import ast
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

repository = Path(__file__).resolve().parents[1]

with TemporaryDirectory() as directory:
    root = Path(directory)
    for recipe in sorted((repository / "recipes").iterdir()):
        if not (recipe / "pyproject.toml").exists():
            continue
        metadata = tomllib.loads((recipe / "pyproject.toml").read_text())["project"]
        assert not any(name.endswith("-upload") for name in metadata.get("scripts", {}))
        assert not any(dep.startswith(("osfclient", "python-dotenv")) for dep in metadata.get("dependencies", []))
        assert not list(recipe.glob("src/*/upload.py"))
        assert metadata["version"] == "1.0.0"
        lock = tomllib.loads((recipe / "uv.lock").read_text())
        assert next(p for p in lock["package"] if p["name"] == metadata["name"])["version"] == "1.0.0"
        target = root / "recipes" / recipe.name
        target.mkdir(parents=True)
        (target / "pyproject.toml").write_text('[project]\nversion = "2.3.4"\n')
        script = recipe / "main.py"
        if not script.exists():
            script = next((recipe / "src").glob("*/cli.py"))
        copied = target / script.relative_to(recipe)
        copied.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(script, copied)

        # Execute only path configuration and parser definitions, avoiding heavy imports.
        tree = ast.parse(copied.read_text())
        names = {"RECIPE", "ROOT", "VERSION", "DEFAULT_OUT", "OUTPUTS", "OUTPUTS_ROOT"}
        nodes = [node for node in tree.body if (
            isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id in names for t in node.targets)
        ) or isinstance(node, ast.With) or (
            isinstance(node, ast.FunctionDef)
            and node.name in {"build_parser", "_build_convert_parser"}
        )]
        namespace = {"__file__": str(copied), "Path": Path, "tomllib": tomllib, "argparse": argparse}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(copied), "exec"), namespace)
        category = "templates" if recipe.name.endswith("-template") else "datasets"
        expected = root / "publish" / category / recipe.name / "2.3.4"
        key = "OUTPUTS_ROOT" if recipe.name == "pepe-mariani-2026-template" else (
            "OUTPUTS" if recipe.name == "huang-2025-template" else "DEFAULT_OUT"
        )
        assert namespace[key] == expected
        for name in ("build_parser", "_build_convert_parser"):
            if name in namespace:
                parser = namespace[name]()
                assert parser.parse_args(["--src", "input"]).out == expected
                assert parser.parse_args(["--src", "input", "--out", "custom"]).out == Path("custom")

    source = root / "source with 'quotes'"
    source.mkdir()
    (source / "participants.tsv").write_text("participant_id\nsub-test\n")
    landemard = root / "recipes/landemard-2026-bids/main.py"
    subprocess.run([sys.executable, str(landemard), str(source)], cwd=root, check=True)
    staged = root / "publish/datasets/landemard-2026-bids/2.3.4"
    assert (staged / "participants.tsv").read_bytes() == (source / "participants.tsv").read_bytes()
    assert subprocess.run([sys.executable, str(landemard), str(source)], capture_output=True).returncode != 0
    custom = root / "custom"
    subprocess.run([sys.executable, str(landemard), str(source), "--out", str(custom)], check=True)
    assert (custom / "participants.tsv").exists()
    assert subprocess.run([sys.executable, str(landemard), str(root / "missing"), "--out", str(root / "invalid")], capture_output=True).returncode != 0

    cache = root / "work"
    cache.mkdir()
    archive = cache / "khallaf-2026.zip"
    with ZipFile(archive, "w") as zipfile:
        zipfile.writestr("naked_mole_rat_fusi_dataset/participants.tsv", "sub-test\n")
    khallaf = root / "recipes/khallaf-2026-bids/main.py"
    subprocess.run([sys.executable, str(khallaf)], cwd=root, check=True)
    assert (root / "publish/datasets/khallaf-2026-bids/2.3.4/participants.tsv").read_text() == "sub-test\n"
    assert not archive.exists()
    assert subprocess.run([sys.executable, str(khallaf)], cwd=root, capture_output=True).returncode != 0
    with ZipFile(archive, "w") as zipfile:
        zipfile.writestr("../unsafe", "bad")
    invalid = root / "unsafe-output"
    assert subprocess.run([sys.executable, str(khallaf), "--out", str(invalid)], cwd=root, capture_output=True).returncode != 0
    assert archive.exists() and not invalid.exists() and not (root / "unsafe").exists()

print("PASS: eight pyproject-driven defaults, lock versions, overrides, staging, and safe extraction")
