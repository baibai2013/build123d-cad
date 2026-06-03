---
name: build123d-cad-gcode
description: |
  build123d-cad 的 FDM 切片子技能。STEP/STL → .gcode 一键命令、估时与
  材料用量解析、切片前几何预检(壁厚 / overhang / bridge / 公差)。
  触发词:切片、slice、G-code、FDM、3D 打印、PrusaSlicer、OrcaSlicer、
  SuperSlicer、打印估时、悬垂、桥接、支撑、PLA、PETG、层高、infill、gyroid。
  本子技能不做:实际打印控制(→ bambu-labs)、CNC / 五轴(范围外)、
  SLA / SLS(P3)。
owner: mechanical
status: ready
phase: P1
since: 2026-06-02
---

# build123d-cad · gcode 子技能

把 mechanical 出的 STEP / STL 喂给本 skill,出 `.gcode` + `.slice.json`(打印分钟、丝长、丝重)。
切片前先跑几何预检,fail-fast 给修改建议,不让用户去机器上才发现支撑爆炸。

> 一句话定位:mechanical 管"画对",gcode 管"打得出 + 打多久 + 多少料"。
>
> 不重写切片算法,只调用 PrusaSlicer / OrcaSlicer / SuperSlicer CLI。

---

## AI 执行准入

读本 SKILL.md 的"主流程 / 决策表 / 默认参数",**不**直接读 references/ 拼;
references/ 只作规则查询表。跨子技能走 [`../../shared/handoff-protocols.md`](../../shared/handoff-protocols.md) 文件接口,不互调函数。
切片器 CLI 不在 host → 报错给 brew 命令,**不静默降级**。

---

## 主流程

```
mechanical 出 STEP
       │
       ▼
[1] precheck.py        — 壁厚 / overhang / bridge / 最小特征预检
       │
       ├─ 失败 → 写 violations.json → handoff 回 mechanical
       │
       └─ 通过 ▼
[2] step_to_stl        — build123d Mesher(skip 若已是 STL)
       │
       ▼
[3] slice.sh           — 调 PrusaSlicer / OrcaSlicer / SuperSlicer
       │
       ▼
[4] parse_gcode.py     — 解析 .gcode 末尾注释:估时 + 丝长 + 丝重
       │
       ▼
[5] handoff            — bambu-labs 推打印 / viewer 看 toolpath
```

---

## 一句话用法

```bash
# 默认参数:0.2 mm 层高 / PLA 210 °C / 20% gyroid 填充 / 0.4 nozzle
bash skills/gcode/scripts/slice.sh /abs/path/part.step

# 自定义
bash skills/gcode/scripts/slice.sh /abs/path/part.step \
  --out /abs/path/output --layer 0.2 --infill 20 \
  --material PLA --printer P1S --slicer prusa
```

stdout 末尾 1 行 JSON 摘要;`.gcode` + `.slice.json` 落到 `--out`(默认 STEP 同目录)。

```python
from gcode_slice import slice_part
result = slice_part("/abs/path/part.step", layer_mm=0.2, infill_pct=20)
# {"gcode": ".../part.gcode", "minutes": 47, "filament_g": 23.4, ...}
```

---

## 切片器选型决策

| 切片器 | CLI 友好度 | 配置生态 | macOS 安装 | 何时选 |
|---|---|---|---|---|
| **PrusaSlicer** | ★★★★★ 一行 .ini 就跑 | 官方 + Prusa MK / Mini 全 | `brew install --cask prusaslicer` | 默认首选;CI 流水线;只 STL 输入 |
| **OrcaSlicer** | ★★★ 需 process+machine+filament JSON 三件套 | Bambu / Voron / Klipper 全 | `brew install --cask orcaslicer` | Bambu / 多色 / 已有 .3mf 工程 |
| **SuperSlicer** | ★★★★ 与 PrusaSlicer .ini 兼容 | 顶层细节(自适应层高 / fuzzy skin) | `brew install --cask superslicer-fork` | 表面质量优先 |

**判定一行**:有 `.3mf` 工程 → OrcaSlicer;只有 STL/STEP 想脚本化 → PrusaSlicer;表面要漂亮 → SuperSlicer。

`scripts/slice.sh` 自动按 `--slicer` flag / `$SLICER` env / 路径里能找到的第一个跑;
找不到则报错并给安装提示,**不静默降级**。

---

## 默认打印参数(可被 flag 覆盖)

| 项 | 默认值 | 改的入口 |
|---|---|---|
| 层高 | 0.2 mm | `--layer` |
| 喷嘴温度(PLA) | 210 °C | `--material` 切到 PETG/ABS 时随之换 |
| 热床温度(PLA) | 60 °C | 同上 |
| 填充类型 | gyroid | profile ini 内 `fill_pattern` |
| 填充密度 | 20% | `--infill` |
| 外壁圈数 | 3 | profile ini |
| 顶 / 底层数 | 4 / 4 | profile ini |
| 喷嘴 | 0.4 mm | `--printer` 切到 0.6 / 0.8 时随之换 |
| 支撑 | 自动(only touching buildplate) | `--support none\|auto\|tree` |

材料对照(温度自动套):

| 材料 | 喷嘴 | 热床 | 风扇 | 备注 |
|---|---|---|---|---|
| PLA | 210 | 60 | 100% | 默认 |
| PETG | 240 | 80 | 50% | 关闭桥接超驰风扇 |
| ABS | 240 | 100 | 0–30% | 必须封闭机器 |
| TPU 95A | 220 | 50 | 100% | 慢速 < 25 mm/s |

