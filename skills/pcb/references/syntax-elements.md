# tscircuit 语法 / 元素速查

> 权威:https://docs.tscircuit.com — 元素/属性大小写敏感,**不要编 props**。
> tscircuit = "React for Electronics":默认导出一个返回 JSX 的函数。

## 骨架(文件:`index.circuit.tsx`,实测入口名)

```tsx
export default () => (
  <board width="20mm" height="15mm">
    {/* 元件 + 连接 */}
  </board>
)
```

## 元素分类

| 类别 | 元素 |
|---|---|
| 容器 | `<board>` `<subcircuit>` `<group>` `<footprint>` `<schematicsection>` |
| 无源 | `<resistor>` `<capacitor>` `<inductor>` `<diode>` `<led>` `<crystal>` `<fuse>` `<battery>` |
| 有源/IC | `<chip>` `<mosfet>` `<transistor>` `<opamp>` |
| 连接 | `<connector>` `<pinheader>` `<jumper>` `<net>` `<netlabel>` `<port>` `<trace>` |
| PCB 图元 | `<via>` `<platedhole>` `<hole>` `<smtpad>` `<silkscreentext>` `<copperpour>` `<cutout>` |

## 关键属性

- **标识**:每个元件 `name="R1"`(唯一,trace 用它引脚)。
- **值**:`resistance="330"` / `capacitance="100nF"` / `inductance="10uH"`。
- **封装**:`footprint="0402"`(无源常用 0402/0603/0805);IC 用具体封装名。
- **PCB 布局**:`pcbX={mm} pcbY={mm} pcbRotation={deg} layer="top|bottom"`。
- **原理图布局**:`schX={} schY={} schRotation={} schOrientation=""`。
- **标准接口**:`<connector standard="usb_c" />`(内置,免 import)。

## 连接(trace + net)— 实测选择器带 `>`

```tsx
{/* 引脚到引脚 */}
<trace from=".U1 > .GPIO0" to=".LED1 > .anode" />
{/* 引脚到命名网络(电源/地走 net) */}
<trace from=".R1 > .pin2" to="net.GND" />
<trace from=".U1 > .VCC" to="net.VCC" />
```

- **selector 实测语法:`.<元件name> > .<引脚名>`(带 `>`)**;net 用 `net.<名>`。
  (`tsci init` 默认模板即 `.R1 > .pin1`。)
- 引脚名:无源用 `.pin1`/`.pin2`,LED 也可 `.anode`/`.cathode`(见 readable-netlist)。
- 电源/地一律走命名 net(`net.VCC` `net.GND`),别两两连。

## 分组(5+ 元件必做)

原理图可读性最关键的一步——按功能块分组:

```tsx
<group>
  <schematicsection schSectionName="Power" />
  {/* 该块元件 */}
</group>
```

## chip 自定义引脚

```tsx
<chip
  name="U1"
  footprint="soic8"
  pinLabels={{ pin1: "VCC", pin4: "GND", pin8: "OUT" }}
/>
```

## 参数化(对齐本仓库「参数顶置」规则)

```tsx
const W = 20, H = 15, R_LED = "330"
export default () => (
  <board width={`${W}mm`} height={`${H}mm`}>
    <resistor name="R1" resistance={R_LED} footprint="0402" />
  </board>
)
```

> 更多元素 + 完整属性表见官方 docs 的 builtin elements(~90 个),用到再查,别背。
