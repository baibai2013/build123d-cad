# 加一个新子技能

以后扩 PCB / 电子 / 固件等域，流程固定如下。

## 步骤

```bash
cd ~/.agents/skills/build123d-cad
mkdir -p skills/<name>/{references,scripts,tests}
touch skills/<name>/{SKILL.md,README.md} skills/<name>/tests/conftest.py
```

然后改 3 处共享配置：

1. **父 `SKILL.md`** 路由表加一行（子技能名 / 触发关键词 / 路径）。
2. **`shared/multi-skill-router.md`** 关键词表加一行。
3. **`shared/dependencies.md`** 标注上下游依赖；若有跨子技能交换，在 **`shared/handoff-protocols.md`** 加 handoff 条目。

## 子技能 SKILL.md 最小骨架

```markdown
# <name> — 一句话定位

## 何时用
（触发关键词 / 典型需求）

## 流程
（步骤 / 命令）

## 产物
（输出路径约定，对齐 shared/handoff-protocols.md）
```

## 验收

- `test -f skills/<name>/SKILL.md && test -d skills/<name>/tests`
- `cd skills/<name> && pytest tests/` 至少 1 个 smoke test 通过。
- 父 `SKILL.md` 行数仍 ≤220。

## 占位规范（WIP 子技能）

未落地的域（如 P3 的 pcb/electronics-bom）只放 `SKILL.md`(写 "WIP" + 路线图) + `README.md` + 空 `references/`(`.gitkeep`)，路由表标 `(WIP)`。
