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
    checker = _load_module(subskill_root, "check_pcb_fit.py")
    payload = checker.run(example_project_copy)
    assert payload["valid"] is False
    assert payload["blockers"]
    assert payload["flex"]["estimated_board_flex_mm"] > 0
    report = json.loads((example_project_copy / "reports" / "pcb_fit.json").read_text(encoding="utf-8"))
    assert report["valid"] is False
    assert "mounting" in report
    assert (example_project_copy / "reports" / "pcb_reliability_report.json").exists()
    connector_report = json.loads(
        (example_project_copy / "reports" / "connector_clearance.json").read_text(encoding="utf-8")
    )
    assert connector_report["valid"] is False
    assert connector_report["connectors"][0]["blockers"]


def test_supported_board_passes(subskill_root, tmp_path):
    checker = _load_module(subskill_root, "check_pcb_fit.py")
    (tmp_path / "pcb_mechanical.yaml").write_text(
        'version: "1.0"\n'
        "board:\n"
        "  name: pass_board\n"
        "  width_mm: 70\n"
        "  length_mm: 80\n"
        "  thickness_mm: 1.6\n"
        "  mass_g: 28\n"
        "  enclosure_clearance_mm: 3\n"
        "  edge_clearance_mm: 3\n"
        "mounting:\n"
        "  hole_count: 4\n"
        "  standoff_count: 4\n"
        "  hole_edge_distance_mm: 3.5\n"
        "  max_unsupported_span_mm: 48\n"
        "loads:\n"
        "  vibration_g: 3\n"
        "  drop_height_m: 0.2\n"
        "connectors:\n"
        "  - name: battery_xt30\n"
        "    kind: power\n"
        "    height_mm: 8\n"
        "    clearance_mm: 3\n"
        "    nearest_standoff_mm: 18\n"
        "    cable_bend_radius_mm: 30\n"
        "    cable_min_bend_radius_mm: 25\n"
        "    strain_relief: true\n",
        encoding="utf-8",
    )
    payload = checker.run(tmp_path)
    assert payload["valid"] is True
    assert payload["blockers"] == []
    assert payload["scores"]["fit"] == 25
