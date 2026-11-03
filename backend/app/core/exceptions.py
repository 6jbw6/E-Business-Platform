"""业务错误码与全局异常处理。"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

# 统一响应体里的业务码：0 表示成功，其余按模块分段
CODE_OK = 0
CODE_BAD_REQUEST = 40000
CODE_UNAUTHORIZED = 40100
CODE_FORBIDDEN = 40300
CODE_NOT_FOUND = 40400
CODE_CONFLICT = 40900
CODE_SERVER_ERROR = 50000


class BizError(Exception):
    """可预期的业务异常，会被翻译成一个标准响应体。"""

    def __init__(
        self,
        message: str,
        *,
        code: int = CODE_BAD_REQUEST,
        http_status: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status


def not_found(message: str = "资源不存在") -> BizError:
    return BizError(message, code=CODE_NOT_FOUND, http_status=status.HTTP_404_NOT_FOUND)


def conflict(message: str) -> BizError:
    return BizError(message, code=CODE_CONFLICT, http_status=status.HTTP_409_CONFLICT)


def unauthorized(message: str = "登录状态已失效，请重新登录") -> BizError:
    return BizError(message, code=CODE_UNAUTHORIZED, http_status=status.HTTP_401_UNAUTHORIZED)


def forbidden(message: str = "没有权限执行该操作") -> BizError:
    return BizError(message, code=CODE_FORBIDDEN, http_status=status.HTTP_403_FORBIDDEN)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BizError)
    async def _biz_error(_: Request, exc: BizError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content={"code": exc.code, "message": exc.message, "data": None},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(p) for p in first.get("loc", ())[1:]) or "请求参数"
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "code": CODE_BAD_REQUEST,
                "message": f"{field} 校验失败：{first.get('msg', '参数不合法')}",
                "data": None,
            },
        )

    @app.exception_handler(IntegrityError)
    async def _integrity_error(_: Request, exc: IntegrityError) -> JSONResponse:
        # 唯一索引兜底：并发写入同名/重复记录时给出可读提示而不是 500
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "code": CODE_CONFLICT,
                "message": "数据已存在或被其他请求占用，请刷新后重试",
                "data": None,
            },
        )
