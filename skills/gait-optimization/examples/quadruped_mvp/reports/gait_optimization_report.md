# Gait Optimization Report

Project: quadruped_mvp
Status: FAIL
Current score: 36
Best candidate: safer_trot (100)

## Blockers
- stand stable time 21s below target 30s
- flat walk fell
- body roll 11deg above limit 8deg
- body pitch 9deg above limit 8deg
- foot slip ratio 0.18 above limit 0.12
- joint torque margin 12% below target 20%

## Warnings
- average speed 0.43m/s below target 0.5m/s
- cost of transport 3.1 above limit 2.5

## Next Actions
- lower body height or increase stance duty factor
- reduce stride length and increase duty factor
- reduce lateral body motion and stance width error
- move COM or reduce acceleration/stride aggressiveness
- reduce stride length or increase stance time
- reduce gait aggressiveness or increase actuator torque
- increase speed only after stability blockers are cleared
- reduce vertical motion and avoid excessive swing clearance
