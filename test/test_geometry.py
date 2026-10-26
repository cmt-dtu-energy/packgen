"""Tests for the Blender-independent geometry of the packing simulation."""

from math import isclose, pi
from statistics import mean
from typing import Any

import pytest

from packgen import geometry
from packgen.geometry import ParticleType


def test_volume_prism_square() -> None:
    """A square with circumradius r has area 2 r^2."""
    r, h = 1.7, 0.3
    assert isclose(geometry.volume_prism(4, r, h), 2 * r**2 * h)


def test_volume_prism_approaches_cylinder() -> None:
    """A prism with many sides approaches a cylinder."""
    r, h = 0.5, 2.0
    assert isclose(geometry.volume_prism(10_000, r, h), pi * r**2 * h, rel_tol=1e-6)


def test_volume_prism_scaling() -> None:
    """Volume is quadratic in the radius and linear in the height."""
    v = geometry.volume_prism(6, 1.0, 1.0)
    assert isclose(geometry.volume_prism(6, 2.0, 1.0), 4 * v)
    assert isclose(geometry.volume_prism(6, 1.0, 2.0), 2 * v)


def test_num_particles_total(parameters: dict[str, Any]) -> None:
    """Total count is the product of the lattice dimensions."""
    parameters.update(num_particles_x=3, num_particles_y=4, num_particles_z=5)
    assert geometry.num_particles_total(parameters) == 60


def test_num_B_particles_zero_mass_fraction(parameters: dict[str, Any]) -> None:
    """No type-B particles are generated for a zero mass fraction."""
    parameters["mass_fraction_B"] = 0
    assert geometry.num_B_particles(parameters, 100) == 0


def test_num_B_particles_identical_particles(parameters: dict[str, Any]) -> None:
    """For identical particle types, mass fraction equals number fraction."""
    parameters.update(
        r_B=parameters["r_A"],
        thickness_B=parameters["thickness_A"],
        density_B=parameters["density_A"],
        mass_fraction_B=0.25,
    )
    assert geometry.num_B_particles(parameters, 100) == 25


@pytest.mark.parametrize("mass_fraction_B", [0.1, 0.3, 0.5, 0.9])
def test_num_B_particles_recovers_mass_fraction(
    parameters: dict[str, Any], mass_fraction_B: float
) -> None:
    """The number of B particles reproduces the requested mass fraction."""
    parameters["mass_fraction_B"] = mass_fraction_B
    total = 100_000
    N_B = geometry.num_B_particles(parameters, total)
    m_A = geometry.particle_mass(parameters, ParticleType.A)
    m_B = geometry.particle_mass(parameters, ParticleType.B)
    actual = N_B * m_B / (N_B * m_B + (total - N_B) * m_A)
    assert isclose(actual, mass_fraction_B, rel_tol=1e-3)


def test_number_fraction_B(parameters: dict[str, Any]) -> None:
    """Number fraction is the number of B particles over the total."""
    total = geometry.num_particles_total(parameters)
    expected = geometry.num_B_particles(parameters, total) / total
    assert geometry.number_fraction_B(parameters) == expected


@pytest.mark.parametrize(
    ("fraction_B", "rnd", "expected"),
    [
        (0.0, 0.0, ParticleType.A),
        (0.0, 1.0, ParticleType.A),
        (1.0, 0.01, ParticleType.B),
        (0.2, 0.79, ParticleType.A),
        (0.2, 0.81, ParticleType.B),
    ],
)
def test_choose_particle_type(
    fraction_B: float, rnd: float, expected: ParticleType
) -> None:
    """Random numbers above the A fraction produce B particles."""
    assert geometry.choose_particle_type(fraction_B, rnd) == expected


def test_particle_dimensions_are_scaled(parameters: dict[str, Any]) -> None:
    """Dimensions are the per-type values multiplied by the scale."""
    s = parameters["scale"]
    assert geometry.particle_dimensions(parameters, ParticleType.A) == (
        s * parameters["r_A"],
        s * parameters["thickness_A"],
    )
    assert geometry.particle_dimensions(parameters, ParticleType.B) == (
        s * parameters["r_B"],
        s * parameters["thickness_B"],
    )


def test_particle_mass(parameters: dict[str, Any]) -> None:
    """Mass is density times the volume of the scaled prism."""
    r, h = geometry.particle_dimensions(parameters, ParticleType.B)
    expected = parameters["density_B"] * geometry.volume_prism(
        parameters["num_sides"], r, h
    )
    assert isclose(geometry.particle_mass(parameters, ParticleType.B), expected)


def test_lattice_positions(parameters: dict[str, Any]) -> None:
    """The lattice is centered on the z axis and starts above the floor."""
    parameters.update(num_particles_x=3, num_particles_y=2, num_particles_z=4)
    d = parameters["distance"]
    positions = geometry.lattice_positions(parameters)

    assert len(positions) == 24
    assert len(set(positions)) == 24
    xs, ys, zs = zip(*positions, strict=True)
    assert isclose(mean(xs), 0, abs_tol=1e-12)
    assert isclose(mean(ys), 0, abs_tol=1e-12)
    assert isclose(min(zs), d / 2)
    assert isclose(max(zs), d / 2 + 3 * d)
    assert sorted(set(xs)) == pytest.approx([-d, 0, d])


def test_piston_dimensions(parameters: dict[str, Any]) -> None:
    """The piston is narrower than the container by the slack and starts above."""
    L_piston, z_piston = geometry.piston_dimensions(parameters)
    assert isclose(L_piston, 0.99 * 2 * 1.5)
    max_z = 1.5 / 2 + 2 * 1.5
    assert isclose(z_piston, 1.1 * max_z + L_piston / 2)


def test_piston_dimensions_default_slack(parameters: dict[str, Any]) -> None:
    """Without slack, the piston is as wide as the container."""
    del parameters["container_piston_slack"]
    L_piston, _ = geometry.piston_dimensions(parameters)
    assert isclose(L_piston, 2 * 1.5)


def test_container_encloses_piston(parameters: dict[str, Any]) -> None:
    """The container is as wide as the lattice and taller than the piston."""
    L_piston, z_piston = geometry.piston_dimensions(parameters)
    Lxy, Lz = geometry.container_dimensions(parameters, L_piston, z_piston)
    assert isclose(Lxy, 2 * 1.5)
    assert Lz > z_piston + L_piston / 2
    assert Lxy > L_piston
