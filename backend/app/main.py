"""FastAPI 应用入口。

本地启动：uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.api.router import api_router
from backend.app.core.config import PROJECT_ROOT, settings
from backend.app.core.exceptions import register_exception_handlers
from backend.app.core.storage import upload_root
from backend.app.db.session import engine
from backend.app.schemas.common import ApiResponse, HealthOut

TAGS_METADATA = [
    {"name": "用户与登录", "description": "注册、登录换取 JWT、查看和修改个人资料。"},
    {"name": "商品类别", "description": "两级分类的查询与维护（写操作需管理员）。"},
    {"name": "商品", "description": "商品列表分页搜索、详情，以及上架/改价/下架。"},
    {"name": "购物车", "description": "加购、改数量、勾选、移除与清空。"},
    {"name": "订单", "description": "下单扣库存、订单查询与状态流转（付款/发货/收货/取消）。"},
]

DESCRIPTION = """
B2C 商城后端接口。所有业务接口统一挂在 `/api/v1` 下，返回结构固定为
`{"code": 0, "message": "success", "data": ...}`，`code` 非 0 即为业务错误。

**鉴权方式**：先调用 `/api/v1/auth/login` 拿到 `access_token`，
后续请求头带上 `Authorization: Bearer <token>`（点右上角 Authorize 按钮可直接粘贴）。
"""


class SPAStaticFiles(StaticFiles):
    """托管 Vue 构建产物：history 路由刷新时路径没有对应文件，就回 index.html 交给前端路由。

    以后端前缀开头的路径不做这个兜底，仍然返回 404，免得接口地址写错时拿到一个 HTML。
    """

    async def get_response(self, path: str, scope):
        is_api_path = scope["path"].startswith(settings.api_prefix)
        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if is_api_path or exc.status_code != 404:
                raise
            return await super().get_response("index.html", scope)

        if response.status_code == 404 and not is_api_path:
            return await super().get_response("index.html", scope)
        return response


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_init_db:
        from backend.app.db.init_db import init_db

        init_db()
    yield
    engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=DESCRIPTION,
        openapi_tags=TAGS_METADATA,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=settings.cors_origins.strip() != "*",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)

    # 头像等上传文件走静态目录，不经过业务代码，避免任意路径读取
    uploads = upload_root()
    uploads.mkdir(parents=True, exist_ok=True)
    app.mount(
        settings.upload_url_prefix,
        StaticFiles(directory=str(uploads)),
        name="uploads",
    )

    @app.get("/health", response_model=ApiResponse[HealthOut], tags=["服务状态"], summary="健康检查")
    async def health() -> ApiResponse[HealthOut]:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            database = "up"
        except Exception as exc:  # 连不上库也要给出明确原因，方便部署排障
            database = f"down: {type(exc).__name__}"
        return ApiResponse(
            data=HealthOut(status="up", database=database, version=settings.app_version)
        )

    # 前端构建产物存在就由同一个 uvicorn 托管，挂载必须排在所有后端路由之后
    dist_dir = PROJECT_ROOT / settings.frontend_dist
    if (dist_dir / "index.html").is_file():
        app.mount("/", SPAStaticFiles(directory=str(dist_dir), html=True), name="spa")
    else:

        @app.get("/", include_in_schema=False)
        async def index() -> dict[str, str]:
            return {
                "service": settings.app_name,
                "version": settings.app_version,
                "docs": "/docs",
                "api_prefix": settings.api_prefix,
                "frontend": f"未找到 {settings.frontend_dist}/index.html，页面请用 npm run dev 或 npm run build",
            }

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        return response

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
        )
        schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerToken"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "登录接口返回的 access_token",
        }
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi
    return app


app = create_app()
