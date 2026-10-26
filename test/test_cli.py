"""Tests for the `packgen` command-line entry point, with Blender mocked out."""

from unittest import mock

import pytest

import packgen


@pytest.mark.parametrize(
    ("system", "expected"),
    [
        ("Darwin", "/Applications/Blender.app/Contents/MacOS/Blender"),
        ("Windows", "Blender.exe"),
    ],
)
def test_find_Blender_executable(system: str, expected: str) -> None:
    """The executable path depends on the platform."""
    with mock.patch("platform.system", return_value=system):
        assert packgen.find_Blender_executable().endswith(expected)


def test_find_Blender_executable_linux_uses_path() -> None:
    """On Linux, Blender is looked up on PATH."""
    with (
        mock.patch("platform.system", return_value="Linux"),
        mock.patch("shutil.which", return_value="/opt/blender/blender"),
    ):
        assert packgen.find_Blender_executable() == "/opt/blender/blender"


def test_find_Blender_executable_linux_fallback() -> None:
    """On Linux without Blender on PATH, a default location is used."""
    with (
        mock.patch("platform.system", return_value="Linux"),
        mock.patch("shutil.which", return_value=None),
    ):
        assert packgen.find_Blender_executable() == "/bin/blender"


def test_find_Blender_executable_unknown_platform() -> None:
    """Unsupported platforms raise."""
    with (
        mock.patch("platform.system", return_value="Plan9"),
        pytest.raises(NotImplementedError),
    ):
        packgen.find_Blender_executable()


@pytest.mark.parametrize(
    ("argv", "extra"),
    [
        (["packgen"], []),
        (["packgen", "--", "run.json"], ["--", "run.json"]),
    ],
)
def test_main_launches_blender_with_script(argv: list[str], extra: list[str]) -> None:
    """main() runs Blender with the driver script and forwards args after '--'."""
    with (
        mock.patch("sys.argv", argv),
        mock.patch.object(packgen, "find_Blender_executable", return_value="blender"),
        mock.patch("subprocess.run") as run,
    ):
        packgen.main()
    run.assert_called_once_with(["blender", "-P", str(packgen.BLENDER_SCRIPT), *extra])
