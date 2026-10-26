# packgen

`packgen` generates packings of prismatic particles. It places particles on a lattice
above an open container. Then gravity, collisions and friction, simulated with
[Blender](https://www.blender.org/)'s rigid-body engine, act on them until they settle.
The main output is an STL mesh of the settled particles.

Only hexagonal (in general, regular-polygon) prisms are implemented. There can be two
particle types, *A* and *B*, with different sizes and densities, mixed at a given
mass fraction.

## Installation

1. Install [Blender](https://www.blender.org/download/). `packgen` looks for it at:
    - **macOS**: `/Applications/Blender.app/Contents/MacOS/Blender`
    - **Linux**: `blender` on your `PATH` (falling back to `/bin/blender`)
    - **Windows**: `C:\Program Files\Blender Foundation\Blender\4.3\Blender.exe`
2. Install `packgen` with `pip` or `uv pip`:

    ```shell
    pip install git+https://github.com/cmt-dtu-energy/packgen
    ```

## Usage

Write a [parameters file](parameters.md) (see the
[examples](https://github.com/cmt-dtu-energy/packgen/tree/main/examples)), then run
this in the directory that contains it:

```shell
packgen -- <path to the parameter file>
```

This opens Blender, simulates the packing and writes the outputs to the current
directory. Each output is named `packing_<basename of parameter file>.<extension>`:

| File | Contents |
|---|---|
| `.blend` | The complete Blender file, which can be reopened and used for rendering |
| `.stl` | Only the particles, without the container or piston |
| `.json` | A copy of the input parameters, including the `seed` that was actually used |

Each output can be turned off with the `save_*_file` [parameters](parameters.md#output).
If you leave out `-- <path>`, `packgen` reads `parameters.json` from the current
directory.

!!! tip "Reproducible packings"
    Set `"seed": null` to get a different random packing each run. The seed that was
    drawn is stored in the output `.json`, so you can reproduce any run.
