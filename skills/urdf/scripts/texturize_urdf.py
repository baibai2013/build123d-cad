#!/usr/bin/env python3
"""一键把 URDF 的 STL 网格替换为带纹理的 GLB(Y-up + 保持毫米 + 按 mesh 分木种),输出纹理 URDF。

用法:
    python texturize_urdf.py <in.urdf> [--out OUT.urdf] [--meshdir wood_meshes]
                             [--scale 1.0] [--tones ring=oak,sun=cherry,...]

约束已内置(见 references/textures.md):
  - GLB 预转 Y-up(viewer 会 Y-up→Z-up)
  - 顶点保持 STL 源单位(通常毫米),scale=1.0;viewer 对 URDF GLB 按 unitScale=1 渲染(不再 ×1000)
  - 引用改为 GLB 并写入 scale="0.001 0.001 0.001"(把毫米网格接到米制关节原点)
默认每个不同 mesh 轮换木种以便区分;--tones 可逐个指定(键 = STL 去扩展名的 basename)。
"""
import sys, os, re, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stl_to_wood_glb import convert, WOOD_TONES

DEFAULT_TONE_CYCLE = ["oak", "cherry", "maple", "walnut"]

STL_REF = re.compile(r'filename="(?P<path>[^"]*?)\.stl"(?P<scale>\s+scale="[^"]*")?')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urdf")
    ap.add_argument("--out")
    ap.add_argument("--meshdir", default="wood_meshes")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--tones", default="", help="basename=tone,逗号分隔;余者按轮换")
    args = ap.parse_args()

    urdf_dir = os.path.dirname(os.path.abspath(args.urdf))
    text = open(args.urdf).read()
    out_urdf = args.out or os.path.join(urdf_dir, os.path.splitext(os.path.basename(args.urdf))[0] + "_textured.urdf")
    mesh_out_dir = os.path.join(urdf_dir, args.meshdir)
    os.makedirs(mesh_out_dir, exist_ok=True)

    tone_map = {}
    for pair in filter(None, args.tones.split(",")):
        k, _, v = pair.partition("=")
        tone_map[k.strip()] = v.strip()

    # 收集不同的 STL 引用(按出现顺序),分配木种
    seen = []
    for m in STL_REF.finditer(text):
        base = os.path.basename(m.group("path"))
        if base not in seen:
            seen.append(base)
    assigned = {}
    for i, base in enumerate(seen):
        tone = tone_map.get(base, DEFAULT_TONE_CYCLE[i % len(DEFAULT_TONE_CYCLE)])
        assigned[base] = tone if tone in WOOD_TONES else "oak"

    # 转每个 STL → GLB
    for m in STL_REF.finditer(text):
        path = m.group("path")  # 例 meshes/ring
        base = os.path.basename(path)
        stl_abs = os.path.join(urdf_dir, path + ".stl")
        glb_abs = os.path.join(mesh_out_dir, base + ".glb")
        if not os.path.exists(glb_abs):  # 同名只转一次
            if not os.path.exists(stl_abs):
                print(f"warn: 找不到 {stl_abs},跳过", file=sys.stderr); continue
            nv = convert(stl_abs, glb_abs, args.scale, assigned[base])
            print(f"  {base}.stl → {args.meshdir}/{base}.glb  ({nv} verts, {assigned[base]})")

    # 改写引用:filename 指向 GLB,并写入 scale="0.001 0.001 0.001"(毫米网格→米制关节)
    def repl(m):
        base = os.path.basename(m.group("path"))
        return f'filename="{args.meshdir}/{base}.glb" scale="0.001 0.001 0.001"'
    new_text = STL_REF.sub(repl, text)
    open(out_urdf, "w").write(new_text)
    print(f"\n纹理 URDF: {out_urdf}")
    print(f"网格目录: {mesh_out_dir}")
    print("验证: python verify_urdf.py " + out_urdf)

if __name__ == "__main__":
    main()
