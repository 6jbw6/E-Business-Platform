"""通用响应包装与分页结构。"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """所有接口统一返回这个结构：code=0 表示成功。"""

    code: int = Field(default=0, description="业务码，0=成功，非 0 见接口文档错误码表")
    message: str = Field(default="success", description="提示信息")
    data: T | None = Field(default=None, description="业务数据")


class PageData(BaseModel, Generic[T]):
    """列表接口的分页载荷。"""

    items: list[T] = Field(default_factory=list, description="当前页数据")
    total: int = Field(default=0, description="总条数")
    page: int = Field(default=1, description="当前页码，从 1 开始")
    page_size: int = Field(default=10, description="每页条数")
    pages: int = Field(default=0, description="总页数")


def ok(data: T | None = None, message: str = "success") -> "ApiResponse[T]":
    return ApiResponse(data=data, message=message)


def make_page(items: list, total: int, page: int, page_size: int) -> PageData:
    pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return PageData(items=items, total=total, page=page, page_size=page_size, pages=pages)


class HealthOut(BaseModel):
    status: str = Field(description="服务状态，正常时为 up")
    database: str = Field(description="数据库连通性")
    version: str = Field(description="服务版本号")
