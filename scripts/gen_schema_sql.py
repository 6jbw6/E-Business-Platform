"""由 ORM 模型反向生成 sql/01_schema.sql，保证文档里的建表语句和代码不脱节。

用法（在项目根目录）：
    python -m scripts.gen_schema_sql
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._bootstrap import setup_console

ROOT = setup_console()

from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateIndex, CreateTable

import backend.app.models  # noqa: F401  触发全部模型注册
from backend.app.core.config import settings
from backend.app.db.base import Base

HEADER = """-- ---------------------------------------------------------------------------
-- B2C 商城 · 数据库建表脚本
-- 生成方式：python -m scripts.gen_schema_sql（由 ORM 模型反向生成，勿手工改动）
-- 目标库：MySQL 8.0 / InnoDB / utf8mb4
-- 执行：mysql -u root -p < sql/01_schema.sql
-- ---------------------------------------------------------------------------

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS `{database}`
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

USE `{database}`;

"""


def render() -> str:
    dialect = mysql.dialect()
    parts = [HEADER.format(database=settings.mysql_database)]
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=dialect)).strip()
        parts.append(f"{ddl};\n")
        # 索引不属于 CREATE TABLE 的输出，单独补一段，脚本才能建出完整库
        for index in sorted(table.indexes, key=lambda i: i.name or ""):
            parts.append(f"{str(CreateIndex(index).compile(dialect=dialect)).strip()};\n")
    parts.append("SET FOREIGN_KEY_CHECKS = 1;\n")
    return "\n".join(parts)


def main() -> int:
    target = ROOT / "sql" / "01_schema.sql"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(), encoding="utf-8", newline="\n")
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    print(f"已生成 {target}\n包含表：{tables}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
