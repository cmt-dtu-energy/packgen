"""Pure geometric and compositional calculations for the packing simulation.

Nothing in this module depends on Blender, so it can be tested and reused
outside Blender's embedded Python interpreter.
"""

import math
from enum import IntEnum
from typing import Any


class ParticleType(IntEnum):
    """Type of a particle; the value indexes per-type parameter sequences."""

    INVALID = -1
    A = 0
    B = 1


def volume_prism(sides: float, radius: float, height: float) -> float:
    """Return the volume of a prism with given number of sides, radius, and height.

    References:
        https://en.wikipedia.org/wiki/Regular_polygon

    """
    return 1 / 2 * sides * radius * radius * math.sin(2 * math.pi / sides) * height


def num_particles_total(parameters: dict[str, Any]) -> int:
    """Return the total number of particles in the initial lattice."""
    return (
        int(parameters["num_particles_x"])
        * int(parameters["num_particles_y"])
        * int(parameters["num_particles_z"])
    )


def num_B_particles(parameters: dict[str, float], num_particles_total: int) -> int:
    """Return the total number of type-B particles to be generated.

    Args:
        parameters (dict[str, float]): The parameters of the packing simulation.
        num_particles_total (int): The total number of particles to be generated.

    """
    rho_B = parameters["density_B"]
    rho_A = parameters["density_A"]

    r_B = parameters["r_B"]
    r_A = parameters["r_A"]

    h_B = parameters["thickness_B"]
    h_A = parameters["thickness_A"]

    n_sides = int(parameters["num_sides"])
    V_B = volume_prism(n_sides, r_B, h_B)
    V_A = volume_prism(n_sides, r_A, h_A)

    beta = rho_B * V_B / (rho_A * V_A)

    x_B = parameters["mass_fraction_B"]
    alpha = 1 / beta * (x_B / (1 - x_B))

    N_B = alpha / (1 + alpha) * num_particles_total

    return math.ceil(N_B)


def number_fraction_B(parameters: dict[str, Any]) -> float:
    """Return the fraction of type-B particles by number."""
    total = num_particles_total(parameters)
    return num_B_particles(parameters, total) / total


def choose_particle_type(fraction_B: float, rnd: float) -> ParticleType:
    """Choose a particle type from a uniform random number in [0, 1].

    Args:
        fraction_B (float): The fraction of type-B particles by number.
        rnd (float): A random number drawn uniformly from [0, 1].

    """
    # if we are supposed to generate only 20% of A,
    # and we randomly select a number bigger than that,
    # then we must generate the other type
    if rnd > 1 - fraction_B:
        return ParticleType.B
    return ParticleType.A


def particle_dimensions(
    parameters: dict[str, Any], particle_type: ParticleType
) -> tuple[float, float]:
    """Return the scaled (radius, height) of a particle of the given type."""
    scale = parameters["scale"]
    radii = (parameters["r_A"], parameters["r_B"])
    heights = (parameters["thickness_A"], parameters["thickness_B"])
    return scale * radii[particle_type], scale * heights[particle_type]


def particle_mass(parameters: dict[str, Any], particle_type: ParticleType) -> float:
    """Return the mass of a particle of the given type."""
    densities = (parameters["density_A"], parameters["density_B"])
    radius, height = particle_dimensions(parameters, particle_type)
    volume = volume_prism(parameters["num_sides"], radius, height)
    return densities[particle_type] * volume


def lattice_positions(parameters: dict[str, Any]) -> list[tuple[float, float, float]]:
    """Return the initial (x, y, z) positions of the particles.

    Particles are placed on a regular lattice centered on the z axis,
    with the first layer at half the lattice spacing above the origin.
    """
    num_particles_x = int(parameters["num_particles_x"])
    num_particles_y = int(parameters["num_particles_y"])
    num_particles_z = int(parameters["num_particles_z"])
    distance = parameters["distance"]
    z0 = distance / 2
    return [
        (
            (ix - num_particles_x / 2 + 0.5) * distance,
            (iy - num_particles_y / 2 + 0.5) * distance,
            z0 + iz * distance,
        )
        for ix in range(num_particles_x)
        for iy in range(num_particles_y)
        for iz in range(num_particles_z)
    ]


def piston_dimensions(parameters: dict[str, Any]) -> tuple[float, float]:
    """Return the (side length, center height) of the piston.

    The piston is a cube slightly narrower than the container, placed above
    the highest particle of the initial lattice.
    """
    distance = parameters["distance"]
    L_container = int(parameters["num_particles_x"]) * distance
    max_z_particles = distance / 2 + int(parameters["num_particles_z"]) * distance
    slack = parameters.get("container_piston_slack", 0.0)
    L_piston = (1 - slack) * L_container
    z_piston = 1.1 * max_z_particles + L_piston / 2
    return L_piston, z_piston


def container_dimensions(
    parameters: dict[str, Any], L_piston: float, z_piston: float
) -> tuple[float, float]:
    """Return the (side length, height) of the container.

    The container is tall enough to enclose the piston at its initial position.
    """
    Lxy = parameters["num_particles_x"] * parameters["distance"]
    Lz = 1.1 * (z_piston + L_piston / 2)
    return Lxy, Lz
