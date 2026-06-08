# MuJoCo Validation Report

Project: quadruped_mvp
Backend: metadata
Status: FAIL

## Scenarios
- stand (stand): PASS
- walk_flat (walk_flat): FAIL
- slope_8deg (slope): FAIL
- drop_80mm (drop): PASS

## Blockers
- walk_flat fell
- walk_flat body roll 13.5deg above 8deg
- walk_flat body pitch 10.2deg above 8deg
- walk_flat foot slip ratio 0.22 above 0.12
- walk_flat torque margin 8% below 20%
- slope_8deg body pitch 9.5deg above 8deg
- slope_8deg foot slip ratio 0.14 above 0.12
- slope_8deg torque margin 16% below 20%

## Next Actions
- reduce stride aggressiveness or adjust COM for walk_flat
- reduce lateral motion or widen stance for walk_flat
- move battery/COM or reduce acceleration for walk_flat
- increase stance time or adjust friction/contact parameters for walk_flat
- reduce gait load or choose stronger actuator for walk_flat
- reduce vertical motion and swing clearance for walk_flat
- move battery/COM or reduce acceleration for slope_8deg
- increase stance time or adjust friction/contact parameters for slope_8deg
- reduce gait load or choose stronger actuator for slope_8deg
- reduce vertical motion and swing clearance for slope_8deg
- adjust contact parameters or landing stiffness for drop_80mm

## Backend Note
- metadata mode: these are not real MuJoCo solver results
