"""web_preview — 飞书/CI/Python 调用入口。

```
from web_preview import start
url = start("/abs/path/to/foo.step")  # → "http://127.0.0.1:4178/?engine=cad&dir=...&file=foo.step"
```

CLI:

```
python web_preview.py /abs/path/to/foo.step
```

设计:
- 仅包装 start.sh,不重复实现路由/端口/复用逻辑(避免双轨)。
- 失败抛 RuntimeError(带退出码),让上层飞书机器人/CI 自行决定是否降级到 snapshot()。
- snapshot() 是 P1 任务(headless 降级链),见 references/headless-fallback.md。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
START_SH = SCRIPT_DIR / "start.sh"


def start(file_path: str | os.PathLike, workspace: str | os.PathLike | None = None) -> str:
    """起 viewer server,返回可点开的 URL(stdout 唯一一行)。

    参数:
      file_path: 要预览的文件绝对路径
      workspace: workspace_root,缺省由 start.sh 推断(git 顶层 / 文件目录)

    异常:
      FileNotFoundError: 文件不存在(start.sh exit 3)
      ValueError: 后缀不支持(start.sh exit 2)
      RuntimeError: 端口分配失败(start.sh exit 4)或其它
    """
    file_path = str(Path(file_path).resolve())
    cmd = ["bash", str(START_SH), file_path]
    if workspace:
        cmd.append(str(Path(workspace).resolve()))

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if proc.returncode == 0:
        return proc.stdout.strip()

    err = (proc.stderr or "").strip()
    if proc.returncode == 3:
        raise FileNotFoundError(err or file_path)
    if proc.returncode == 2:
        raise ValueError(err or "unsupported extension or bad args")
    if proc.returncode == 4:
        raise RuntimeError(f"port allocation failed: {err}")
    raise RuntimeError(f"start.sh exit {proc.returncode}: {err}")


def snapshot(file_path, workspace=None, mode: str = "auto"):
    """P1: headless 降级链(playwright → OCP → VTK)。

    P0 阶段未实现,占位抛出 NotImplementedError。
    详见 references/headless-fallback.md(待 P1 落盘)。
    """
    raise NotImplementedError(
        "snapshot() 是 P1-5 任务,目前未实现。本周先跑通 P0-3(start)。"
    )


def _cli():
    if len(sys.argv) < 2:
        print("usage: python web_preview.py <file_path> [workspace_root]", file=sys.stderr)
        sys.exit(2)
    f = sys.argv[1]
    ws = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        url = start(f, ws)
        print(url)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    _cli()
