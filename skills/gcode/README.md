# gcode — 开发者说明

build123d-cad 父技能下的 FDM 切片子技能。把 mechanical 出的 STEP / STL 做打印前
几何预检 + 切片估时,产 `<part>.slice.json`(打印分钟 / 丝长 / 丝重 / 层数)。
定位:mechanical 管"画对",gcode 管"打得出 + 打多久 + 多少料"。

## 脚本

- `scripts/slice_precheck.py` — 当前 P1 唯一实跑脚本,两段合一:
  1. **overhang 几何预检**:零依赖纯 Python 解析 STL 面法线,从竖直量角(壁 0° /
     天花 90°),有支撑阈值 45° / 无支撑 30°,排除贴床面;超阈写 violations 不静默。
  2. **OrcaSlicer 切片估时**:调 OrcaSlicer CLI 切片,解析估时 / 丝长 / 丝重
     (缺密度时按 cm³×密度兜底) / 层数。切片器不在 host → 报错给 brew 命令,
     **不静默降级**。

> SKILL.md「主流程」列的 precheck / step_to_stl / slice.sh / parse_gcode 是完整蓝图;
> P1 先把 overhang 预检 + 估时整合进 `slice_precheck.py`,其余按需再拆。

## 依赖

- OrcaSlicer(切片估时必需):`brew install --cask orcaslicer`,本机验过 2.3.2。
  注:运行时拷系统机型预设并置 `use_relative_e_distances=0`,绕开 2.3.2 的
  `layer_gcode G92 E0` 校验坑;层高 / 填充 / 支撑用 flag override。
- overhang 预检纯标准库,无第三方依赖。

## 测试

```bash
cd ~/.agents/skills/build123d-cad
pytest skills/gcode/tests/                 # 14 离线纯函数,秒级
RUN_SLOW=1 pytest skills/gcode/tests/      # +1 真切片(@slow,无 orca 自动 skip)
```

本机实测:立方体 ~25 min / 4.3 g;桌板悬垂 1600 mm² / 90° 检出;立方体底面 0 误报。

## 产物 / handoff

- 产物 `output/<task>/<part>.slice.json`,接口见 `../../shared/handoff-protocols.md`。
- 上游 mechanical(STEP)→ 本 skill;下游 bambu-labs(推打印)/ viewer(看 toolpath)。
