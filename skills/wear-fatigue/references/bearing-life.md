# Bearing Life

For MVP gating, bearing supplier or estimated `l10_life_hours` is compared
directly against `target_maintenance_hours`.

Blockers:

- `l10_life_hours < target_maintenance_hours`
- `radial_load_n > radial_load_limit_n`
- `axial_load_n > axial_load_limit_n`
- `mounting_error_deg > mounting_error_deg_max`

When supplier data is unavailable, estimate bearing life conservatively and mark
the source in the input file.
