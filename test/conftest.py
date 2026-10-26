"""Shared fixtures for the packgen test suite."""

import json
from pathlib import Path
from typing import Any

import pytest

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def tiny_parameters_file() -> Path:
    """Path to a small, fast-to-simulate parameters file."""
    return DATA_DIR / "tiny.json"


@pytest.fixture
def parameters(tiny_parameters_file: Path) -> dict[str, Any]:
    """Parameters of a small packing simulation."""
    return json.loads(tiny_parameters_file.read_text())
