# benchmarks prompts

每题一个 `<NN>_<name>.md`,内容是给 agent-eval 直接喂的 CN prompt + 验收要点。

完整规格(中英文 prompt + 验收维度 + golden 关键字段 + 难度)见
`share/build123d-cad改造/examples/benchmarks-prompts.md`。

| # | name | suite | difficulty | timeout |
|---|---|---|---|---|
| 1 | calibration_block | fast | ★ | 30 s |
| 2 | flange_4hole | fast | ★★ | 45 s |
| 3 | l_bracket | fast | ★★ | 45 s |
| 4 | stepped_shaft | full | ★★★ | 60 s |
| 5 | enclosure_box | full | ★★★ | 90 s |
| 6 | clevis_yoke | full | ★★★ | 60 s |
| 7 | radial_cylinder | full | ★★★★ | 90 s |
| 8 | impeller_3blade | full | ★★★★ | 120 s |
| 9 | spiral_staircase | full | ★★★★★ | 90 s |
| 10 | planetary_gear_set | full | ★★★★★ | 150 s |
