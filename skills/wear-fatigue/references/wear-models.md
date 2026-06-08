# Wear Models

The MVP uses conservative deterministic rules:

- Gear/reducer: block when `contact_stress_mpa > allowable_contact_stress_mpa`
  or `estimated_life_hours < target_maintenance_hours`.
- Foot pad: block when `estimated_wear_life_hours < target_maintenance_hours`
  or the pad is not replaceable.
- Joint interface: block when `limit_impact_j > limit_impact_j_max` or screw
  loosening risk is marked `high`.
- Harness: block when `min_bend_radius_mm < required_bend_radius_mm`, motion
  envelope is not clear, or pinch risk is present.
- Connector: block when mating cycles are below target, vibration lock is
  missing, or strain relief is missing.

Warnings are used for low margin conditions that are not immediate blockers.
