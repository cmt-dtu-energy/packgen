"""Tests for command-line and parameters-file handling."""

import json
from pathlib import Path

import pytest

from packgen import params


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["blender", "-P", "blend.py"], "parameters.json"),
        (["blender", "-P", "blend.py", "--"], "parameters.json"),
        (["blender", "-P", "blend.py", "--", "my_run.json"], "my_run.json"),
        (["blender", "--", "a.json", "b.json"], "a.json"),
    ],
)
def test_get_parameters_file(argv: list[str], expected: str) -> None:
    """The parameters file is the first argument after '--'."""
    assert params.get_parameters_file(argv) == expected


def test_get_parameters_file_defaults_to_sys_argv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without an explicit argv, sys.argv is used."""
    monkeypatch.setattr("sys.argv", ["blender", "--", "from_sys.json"])
    assert params.get_parameters_file() == "from_sys.json"


def test_get_params_suffix() -> None:
    """The suffix is the parameters file stem."""
    assert params.get_params_suffix(["x", "--", "runs/case_5.json"]) == "case_5"
    assert params.get_params_suffix(["x"]) == "parameters"


def test_load_parameters_keeps_seed(tmp_path: Path) -> None:
    """A given seed is preserved."""
    f = tmp_path / "p.json"
    f.write_text(json.dumps({"seed": 42, "scale": 2.5}))
    assert params.load_parameters(str(f)) == {"seed": 42, "scale": 2.5}


@pytest.mark.parametrize("content", [{"seed": None}, {}])
def test_load_parameters_draws_seed(tmp_path: Path, content: dict) -> None:
    """A null or missing seed is replaced by a random one."""
    f = tmp_path / "p.json"
    f.write_text(json.dumps(content))
    seed = params.load_parameters(str(f))["seed"]
    assert isinstance(seed, float)
    assert 0 <= seed < 1e6
