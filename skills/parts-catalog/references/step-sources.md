# STEP 来源 + License 速查

回答两个问题:
1. **「这个件去哪儿下 STEP?」** —— 看「来源排序」表。
2. **「下了能用吗?」** —— 看「license 红线」流程图。

> 所有外部 STEP 落盘到 `output/<task>/parts/`,**必须配套**写 `<id>.LICENSE.txt` + `manifest.yaml`。

---

## 来源排序(按 license 友好度 + 件源覆盖度)

| # | 来源 | URL | 覆盖范围 | License 默认 | 入 parts-lib 仓 |
|---|---|---|---|---|---|
| 1 | 厂商官网 | SKF / NSK / Bosch Rexroth / Festo / SMC / IGUS / Misumi / Maxon / Faulhaber | 自家全产品线 | 「For evaluation / engineering use」 | 视具体声明,通常 ✅ 装配引用,❌ 二次分发 |
| 2 | StepperOnline | https://www.stepperonline.com | NEMA8/14/17/23/34 步进 + 驱动 | 自由下载 | ✅(注明出处) |
| 3 | Misumi | https://us.misumi-ec.com | 工厂自动化件、铝型材、轴承座、导轨 | 商用 OK | ✅(保留 Misumi 编号) |
| 4 | TraceParts | https://www.traceparts.com | 海量厂商件库,注册免费 | 商用 OK,**保留水印里的来源 URL** | ✅ |
| 5 | 3DContentCentral | https://www.3dcontentcentral.com | SolidWorks 生态,500 万+ 件 | 商用 OK,**注明出处** | ✅ |
| 6 | GrabCAD | https://grabcad.com/library | 用户上传(品质参差) | **逐件确认**,默认非商用 | ⚠️ 仅 license 明确友好者 |
| 7 | McMaster-Carr | https://www.mcmaster.com | 紧固件/管件/原材料/工具,几何精确 | 商用免费下载,**不可二次分发** | ❌ 不入仓,只本地装配引用 |
| 8 | GitHub 开源仓 | search:`<part-name> filename:*.step` | 偶有零散 | 看仓库 LICENSE | ✅ MIT/BSD/Apache-2.0/Unlicense/CC0 才入仓 |

> **机器人方向常用栈**:四足关节 → StepperOnline(步进) + 厂商(轴承,SKF/NSK 优先) + Misumi(导轨/型材) + GrabCAD(舵机/IMU/相机壳)。

---

## License 红线(判定流程图)

```
下载到 STEP / 引入第三方件
        │
        ▼
[Q1] 来源页 / 文件 / README 写明 license 了吗?
        │
   否 ──┴── 是
   │           │
   ▼           ▼
[BLOCK]    [Q2] 是 MIT / BSD / Apache-2.0 / Unlicense / CC0 / 厂商授权?
不可用       │
不入仓        ├─ 是 ──→ 可入 parts-lib(走 promotion 流程)
不本地引用    └─ 否 ──→ [Q3] 写的是 "personal use" / "non-commercial" / "evaluation only"?
                            │
                       ├─ 是 ──→ ⚠️ 只本地装配引用,不入仓,manifest.yaml 标 RESTRICTED
                       └─ 否 ──→ 不确定 → 当 BLOCK 处理,问用户/法务
```

### 红线条目(违反 = 装配文件需删除 + parts-lib 拒收)

- 不标 source URL → 一律不可用。
- 不标 license 或 license 模糊 → 不入 parts-lib,本地装配也最多临时用。
- McMaster STEP / 厂商「For evaluation only」STEP **不可推到公有仓**(包括 build123d-parts-lib)。
- GrabCAD 默认假设非商用,要 ✅ 必须看到 uploader 写明 CC0 / MIT / Public Domain。

### 安全名单(可放心入仓)

- MIT / BSD-2 / BSD-3 / Apache-2.0 / Unlicense / CC0 / WTFPL / 0BSD / ISC。
- 厂商授权里**白纸黑字写「commercial use allowed」或「royalty-free distribution」**(罕见但有,如 IGUS dryspin)。

---

## 产物清单(落盘约定)

每个外部 STEP 落到 `output/<task>/parts/` 时,产生 3 个文件:

```
output/<task>/parts/
  ├── <part_id>.step
  ├── <part_id>.LICENSE.txt
  └── manifest.yaml          # 多件共用一个,append 即可
```

### `<part_id>.LICENSE.txt` 模板

```
Part:        608ZZ deep groove ball bearing
Source:      https://www.skf.com/group/products/rolling-bearings/ball-bearings/deep-groove-ball-bearings/productid-608-2Z
License:     SKF — Engineering use; redistribution NOT permitted.
Downloaded:  2026-06-02
Sha256:      <填 sha256sum 输出>
Notes:       仅本项目装配使用;不得提交到 build123d-parts-lib 公有仓。
```

### `manifest.yaml` 模板

```yaml
# output/<task>/parts/manifest.yaml — 装配里所有外部 STEP 的元数据
parts:
  608zz_skf:
    file: 608zz_skf.step
    source_url: https://www.skf.com/...
    license: "SKF eval — no redistribution"
    license_class: RESTRICTED          # OPEN | PERMISSIVE | RESTRICTED | UNKNOWN
    sha256: 0a1b2c...
    downloaded: 2026-06-02
    promotable_to_parts_lib: false     # license 不允许 → 永远 false

  bracket_xyz:
    file: bracket_xyz.step
    source_url: https://github.com/foo/bar/blob/main/parts/bracket.step
    license: MIT
    license_class: PERMISSIVE
    sha256: f3e4d5...
    downloaded: 2026-06-02
    promotable_to_parts_lib: true      # 走 promotion → parts-lib PR
```

> mechanical 子技能拿到装配任务时,**先读 manifest.yaml** 确认所有件 license 状态,再决定是否能进 git 仓库(RESTRICTED 件需 `.gitignore`)。

---

## 厂商 STEP 下载技巧(踩过的坑)

- **SKF / NSK**:网站需选轴承型号 → "CAD download" 里有 STEP / IGES / STL 三选一,优先 STEP AP214。
- **Bosch Rexroth**:导轨/丝杠去 mediadirectory.boschrexroth.com,要注册但免费。
- **Misumi**:每个件页面右侧 "3D CAD" 按钮,选 STEP 格式。它会**按你输的尺寸参数动态生成 STEP**(L=100 vs L=120 给你两个文件)。
- **Festo / SMC**:气缸/阀岛走 partcommunity.com(TraceParts 旗下),登录后下载。
- **StepperOnline**:每个步进型号详情页有 "Download" 区,直接给 STEP/STP。
- **GrabCAD**:搜索时加引号锁型号,例 `"NEMA17"`。点进作品页**先看右侧 license 标签**再决定要不要下。

---

## 反求兜底:厂家无 STEP / license 不允许

如果一个件:
- 厂家不给 STEP(很多杂牌零件、国产舵机)
- 给的 STEP license 不允许在公开项目里用

→ 走 mechanical 子技能从规格书 PDF / 卡尺实测参数化建模(参考物建模 playbook):
- mechanical 的 `protocols/reference-product-playbook.md` 是流程权威。
- 入库 promotion 时**自家建模**的件 license 默认 MIT(项目政策)。
- SG90 已有先例:`parts/servos/sg90.py` 即从 `references/sg90-step/sg90_ref.step` 反求 + 卡尺校核而来,license MIT。

---

## 一句话总结

> **能用 build123d-parts-lib import 就别下 STEP;必须下 STEP 优先厂商官网 + 安全名单 license;McMaster 只能本地用、不能入仓;license 不明的一律 BLOCK,不要赌。**
