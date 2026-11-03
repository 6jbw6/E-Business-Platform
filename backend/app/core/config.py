from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """全部配置项都可以用根目录 .env 或同名环境变量覆盖。"""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "B2C 商城后端服务"
    app_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    debug: bool = False

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "ebusiness_mall"
    # 设置后直接用它，忽略上面的分字段配置（便于 Docker/服务器一行切换）
    database_url: str | None = None

    jwt_secret: str = "please-change-this-secret-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120

    cors_origins: str = "*"

    # 首次启动时自动建表并播种演示数据；生产部署建议关掉，改用 sql/*.sql
    auto_init_db: bool = False

    @property
    def sqlalchemy_uri(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"mysql+pymysql://{quote_plus(self.mysql_user)}:{quote_plus(self.mysql_password)}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset=utf8mb4"
        )

    @property
    def server_uri(self) -> str:
        """不带库名的连接串，用于首次建库。"""
        return (
            f"mysql+pymysql://{quote_plus(self.mysql_user)}:{quote_plus(self.mysql_password)}"
            f"@{self.mysql_host}:{self.mysql_port}/?charset=utf8mb4"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
