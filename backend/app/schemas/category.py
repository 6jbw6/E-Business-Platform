"""商品类别相关的请求/响应模型。"""

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50, description="类别名称")
    parent_id: int | None = Field(default=None, description="父类别ID，不传即一级分类")
    icon: str = Field(default="", max_length=255, description="类别图标")
    sort_order: int = Field(default=0, ge=0, description="同级排序，越小越靠前")
    status: int = Field(default=1, ge=0, le=1, description="状态：1=显示，0=隐藏")


class CategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    icon: str | None = Field(default=None, max_length=255)
    sort_order: int | None = Field(default=None, ge=0)
    status: int | None = Field(default=None, ge=0, le=1)


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="类别ID")
    name: str = Field(description="类别名称")
    parent_id: int | None = Field(default=None, description="父类别ID")
    level: int = Field(description="层级：1=一级，2=二级")
    icon: str = Field(default="", description="类别图标")
    sort_order: int = Field(description="同级排序")
    status: int = Field(description="状态：1=显示，0=隐藏")


class CategoryTreeOut(CategoryOut):
    children: list[CategoryOut] = Field(default_factory=list, description="子分类列表")
