# Wear/Fatigue Report

Project: quadruped_mvp
Status: FAIL

## Components
- gear: front_left_knee_reducer - FAIL
- gear: rear_left_hip_reducer - PASS
- bearing: front_left_knee_output_bearing - FAIL
- bearing: rear_left_hip_bearing - PASS
- foot_pad: front_foot_pad - FAIL
- foot_pad: rear_foot_pad - PASS
- joint_interface: front_knee_limit_stop - FAIL
- joint_interface: rear_hip_limit_stop - PASS
- harness: front_leg_motor_bundle - FAIL
- harness: body_power_harness - PASS
- connector: battery_xt30 - FAIL
- connector: imu_header - PASS

## Blockers
- front_left_knee_reducer contact stress 1320MPa above allowable 1100MPa
- front_left_knee_reducer estimated gear life 35h below target 50h
- front_left_knee_output_bearing bearing L10 life 28h below target 50h
- front_left_knee_output_bearing radial load 210N above limit 180N
- front_left_knee_output_bearing mounting error 1.6deg above 1deg
- front_foot_pad foot pad wear life 42h below target 50h
- front_knee_limit_stop limit impact 7.5J above 5J
- front_knee_limit_stop screw loosening risk is high
- front_leg_motor_bundle bend radius 18mm below required 25mm
- front_leg_motor_bundle motion envelope is not clear
- front_leg_motor_bundle has pinch risk
- battery_xt30 mating cycles 30 below target 50
- battery_xt30 missing vibration lock
- battery_xt30 missing strain relief

## Next Actions
- increase reducer size, improve material, or reduce knee torque for front_left_knee_reducer
- reduce load or choose longer-life reducer for front_left_knee_reducer
- select larger bearing or reduce radial load for front_left_knee_output_bearing
- add support or move load path closer to front_left_knee_output_bearing
- tighten bearing seat alignment for front_left_knee_output_bearing
- change foot pad material or make front_foot_pad easy to replace
- add damping or soften joint limit stop for front_knee_limit_stop
- add threadlocker, locking nut, or preload control for front_knee_limit_stop
- reroute front_leg_motor_bundle or increase service loop radius
- move front_leg_motor_bundle outside leg sweep envelope
- add clip, sleeve, or hard routing feature for front_leg_motor_bundle
- choose connector with higher mating cycle rating for battery_xt30
- add latch, retention clip, or locking connector for battery_xt30
- add strain relief near battery_xt30
