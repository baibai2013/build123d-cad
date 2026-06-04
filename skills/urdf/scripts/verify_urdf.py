#!/usr/bin/env python3
"""Headless 验证任意 URDF(生成的 / 纯 primitive 无网格文件 / STL / GLB / 纹理,皆可):
起 viewer → 截静态图 + 驱动关节图(小尺寸省 AI token)→ 抓控制台报错 → 打印核对清单。
配合 references/urdf-workflow.md「Render-Verify + Fix Loop」用——任何 URDF 落地后都应跑一遍。

用法(需用装了 playwright+chromium 的解释器,如 build123d-parts-lib 的 .venv):
    <venv>/bin/python verify_urdf.py <urdf> [--joint NAME] [--deg 60]
                                    [--outdir DIR] [--width 640] [--height 460]

要点:勿弹可见标签页(headless);截图视口默认 640×460(~390 token/张,1100×760≈1100)。
"""
import sys, os, re, subprocess, argparse

def start_viewer(urdf):
    start_sh = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             "..", "..", "viewer", "scripts", "start.sh"))
    r = subprocess.run(["bash", start_sh, os.path.abspath(urdf)],
                       capture_output=True, text=True, timeout=120)
    url = (r.stdout or "").strip().splitlines()
    url = next((l for l in url if l.startswith("http")), "")
    if not url:
        sys.exit(f"start.sh 没返回 URL。stderr:\n{r.stderr[-500:]}")
    return url

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urdf")
    ap.add_argument("--joint", default="", help="要驱动的关节名;留空=自动取第一个")
    ap.add_argument("--deg", default="60")
    ap.add_argument("--outdir", default="")
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=460)
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("缺 playwright。用装了 playwright + `playwright install chromium` 的解释器跑"
                 "(如 ~/work/build123d-parts-lib/.venv/bin/python)。")

    outdir = args.outdir or os.path.join(os.path.dirname(os.path.abspath(args.urdf)), "_verify")
    os.makedirs(outdir, exist_ok=True)
    url = start_viewer(args.urdf)
    print("URL:", url)

    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--ignore-gpu-blocklist"])
        pg = b.new_page(viewport={"width": args.width, "height": args.height})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.goto(url, wait_until="load", timeout=30000)
        pg.wait_for_timeout(6000)
        static_png = os.path.join(outdir, "static.png")
        pg.screenshot(path=static_png)

        # 关节输入框:aria-label="<joint> value in deg"
        sel = (f'input[aria-label="{args.joint} value in deg"]' if args.joint
               else 'input[aria-label$="value in deg"]')
        inp = pg.query_selector(sel)
        driven_png = ""
        if inp:
            inp.click(); inp.fill(str(args.deg)); pg.keyboard.press("Enter")
            pg.wait_for_timeout(3000)
            driven_png = os.path.join(outdir, "driven.png")
            pg.screenshot(path=driven_png)
        real_errs = [e for e in errs if not any(k in e for k in ("github", "message port", "lastError"))]
        b.close()

    print("静态截图:", static_png)
    if driven_png:
        print(f"驱动截图(关节={args.joint or '第一个'}={args.deg}°):", driven_png)
    else:
        print("未找到可动关节输入框(无关节或选择器不匹配)")
    if real_errs:
        print("控制台报错(⚠ 渲染失败的首要线索):", real_errs[:5])
    else:
        print("控制台无报错")
    print("\n核对清单(任何 URDF):① 无报错且模型渲出来(没 'Failed to load render mesh')"
          " ② 每个 link 都在、形状对 ③ 朝向对(轴/平面符合预期) ④ 居中、相对位置/原点对"
          " ⑤ 关节面板列出可动关节,驱动后对应 link 绕正确轴运动(mimic 联动对)"
          "  —— 若有纹理另查:贴图显示(非灰模)+ 随关节跟随。")

if __name__ == "__main__":
    main()
