# Parameters file

The simulation is configured with a JSON file. The value in the *Default* column is used
when a key is missing. Keys with no default are required.

## Particles

| Key | Default | Description |
|---|---|---|
| `num_sides` | | Number of sides of the polygonal faces (6 for hexagonal prisms) |
| `r_A`, `r_B` | | Circumscribed radius of the polygonal faces of type-A/B particles |
| `thickness_A`, `thickness_B` | | Height of the type-A/B prisms |
| `scale` | | Factor applied to all radii and thicknesses |
| `density_A`, `density_B` | | Densities of the two particle types (the particle mass is density × prism volume) |
| `mass_fraction_B` | | Mass fraction of type-B particles, in `[0, 1)` |
| `particle_friction` | | Friction coefficient of the particles |
| `particle_restitution` | | Restitution (bounciness) of the particles |
| `particle_damping` | | Linear damping of the particles |

## Initial lattice and container

Particles start on a regular `num_particles_x × num_particles_y × num_particles_z`
lattice. The container is open at the top and has a square cross-section whose side is
`num_particles_x × distance`.

| Key | Default | Description |
|---|---|---|
| `num_particles_x`, `num_particles_y`, `num_particles_z` | | Lattice dimensions; their product is the total number of particles |
| `distance` | | Lattice spacing |
| `container_wall_thickness` | `-0.2` | Thickness of the container walls (Blender *Solidify* modifier) |
| `use_piston` | | Drop a cubic piston on top of the particles to compact them |
| `mass_piston` | | Mass of the piston |
| `container_piston_slack` | `0.0` | Fraction by which the piston is narrower than the container |

## Simulation

| Key | Default | Description |
|---|---|---|
| `seed` | | Random seed for particle types and orientations; `null` draws a random seed |
| `gravity_field` | `[0, 0, -9.8]` | Gravity vector |
| `end_frame` | | Number of frames to simulate; the outputs are taken at this frame |
| `quit_on_finish` | `false` | Close Blender when the simulation finishes |

## Output

| Key | Default | Description |
|---|---|---|
| `save_blender_file` | `true` | Save `packing_<name>.blend` |
| `save_stl_file` | `true` | Save `packing_<name>.stl` |
| `save_json_file` | `true` | Save `packing_<name>.json` |
