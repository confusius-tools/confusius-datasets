"""Render recording progress columns without importing conversion dependencies."""

import ast
from io import StringIO
from pathlib import Path

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
from rich.table import Column

repository = Path(__file__).resolve().parents[1]
for name in (
    "pepe-mariani-2026-bids", "pereira-2025-bids",
    "cybis-pereira-2026-bids", "nunez-elizalde-2022-bids",
):
    package = repository / "recipes" / name / "src" / name.replace("-", "_")
    source = package / ("convert.py" if name.startswith("cybis-") else "converter.py")
    tree = ast.parse(source.read_text())
    helper = next((node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_progress_columns"), None)
    if helper is not None:
        expression = next(node.value for node in ast.walk(helper) if isinstance(node, ast.Return))
    else:
        call = next(node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Progress")
        expression = ast.List(elts=call.args, ctx=ast.Load())
    code = compile(ast.fix_missing_locations(ast.Expression(expression)), str(source), "eval")
    for width in (80, 120):
        output = StringIO()
        console = Console(file=output, width=width, force_terminal=True, color_system=None)
        progress = Progress(*eval(code), console=console, auto_refresh=False)
        task = progress.add_task("Converting sub-" + "long-filename_" * 20 + "pwd.nii.gz", total=1365)
        progress.update(task, completed=683)
        console.print(progress.get_renderable())
        rendered = output.getvalue()
        assert len(rendered.splitlines()) == 1, (name, width, rendered)
        assert "Converting" in rendered and "…" in rendered, (name, width, rendered)
        assert "━" in rendered and "683/1365" in rendered, (name, width, rendered)
        assert "0:00:00" in rendered, (name, width, rendered)
        assert len(rendered.rstrip("\n")) <= width

print("PASS: four converters retain bars, counts, and timers at 80 and 120 columns")
