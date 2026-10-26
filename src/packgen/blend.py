"""Run packing simulation in Blender.

This script reads parameters from a file passed on the
command line, or "parameters.json" by default, and
simulates particles falling due to the gravitational field
inside a container box.

There are two types of particles, "A" and "B". The particles are assumed to be
prismatic, with the polygonal faces characterized by a circumscribed radius,
and the prism having a given height. The parameters file describes these
geometric parameters, together with the densities of the particles.
The container configuration is also included.

Original design and implementation by Andrea Insinga.
"""

import json
import os
import random
import sys
from pathlib import Path
from typing import Any

import bpy

# Blender runs this file as a script (`blender -P blend.py`), with its own
# interpreter where `packgen` may not be installed, so make the package importable.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packgen.geometry import (
    ParticleType,
    choose_particle_type,
    container_dimensions,
    lattice_positions,
    number_fraction_B,
    particle_dimensions,
    particle_mass,
    piston_dimensions,
)
from packgen.params import (
    get_parameters_file,
    get_params_suffix,
    load_parameters,
)

COMBINATION_RED = (0.1, 0.8)
COMBINATION_GREEN = (0.8, 0.4)
COMBINATION_BLUE = (0.7, 0.7)


class Particle:
    def __init__(
        self, x: float, y: float, z: float, parameters: dict[str, Any]
    ) -> None:
        self.parameters = parameters
        particle_type = choose_particle_type(
            number_fraction_B(parameters), random.uniform(0.0, 1.0)
        )
        self.type = particle_type
        radius, height = particle_dimensions(parameters, particle_type)

        bpy.ops.mesh.primitive_cylinder_add(
            vertices=parameters["num_sides"],
            radius=radius,
            depth=height,
            enter_editmode=False,
            location=(x, y, z),
        )
        # Get the active object (the newly created particle)
        particle = bpy.context.active_object
        # Assign a random rotation to the cube
        particle.rotation_euler = (
            random.uniform(0, 6.283185),
            random.uniform(0, 6.283185),
            random.uniform(0, 6.283185),
        )
        # Add rigid body physics to the particle
        bpy.ops.rigidbody.object_add(type="ACTIVE")
        particle.rigid_body.friction = parameters["particle_friction"]
        particle.rigid_body.restitution = parameters["particle_restitution"]
        particle.rigid_body.mass = particle_mass(parameters, particle_type)
        particle.rigid_body.linear_damping = parameters["particle_damping"]
        mat = bpy.data.materials.new("GenericMaterial")
        mat.diffuse_color = (
            float(COMBINATION_RED[particle_type]),
            float(COMBINATION_GREEN[particle_type]),
            float(COMBINATION_BLUE[particle_type]),
            1.0,
        )
        mat.specular_intensity = 0
        particle.active_material = mat


class Container:
    def __init__(self, side: float, height: float, parameters: dict[str, Any]) -> None:
        """Create an open cube-like container of given side length and height.

        Args:
            side (float): The length of the sides of the cube.
            height (float): The height of the container.
            parameters: The parameters of the packing simulation.

        """
        height_to_side_scale = height / side
        bpy.ops.mesh.primitive_cube_add(
            size=side,
            enter_editmode=False,
            location=(0, 0, height / 2),
            scale=(1, 1, height_to_side_scale),
        )
        cube = bpy.context.active_object

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.mesh.select_mode(type="FACE")

        bpy.ops.object.mode_set(mode="OBJECT")
        top_face = [face for face in cube.data.polygons if face.normal.z > 0.9]
        for face in top_face:
            face.select = True

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.delete(type="FACE")
        bpy.ops.object.mode_set(mode="OBJECT")

        modifier = cube.modifiers.new(name="Solidify", type="SOLIDIFY")

        modifier.thickness = parameters.get("container_wall_thickness", -0.2)

        bpy.ops.rigidbody.object_add(type="PASSIVE")
        cube.rigid_body.collision_shape = "MESH"
        cube.name = "Container"
        self.name = cube.name


