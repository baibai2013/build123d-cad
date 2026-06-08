# Electronics BOM Selection Rationale

Project: quadruped_mvp
Status: FAIL
Mode: offline_curated_catalog

## Selected Parts
- mcu: STM32G431CBT6 x1 (jlcpcb_basic)
- motor_driver: TMC6300-LA x12 (jlcpcb_extended)
- motor_driver: TMC6300-LA x12 (jlcpcb_extended)
- encoder: AS5047P x12 (jlcpcb_extended)
- imu: ICM-42688-P x1 (jlcpcb_extended)
- buck_regulator: MP1584EN x2 (jlcpcb_basic)
- battery_connector: XT30PW-M x1 (manual)

## Blockers
- best motor_driver candidate TMC6300-LA does not meet required constraints

## Next Actions
- select higher rated motor_driver part or relax constraints
