#!/usr/bin/env python3
"""把二进制 STL 转成带「木纹 baseColorTexture + 平面投影 UV」的 GLB(纯标准库)。
用法: stl_to_wood_glb.py in.stl out.glb [scale]   scale 默认 0.001(mm→m)"""
import sys, struct, json, zlib, math

def parse_binary_stl(path, scale):
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[80:84])[0]
    off = 84
    pos, nrm = [], []
    for _ in range(n):
        nx, ny, nz = struct.unpack("<3f", b[off:off+12]); off += 12
        tri = []
        for _v in range(3):
            x, y, z = struct.unpack("<3f", b[off:off+12]); off += 12
            tri.append((x*scale, y*scale, z*scale))
        off += 2  # attribute byte count
        # 用面法线(平整着色,齿轮足够)
        # 若 STL 法线为 0 则现算
        if abs(nx)+abs(ny)+abs(nz) < 1e-9:
            ax, ay, az = (tri[1][0]-tri[0][0], tri[1][1]-tri[0][1], tri[1][2]-tri[0][2])
            bx, by, bz = (tri[2][0]-tri[0][0], tri[2][1]-tri[0][1], tri[2][2]-tri[0][2])
            nx, ny, nz = (ay*bz-az*by, az*bx-ax*bz, ax*by-ay*bx)
            l = math.hypot(nx, ny, nz) or 1.0
            nx, ny, nz = nx/l, ny/l, nz/l
        for v in tri:
            pos.append(v); nrm.append((nx, ny, nz))
    return pos, nrm

WOOD_TONES = {
    "oak":     ((216, 170, 112), (165, 116, 66)),   # 浅橡木
    "walnut":  ((150, 100, 60),  (96, 60, 34)),      # 深胡桃
    "cherry":  ((198, 120, 84),  (140, 74, 48)),     # 樱桃木(偏红)
    "maple":   ((226, 196, 146), (188, 150, 100)),   # 枫木(偏黄白)
}

def make_wood_png(tone="oak", w=256, h=256):
    """程序化木纹:暖棕底 + 沿 U 方向的年轮/纹理条带。"""
    def lerp(a, b, t): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
    light, dark = WOOD_TONES.get(tone, WOOD_TONES["oak"])
    px = bytearray()
    for y in range(h):
        px.append(0)  # PNG filter type
        for x in range(w):
            u = x / w
            # 多频年轮 + 轻微行向扰动,模拟木纹
            grain = (math.sin(u*math.pi*18 + math.sin(u*7.0)*1.5
                              + y*0.015) * 0.5 + 0.5)
            grain = grain ** 1.6
            streak = 0.12 * math.sin(y*0.5 + x*0.08)
            t = min(max(grain + streak, 0.0), 1.0)
            r, g, bb = lerp(light, dark, t)
            px += bytes((r, g, bb, 255))
    def chunk(typ, data):
        c = typ + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(px), 9)) + chunk(b"IEND", b"")

def planar_uv(pos, tile=2.5):
    xs = [p[0] for p in pos]; ys = [p[1] for p in pos]
    minx, maxx = min(xs), max(xs); miny, maxy = min(ys), max(ys)
    sx = (maxx-minx) or 1.0; sy = (maxy-miny) or 1.0
    return [((p[0]-minx)/sx*tile, (p[1]-miny)/sy*tile) for p in pos]

def pad4(b, fill=b"\x00"):
    return b + fill * ((4 - len(b) % 4) % 4)

def write_glb(out, pos, nrm, uv, tone='oak'):
    pos_b = b"".join(struct.pack("<3f", *t) for t in pos)
    nrm_b = b"".join(struct.pack("<3f", *t) for t in nrm)
    uv_b  = b"".join(struct.pack("<2f", *t) for t in uv)
    nverts = len(pos)
    # 非索引:每三个顶点一个三角形,索引 = 顺序
    if nverts <= 65535:
        idx_b = b"".join(struct.pack("<H", i) for i in range(nverts)); idx_ct = 5123
    else:
        idx_b = b"".join(struct.pack("<I", i) for i in range(nverts)); idx_ct = 5125
    png = make_wood_png(tone)
    segs = []; off = 0
    def add(d):
        nonlocal off
        d = pad4(d); o = off; off += len(d); segs.append(d); return o
    pos_o = add(pos_b); nrm_o = add(nrm_b); uv_o = add(uv_b); idx_o = add(idx_b); png_o = add(png)
    blob = b"".join(segs)
    mins = [min(p[i] for p in pos) for i in range(3)]
    maxs = [max(p[i] for p in pos) for i in range(3)]
    g = {
      "asset": {"version": "2.0", "generator": "stl_to_wood_glb"},
      "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0}],
      "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2}, "indices": 3, "material": 0}]}],
      "materials": [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0.0, "roughnessFactor": 0.75}, "name": "wood"}],
      "textures": [{"source": 0, "sampler": 0}],
      "images": [{"bufferView": 4, "mimeType": "image/png"}],
      "samplers": [{"magFilter": 9729, "minFilter": 9729, "wrapS": 10497, "wrapT": 10497}],
      "accessors": [
        {"bufferView": 0, "componentType": 5126, "count": nverts, "type": "VEC3", "min": mins, "max": maxs},
        {"bufferView": 1, "componentType": 5126, "count": nverts, "type": "VEC3"},
        {"bufferView": 2, "componentType": 5126, "count": nverts, "type": "VEC2"},
        {"bufferView": 3, "componentType": idx_ct, "count": nverts, "type": "SCALAR"},
      ],
      "bufferViews": [
        {"buffer": 0, "byteOffset": pos_o, "byteLength": len(pos_b), "target": 34962},
        {"buffer": 0, "byteOffset": nrm_o, "byteLength": len(nrm_b), "target": 34962},
        {"buffer": 0, "byteOffset": uv_o,  "byteLength": len(uv_b),  "target": 34962},
        {"buffer": 0, "byteOffset": idx_o, "byteLength": len(idx_b), "target": 34963},
        {"buffer": 0, "byteOffset": png_o, "byteLength": len(png)},
      ],
      "buffers": [{"byteLength": len(blob)}],
    }
    js = pad4(json.dumps(g, separators=(",", ":")).encode(), b" ")
    glb = b"glTF" + struct.pack("<II", 2, 12+8+len(js)+8+len(blob))
    glb += struct.pack("<I", len(js)) + b"JSON" + js
    glb += struct.pack("<I", len(blob)) + b"BIN\x00" + blob
    open(out, "wb").write(glb)
    return nverts

def zup_to_yup(seq):
    # CAD/URDF 是 Z-up,glTF 标准是 Y-up;viewer 的 GLB 管线会做 Y-up→Z-up({x,-z,y})。
    # 故这里把 Z-up 顶点预转成 Y-up:(x,y,z)→(x,z,-y),让 viewer 转回后正好复原 Z-up 朝向。
    return [(x, z, -y) for (x, y, z) in seq]

inp, outp = sys.argv[1], sys.argv[2]
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 0.001
tone = sys.argv[4] if len(sys.argv) > 4 else "oak"
pos, nrm = parse_binary_stl(inp, scale)
uv = planar_uv(pos)               # UV 用齿轮面 (x,y) 算,木纹落在齿轮正面
pos = zup_to_yup(pos)
nrm = zup_to_yup(nrm)
nv = write_glb(outp, pos, nrm, uv, tone)
print(f"{outp}: {nv} verts, tone={tone}, Y-up")
