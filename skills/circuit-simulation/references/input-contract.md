# Input Contract

The MVP reads a project directory containing `circuit_requirements.yaml`.

```yaml
version: "1.0"
checks:
  erc_pass: false
  drc_pass: true

battery:
  voltage_nominal_v: 24
  max_current_a: 30
  fuse_current_a: 25

safety:
  emergency_stop: false
  reverse_polarity_protection: true
  undervoltage_cutoff_v: 18
  tvs_diode: false
  bulk_capacitance_uf: 470

power_rails:
  - name: logic_5v
    voltage_v: 5
    regulator_current_a: 2
    load_current_a: 1.8
    efficiency_pct: 86

motor_drivers:
  - name: leg_driver_bank
    count: 12
    peak_current_a_each: 4
    continuous_current_a_each: 1.4
    driver_peak_limit_a_each: 3.5
    driver_continuous_limit_a_each: 1.2

thermal:
  ambient_c: 35
  components:
    - name: buck_5v
      dissipation_w: 1.4
      thermal_resistance_c_w: 55
      max_temp_c: 85
```

All currents use amperes, power uses watts, and temperatures use Celsius.
