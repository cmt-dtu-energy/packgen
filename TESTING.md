# Testing packgen

## Layout

`packgen` is split so that almost all logic can be tested from a normal virtual
environment:

| Module | Depends on Blender? | How it is tested |
|---|---|---|
| `packgen/geometry.py`: volumes, particle-type mixing, lattice, piston/container sizing | no | unit tests (`test/test_geometry.py`, `test/test_volumes.py`) |
| `packgen/params.py`: command-line and parameters-file handling | no | unit tests (`test/test_params.py`) |
| `packgen/__init__.py`: `packgen` entry point, Blender discovery | no (Blender is mocked) | unit tests (`test/test_cli.py`) |
| `packgen/blend.py`: the thin layer driving `bpy` (mesh creation, rigid bodies, baking, export) | **yes** | end-to-end test (`test/test_blender.py`, marked `blender`) |

## Running

```shell
uv run pytest --cov            # unit tests + coverage of the Blender-independent core
uv run pytest -m blender       # end-to-end: runs a tiny packing in background Blender
```

The `blender` tests are skipped by default. They find Blender the same way the `packgen`
command does. To use a different executable, set `$BLENDER`.

## What is not covered by unit tests, and why

- **`blend.py`** is left out of coverage. It only runs inside Blender's embedded
  interpreter (`blender -P blend.py`), and its job is to call `bpy` operators. The
  `blender`-marked test checks it end to end: it runs a simulation and checks the STL/JSON
  outputs. It does not check the physics results themselves.
- **The real `subprocess` launch in `main()`** is mocked in the unit tests. The end-to-end
  test runs Blender directly in background mode (`-b`), not through `main()`, because
  `main()` opens the Blender GUI.
- **Windows**: the hard-coded Blender path in `find_Blender_executable()` has only been
  checked in a mocked test, never against a real Windows install.

## Blender versions verified

| Blender | OS | Date | How |
|---|---|---|---|
| 4.3.2 | macOS (Apple Silicon) | 2026-10-26 | `pytest -m blender`. The STL output was also byte-identical to the pre-refactor code for `examples/parameters.json` |

Add a row when you check a new Blender version. This is the most likely thing to break.