---

## 切片前几何预检

```bash
python skills/gcode/scripts/precheck.py /abs/path/part.step \
    --layer 0.2 --nozzle 0.4 \
    --out output/<task>/part.precheck.json
```

| 检查项 | 阈值 / 规则 | failure 建议 |
|---|---|---|
| 最小壁厚 | `≥ 2 × nozzle`(0.4 → 0.8 mm) | "wall ≥ 0.8 mm 或换 0.3 nozzle" |
| Overhang 角度 | 自动支撑临界 ≤ 45°;无支撑 ≤ 30° | "倒角 / 加 chamfer / 改朝向" |
| 桥接长度 | ≤ 10 mm 无支撑可桥;> 25 mm 必须支撑 | "拆模 / 加临时筋 / 改朝向" |
| 最小特征 | ≥ 0.4 mm(单线宽) | "字号放大 / depth 加深 / 换细喷嘴" |
| 总尺寸 | ≤ 打印机 build volume(查 `--printer`) | "切件 / 旋转 / 换大机器" |
| 第一层接触面 | ≥ 100 mm² 或加 brim | "auto-add brim / 重新摆放" |

完整阈值表 + 反例:[references/fdm-design-rules.md](references/fdm-design-rules.md)。

输出格式:

```json
{
  "ok": false,
  "violations": [
    {"rule": "min_wall", "value_mm": 0.6, "threshold_mm": 0.8,
     "where": "rib at z=12.4",
     "suggestion": "wall ≥ 0.8 mm 或换 0.3 nozzle"}
  ]
}
```

---

## 估时与材料解析

切片器在 `.gcode` 末尾注释里写好真值,本 skill 不做仿真,只做解析。

PrusaSlicer / SuperSlicer 注释格式(`scripts/parse_gcode.py` 处理):

```
; estimated printing time (normal mode) = 1h 47m 23s
; filament used [mm] = 4523.18
; filament used [g] = 23.4
```

OrcaSlicer 格式略不同(`total estimated time` / `total filament length`),同一脚本兼容。

输出 `<part>.slice.json`:

```json
{
  "gcode": "/abs/path/part.gcode",
  "minutes": 107,
  "filament_mm": 4523.18,
  "filament_g": 23.4,
  "layer_count": 142,
  "first_layer_height_mm": 0.2,
  "slicer": "PrusaSlicer-2.9.5",
  "profile": {"layer": 0.2, "infill_pct": 20, "material": "PLA"}
}
```

---

## handoff(跨子技能)

| 方向 | 上 / 下游 | 接口 |
|---|---|---|
| ← mechanical | `output/<task>/<part>.step` | 调本 skill 即可,自动 STEP→STL |
| ← parts-catalog | 标准件 STEP | 一般不切片(买的);仅打印外壳 / 适配件 |
| → bambu-labs | `<part>.gcode` | `bambu-labs.send(<part>.gcode, printer=...)` |
| → viewer | `<part>.gcode` | `viewer.start(<part>.gcode)` 出 toolpath ribbon URL |

完整路径约定:[`../../shared/handoff-protocols.md`](../../shared/handoff-protocols.md) — gcode 产物落 `output/<task>/<part>.{gcode,slice.json}`。

STEP→STL 转换走父技能 build123d 环境(`scripts/slice.sh` 内部:能 `import build123d` 就用 `Mesher`;否则报错并提示 `pip install build123d`)。

---

## 输出物路径约定

```
output/<task>/
├── <part>.gcode             # 切片产物
├── <part>.slice.json        # 估时 + 材料解析
└── <part>.precheck.json     # 几何预检报告(失败时含 violations)
```

不在本 skill 目录下放 output(父级 SKILL.md 第 158 行约定)。

---

## 验证 + 测试

```bash
# 端到端 demo:任一 STEP → .gcode + 估时
STEP=/Users/liyijiang/work/build123d-parts-lib/build123d_parts_lib/parts/seals/cache/oring.step
bash skills/gcode/scripts/slice.sh "$STEP" --out /tmp/gcode-demo
cat /tmp/gcode-demo/oring.slice.json    # 预期 minutes>0、filament_g>0

# 单元测试
cd skills/gcode && pytest tests/ -v
# - test_smoke.py    P0 骨架 + SKILL.md ≤ 250 行
# - test_slice_real(P1)真 STEP → .gcode(host 没切片器 skip)
# - test_precheck(P1)0.3 mm 薄壁 → violations 非空
```

---

## 角色规则 + 不做什么

1. **不重写算法**,只调切片器 CLI。
2. **预检先于切片**,failures 回环给 mechanical,不擅自改几何。
3. **真值优先**,估时读 `.gcode` 注释,不仿真。
4. **fail loud**:切片器没装就报错给安装命令,不静默降级。
5. **数据落** `output/<task>/`,不污染 skill 目录。

不做:实际打印控制(→ bambu-labs)、CNC / 激光 / 五轴、SLA / SLS / 金属(P3)、自家造切片器、选材推荐。

---

## references/

- `slicer-cli-cheatsheet.md` — PrusaSlicer / OrcaSlicer / SuperSlicer CLI 参数速查 + 配置 ini 怎么导出
- `fdm-design-rules.md` — 壁厚 / 悬垂 / 桥接 / 最小特征 / 公差表 + 高频反例

外部:PrusaSlicer CLI https://help.prusa3d.com/article/command-line-slicing_1675;OrcaSlicer `/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer --help`。
