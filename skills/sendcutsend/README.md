# sendcutsend — 开发者说明

build123d-cad 父技能下的钣金/激光出工子技能。把 mechanical 出的 STEP
变成 SendCutSend 能直接吃的 DXF,做 DFM 自检,出价格区间。

## 文件布局

```
skills/sendcutsend/
├── SKILL.md                                 # 入口,父级路由命中后读这个
├── README.md                                # 本文件
├── references/
│   ├── material-thickness-price.md          # 材料矩阵 + 厚度档 + 单价区间
│   └── dfm-rules-laser-bend.md              # DFM 规则 + 自检 checklist
├── scripts/
│   ├── step_to_dxf.py                       # STEP → DXF(投影 XY + BEND 层)
│   └── quote_estimator.py                   # DFM 自检 + 估价 + 询价 fallback
└── tests/
    ├── conftest.py
    └── test_smoke.py                        # 骨架 smoke
```

## 上手

```bash
# 1. 跑 smoke 验证骨架
cd /Users/liyijiang/.agents/skills/build123d-cad
pytest skills/sendcutsend/tests -m smoke

# 2. 端到端(需要 build123d + ezdxf)
python skills/sendcutsend/scripts/step_to_dxf.py path/to/sheet.step \
    --thickness 1.6 --material AL_5052 \
    --out /tmp/sheet_AL5052-1.6.dxf

python skills/sendcutsend/scripts/quote_estimator.py /tmp/sheet_AL5052-1.6.dxf \
    --thickness 1.6 --material AL_5052 \
    --finish anodize_black --quantity 5 \
    --out /tmp/sheet.quote.json
```

## 与其它子技能的串接

- 上游:`mechanical` 出钣金 STEP + `<part>.meta.json` sidecar(标 sheet_metal=True / 厚度 / 折弯方向)。
- 下游:`viewer` 把生成的 DXF 渲成预览图给 CEO 审。
- 父级编排:命中"激光切"/"钣金"/"DXF"/"SendCutSend" 关键词 → 进本子技能。

## 维护

- `references/material-thickness-price.md` 半年校准一次(SendCutSend 改价后)。
- `quote_estimator.py::quote_api()` 三级 fallback:public API 路径需要校准 endpoint,
  当前默认降级到 manual。
