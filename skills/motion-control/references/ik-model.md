# IK Model

The MVP uses a 2-link planar leg:

- link 1: `thigh_mm`
- link 2: `shank_mm`
- target: `(x_mm, z_mm)`

Blockers:

- Target distance is greater than `thigh + shank`.
- Target distance is less than `abs(thigh - shank)`.
- Computed hip/knee pitch is outside declared joint limits.

This is sufficient to catch obvious geometry and gait target problems before
simulation. Full 3D hip ab/adduction, Jacobian control, and singularity handling
are future work.
