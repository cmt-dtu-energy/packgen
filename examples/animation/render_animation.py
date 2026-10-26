"""Render the packing animation of a baked packgen Blender file to a GIF.

Run inside Blender on a `.blend` produced by packgen (with `save_blender_file`):

    blender -b packing_animation.blend -P render_animation.py -- packing.gif

Frames are rendered with the Workbench engine and assembled into a GIF with
`ffmpeg`, which must be on the PATH. Optional arguments after the output path:

    --size PIXELS   width and height of the GIF (default 400)
    --step N        render every N-th frame (default 1)
    --fps FPS       GIF frame rate (default 24)
    --hold SECONDS  how long to hold the last frame before looping (default 1.5)
"""

import argparse
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

# direction from the scene center towards the camera
VIEW_DIRECTION = Vector((1.0, -1.2, 0.7)).normalized()


def parse_args() -> argparse.Namespace:
    """Parse the arguments given after "--" on the Blender command line."""
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(prog="render_animation.py")
    parser.add_argument("output", type=Path, help="path of the GIF to write")
    parser.add_argument("--size", type=int, default=400)
    parser.add_argument("--step", type=int, default=1)
    parser.add_argument("--fps", type=float, default=24)
    parser.add_argument("--hold", type=float, default=1.5)
    return parser.parse_args(argv)


def setup_scene(size: int) -> None:
    """Configure a clean Workbench render with a cut-away container."""
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"

    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "MATERIAL"
    shading.show_shadows = True
    shading.show_cavity = True
    shading.cavity_type = "WORLD"

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (1.0, 1.0, 1.0)

    container = bpy.data.objects.get("Container")
    if container is not None:
        cut_away_walls(container)
    piston = bpy.data.objects.get("Piston")
    if piston is not None:
        flatten_piston(piston)


def cut_away_walls(container: bpy.types.Object) -> None:
    """Delete the container walls facing the camera, so the particles are visible.

    Only the rendered scene is changed; the .blend file is not saved.
    """
    bm = bmesh.new()
    bm.from_mesh(container.data)
    facing = [f for f in bm.faces if f.normal.dot(VIEW_DIRECTION) > 0.3]
    bmesh.ops.delete(bm, geom=facing, context="FACES")
    bm.to_mesh(container.data)
    bm.free()


def flatten_piston(piston: bpy.types.Object, thickness: float = 0.08) -> None:
    """Render the piston as a thin plate at its bottom face, so it hides less.

    Only the mesh is changed; the baked motion of the piston is unaffected.
    """
    mesh = piston.data
    z_bottom = min(v.co.z for v in mesh.vertices)
    for v in mesh.vertices:
        if v.co.z > z_bottom:
            v.co.z = z_bottom + thickness * piston.dimensions.x
    mesh.update()


def add_camera() -> None:
    """Add a camera looking down at the container from a three-quarter view."""
    scene = bpy.context.scene
    container = bpy.data.objects["Container"]
    side = container.dimensions.x

    # frame the region where the particles start and settle, not the full
    # container height, which is mostly empty
    particles = [o for o in bpy.data.objects if o.name.startswith("Cylinder")]
    scene.frame_set(scene.frame_start)
    top = max(o.matrix_world.translation.z for o in particles)
    target = Vector((0.0, 0.0, 0.45 * top))

    camera_data = bpy.data.cameras.new("AnimationCamera")
    camera_data.lens = 50
    camera = bpy.data.objects.new("AnimationCamera", camera_data)
    scene.collection.objects.link(camera)

    extent = max(side, top)
    distance = 1.35 * extent / (2 * math.tan(camera_data.angle / 2)) + side
    camera.location = target + distance * VIEW_DIRECTION
    camera.rotation_euler = (-VIEW_DIRECTION).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera


def render_frames(frames_dir: Path, step: int) -> None:
    """Render the animation frames as numbered PNG files."""
    scene = bpy.context.scene
    scene.frame_step = step
    scene.render.filepath = str(frames_dir / "frame_")
    bpy.ops.render.render(animation=True)


def assemble_gif(frames_dir: Path, output: Path, fps: float, hold: float) -> None:
    """Assemble the PNG frames into an optimized, looping GIF with ffmpeg."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        sys.exit("ffmpeg not found on PATH; it is needed to assemble the GIF")
    filters = (
        f"tpad=stop_mode=clone:stop_duration={hold},"
        "split[a][b];[a]palettegen=max_colors=64[p];[b][p]paletteuse=dither=bayer"
    )
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-framerate",
            str(fps),
            "-pattern_type",
            "glob",
            "-i",
            str(frames_dir / "frame_*.png"),
            "-filter_complex",
            filters,
            "-loop",
            "0",
            str(output),
        ],
        check=True,
    )


def main() -> None:
    """Render the animation of the open Blender file to a GIF."""
    args = parse_args()
    setup_scene(args.size)
    add_camera()
    with tempfile.TemporaryDirectory() as tmp:
        frames_dir = Path(tmp)
        render_frames(frames_dir, args.step)
        assemble_gif(frames_dir, args.output.resolve(), args.fps, args.hold)
    print(f"Wrote {args.output}")


main()
