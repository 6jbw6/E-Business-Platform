"""命令行脚本公共初始化：补 sys.path，并把控制台输出切成 UTF-8。

Windows 控制台默认 GBK，直接 print 中文路径或中文提示会抛 UnicodeEncodeError。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def setup_console() -> Path:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    return ROOT