class Piston:
    def __init__(self, parameters: dict[str, Any]) -> None:
        L_piston, z_piston = piston_dimensions(parameters)
        self.name: str | None = None

        if parameters["use_piston"]:
            bpy.ops.mesh.primitive_cube_add(
                size=L_piston,
                enter_editmode=False,
                align="WORLD",
                location=(0, 0, z_piston),
                scale=(1, 1, 1),
            )

            piston = bpy.context.active_object
            bpy.ops.rigidbody.object_add(type="ACTIVE")
            piston.rigid_body.friction = (
                0  # piston does not lose velocity when colliding
            )
            piston.rigid_body.restitution = 0  # piston does not bounce when colliding
            piston.rigid_body.mass = parameters["mass_piston"]
            piston.name = "Piston"
            self.name = piston.name

        self.z = z_piston
        self.L = L_piston


class PackingSimulation:
    """Packing simulation to be performed with the physics-engine."""

    def __init__(self, parameters: dict[str, Any]) -> None:
        self.parameters = parameters
        self._clean_state()
        self._initialize_random_state()

    def run(self):
        """Run the particle packing simulation."""  # noqa: D401
        self._initialize_particles()

        piston = self._initialize_piston()
        container = self._initialize_container(piston)

        self.bake_and_export(
            end_frame=self.parameters["end_frame"],
            objects_to_delete=[container, piston],
        )

    def _initialize_piston(self) -> Piston:
        return Piston(self.parameters)

    def _initialize_container(self, piston: Piston) -> Container:
        Lxy, Lz = container_dimensions(self.parameters, piston.L, piston.z)
        return Container(Lxy, Lz, self.parameters)

    def _initialize_particles(self) -> dict[ParticleType, int]:
        counts = {ParticleType.A: 0, ParticleType.B: 0}
        for x, y, z in lattice_positions(self.parameters):
            particle = Particle(x, y, z, self.parameters)
            counts[particle.type] += 1
        return counts

    @staticmethod
    def _clean_state():
        # Delete all existing mesh objects
        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.object.select_by_type(type="MESH")
        bpy.ops.object.delete()

        bpy.ops.ptcache.free_bake_all()

    def _initialize_random_state(self):
        seed = self.parameters["seed"]
        random.seed(seed)

    def bake_and_export(
        self,
        end_frame: int,
        objects_to_delete: Any = None,
    ) -> None:
        """Bake the physics simulation and export the results.

        Args:
            end_frame (int): The last frame to bake the simulation to.
            objects_to_delete: Objects that were created that should now be removed.
                If None, no object will be removed.

        """
        scene = bpy.context.scene
        # set the frame range
        scene.frame_start = 1
        scene.frame_end = end_frame
        # Match the rigid body world's cache frames to scene start and end
        scene.rigidbody_world.point_cache.frame_start = scene.frame_start
        scene.rigidbody_world.point_cache.frame_end = scene.frame_end

        # setting gravity
        parameters = self.parameters
        g = parameters.get("gravity_field", [0, 0, -9.8])
        scene.gravity = g

        bpy.ops.ptcache.bake_all()

        # step to the last frame so all transforms are final
        scene.frame_set(end_frame)

        # Use the current working directory for all output files
        output_dir = Path(os.getcwd())
        suffix = get_params_suffix()
        if parameters.get("save_blender_file", True):
            blend_path = output_dir / f"packing_{suffix}.blend"
            bpy.ops.wm.save_mainfile(filepath=str(blend_path))
        if parameters.get("save_json_file", True):
            json_path = output_dir / f"packing_{suffix}.json"

            with open(json_path, mode="w") as f:
                json.dump(parameters, f)

        # the container deletion should occur after the main saving above
        # to be able to inspect the Blender file
        for object_to_delete in objects_to_delete or []:
            name = getattr(object_to_delete, "name", None)
            if name and name in bpy.data.objects:
                # Method A: use the data API
                obj = bpy.data.objects[name]
                bpy.data.objects.remove(obj, do_unlink=True)

        # export STL with the correct operator
        if parameters.get("save_stl_file", True):
            stl_path = output_dir / f"packing_{suffix}.stl"
            bpy.ops.wm.stl_export(filepath=str(stl_path))

        if parameters.get("quit_on_finish", False):
            bpy.ops.wm.quit_blender()


if __name__ == "__main__":
    PackingSimulation(load_parameters(get_parameters_file())).run()
