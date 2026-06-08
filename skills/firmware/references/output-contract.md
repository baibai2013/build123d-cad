# Output Contract

`generate_project.py` writes:

- `firmware/project_manifest.json`
- `firmware/can_frames.md`
- `firmware/calibration.json`
- `reports/firmware_report.json`

`run_firmware_tests.py` writes:

- `reports/firmware_test_report.json`

`valid: false` means firmware is not ready for build freeze or hardware bring-up.
