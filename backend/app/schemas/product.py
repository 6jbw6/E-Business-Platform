"""商品相关的请求/响应模型。"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreateRequest(BaseModel):
    category_id: int = Field(description="所属类别ID，必须是已存在的二级或一级分类")
    name: str = Field(min_length=1, max_length=120, description="商品名称")
    subtitle: str = Field(default="", max_length=200, description="副标题/卖点")
    main_image: str = Field(default="", max_length=255, description="主图地址")
    price: Decimal = Field(ge=Decimal("0.01"), le=Decimal("99999999.99"), description="售价（元）")
    original_price: Decimal = Field(
        default=Decimal("0.00"), ge=Decimal("0"), le=Decimal("99999999.99"), description="划线价（元）"
    )
    stock: int = Field(default=0, ge=0, description="初始库存")
    unit: str = Field(default="件", max_length=16, description="计量单位")
    detail: str = Field(default="", description="图文详情")
    status: int = Field(default=1, ge=0, le=1, description="状态：1=在售，0=下架")


class ProductUpdateRequest(BaseModel):
    category_id: int | None = Field(default=None)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    subtitle: str | None = Field(default=None, max_length=200)
    main_image: str | None = Field(default=None, max_length=255)
    price: Decimal | None = Field(default=None, ge=Decimal("0.01"))
    original_price: Decimal | None = Field(default=None, ge=Decimal("0"))
    stock: int | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=16)
    detail: str | None = Field(default=None)
    status: int | None = Field(default=None, ge=0, le=1)


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="商品ID")
    category_id: int = Field(description="所属类别ID")
    name: str = Field(description="商品名称")
    subtitle: str = Field(default="", description="副标题")
    main_image: str = Field(default="", description="主图地址")
    price: Decimal = Field(description="售价（元）")
    original_price: Decimal = Field(default=Decimal("0.00"), description="划线价（元）")
    stock: int = Field(description="可售库存")
    sales: int = Field(description="累计销量")
    unit: str = Field(description="计量单位")
    status: int = Field(description="状态：1=在售，0=下架")
    category_name: str | None = Field(default=None, description="所属类别名称")


class ProductDetailOut(ProductOut):
    detail: str | None = Field(default="", description="图文详情")


class ProductImageOut(BaseModel):
    url: str = Field(description="主图相对地址，可直接填进商品表单的 main_image")
