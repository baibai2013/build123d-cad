# skidl 快速上手(写第一份原理图)

> skidl(devbisme/skidl)= Pythonic 网表 DSL,与 build123d「代码即模型」同调性。
> pcb 子技能用它**从零写新原理图**(出 `.net`),批量改既有工程走 `batch_edit.py`(kicad-skip)。
> 安装:`pip install skidl`(装进 CAD 环境,非 company 生产 venv)。

## 最小设计脚本(design.py)

```python
from skidl import Part, Net, generate_netlist

# 元件:lib + name + 封装(footprint)
r1 = Part("Device", "R", value="10k", footprint="Resistor_SMD:R_0402_1005Metric")
c1 = Part("Device", "C", value="1uF", footprint="Capacitor_SMD:C_0402_1005Metric")

# 网络:连脚
vcc, gnd = Net("VCC"), Net("GND")
vcc += r1[1]
r1[2] += c1[1]
c1[2] += gnd

# 出网表(本脚本由 sch_from_skidl.py 调,自动写 .net)
generate_netlist()
```

跑:`python sch_from_skidl.py design.py` → `design.net`

## 接 electronics-bom 的料(文件接口,不互引用)

`sch_from_skidl.py --library library.json` 会把 electronics-bom 选好的料经
环境变量 `PCB_LIBRARY_JSON` 传进来。设计脚本可选读它给 footprint 赋值:

```python
import json, os
lib = json.loads(os.environ.get("PCB_LIBRARY_JSON", "{}"))
fp = lib.get("ESP32-WROOM-32E", {}).get("footprint", "")
u1 = Part("RF_Module", "ESP32-WROOM-32", footprint=fp)
```

> 这是 06 §3.3a.2「零互引用红线」的解法:pcb **不** subprocess 调
> electronics-bom,只读它落盘的 `library.json`(由 agent/父 SKILL 编排先生成)。

## .net → .kicad_sch(GUI 步骤)

skidl 出的是网表 `.net`,**没有**对应 kicad-cli 子命令把它变 `.kicad_sch`。
导入走 KiCad GUI:
1. `new_project.py <name>` 起空白工程
2. eeschema 打开 `<name>.kicad_sch` →「工具 → 从网表更新原理图」选 `.net`
3. 元件落图后手动 layout(或交给布局工程师)

CI / agent 场景一般到 `.net` 为止即可(验证连接正确性);需要图形原理图时才走 GUI 导入。

## 与其他工具的分工(06 §4.2)

| 场景 | 工具 |
|---|---|
| 从零写新原理图 | **skidl**(本文) |
| 批量改既有工程(换封装/电源符号) | **kicad-skip** → `batch_edit.py` |
| 走完整 GUI 插件流程 | kicad-python IPC(9.x 稳定后,见 kicad-9-ipc-status.md) |
