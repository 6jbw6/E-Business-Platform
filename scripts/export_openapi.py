"""导出 OpenAPI 规范到 docs/openapi.json，供接口文档与离线查看使用。

用法（在项目根目录）：
    python -m scripts.export_openapi
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._bootstrap import setup_console

ROOT = setup_console()

from backend.app.main import app


def main() -> int:
    schema = app.openapi()
    target = ROOT / "docs" / "openapi.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths = len(schema.get("paths", {}))
    print(f"已导出 {target} （{paths} 个路径）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
