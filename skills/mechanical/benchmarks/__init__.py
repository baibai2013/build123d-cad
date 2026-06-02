"""mechanical 子技能 benchmarks 套件。

P0-9 落地:10 题(题面见 prompts/),fast 子集 = #1/#2/#3 (PR 必跑),full = 全部。

入口:
    python -m benchmarks.run_all --suite fast
    python -m benchmarks.run_all --suite full
    python -m benchmarks.compare_golden --case calibration_block

依赖:build123d 0.10+(在 ~/work/build123d-parts-lib/.venv/ 内)
设计文档:share/build123d-cad改造/07-测试与验证基建.md §4
"""
