"""命令行初始化数据库：建库 -> 建表 -> 播种演示数据。

用法（在项目根目录）：
    python -m scripts.init_db
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._bootstrap import setup_console

setup_console()

from backend.app.core.config import settings
from backend.app.db.init_db import SEED_USERS, init_db


def main() -> int:
    print(f"目标数据库：{settings.mysql_user}@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}")
    counts = init_db()
    print(
        "初始化完成："
        f"新增用户 {counts.get('users', 0)} 个，"
        f"新增分类 {counts.get('categories', 0)} 个，"
        f"新增商品 {counts.get('products', 0)} 个。"
    )
    for _, username, password, nickname, _, _, role in SEED_USERS:
        print(f"演示账号：{username} / {password}（{nickname}，角色 {role}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
