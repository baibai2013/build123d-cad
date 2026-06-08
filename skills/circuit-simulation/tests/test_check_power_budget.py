from __future__ import annotations

import importlib.util
import json
import sys


def _load_module(subskill_root, script_name):
    path = subskill_root / "scripts" / script_name
    scripts_dir = str(path.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(script_name.replace(".py", ""), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_example_writes_blocking_reports(subskill_root, example_project_copy):
    checker = _load_module(subskill_root, "check_power_budget.py")
    payload = checker.run(example_project_copy)
    assert payload["valid"] is False
    assert payload["blockers"]
    assert payload["checks"]["erc_pass"] is False
    report = json.loads((example_project_copy / "reports" / "circuit_check.json").read_text(encoding="utf-8"))
    assert report["valid"] is False
    assert (example_project_copy / "reports" / "power_budget.json").exists()
    thermal = json.loads((example_project_copy / "reports" / "thermal_report.json").read_text(encoding="utf-8"))
    assert thermal["valid"] is False


def test_conservative_circuit_passes(subskill_root, tmp_path):
    checker = _load_module(subskill_root, "check_power_budget.py")
    (tmp_path / "circuit_requirements.yaml").write_text(
        'version: "1.0"\n'
        "checks:\n"
        "  erc_pass: true\n"
        "  drc_pass: true\n"
        "battery:\n"
        "  voltage_nominal_v: 24\n"
        "  max_current_a: 60\n"
        "  fuse_current_a: 40\n"
        "safety:\n"
        "  emergency_stop: true\n"
        "  reverse_polarity_protection: true\n"
        "  undervoltage_cutoff_v: 19\n"
        "  tvs_diode: true\n"
        "  bulk_capacitance_uf: 2200\n"
        "power_rails:\n"
        "  - name: logic_5v\n"
        "    voltage_v: 5\n"
        "    regulator_current_a: 3\n"
        "    load_current_a: 1.5\n"
        "    efficiency_pct: 90\n"
        "motor_drivers:\n"
        "  - name: leg_driver_bank\n"
        "    count: 12\n"
        "    peak_current_a_each: 2\n"
        "    continuous_current_a_each: 0.7\n"
        "    driver_peak_limit_a_each: 4\n"
        "    driver_continuous_limit_a_each: 2\n"
        "thermal:\n"
        "  ambient_c: 30\n"
        "  components:\n"
        "    - name: buck_5v\n"
        "      dissipation_w: 0.7\n"
        "      thermal_resistance_c_w: 35\n"
        "      max_temp_c: 85\n",
        encoding="utf-8",
    )
    payload = checker.run(tmp_path)
    assert payload["valid"] is True
    assert payload["blockers"] == []
    assert payload["battery"]["peak_current_margin_pct"] >= 20
