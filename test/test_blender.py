"""End-to-end test running a tiny packing through a real Blender installation.

Deselected by default; run with `pytest -m blender`.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

import packgen

pytestmark = pytest.mark.blender


def _blender_executable() -> str | None:
    candidate = os.environ.get("BLENDER") or packgen.find_Blender_executable()
    return shutil.which(candidate) or (candidate if Path(candidate).exists() else None)


def test_tiny_packing(tmp_path: Path, tiny_parameters_file: Path) -> None:
    """A tiny packing runs in background Blender and writes the outputs."""
    executable = _blender_executable()
    if executable is None:
        pytest.skip("Blender executable not found (set $BLENDER)")
    params_file = tmp_path / "tiny.json"
    shutil.copy(tiny_parameters_file, params_file)

    subprocess.run(
        [executable, "-b", "-P", str(packgen.BLENDER_SCRIPT), "--", params_file.name],
        cwd=tmp_path,
        check=True,
        timeout=300,
    )

    assert (tmp_path / "packing_tiny.stl").stat().st_size > 0
    saved = json.loads((tmp_path / "packing_tiny.json").read_text())
    assert saved["seed"] == 7
