"""购物车相关的请求/响应模型。"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CartAddRequest(BaseModel):
    product_id: int = Field(description="商品ID")
    quantity: int = Field(default=1, ge=1, le=999, description="加购数量")


class CartUpdateRequest(BaseModel):
    quantity: int | None = Field(default=None, ge=1, le=999, description="修改后的数量")
    checked: int | None = Field(default=None, ge=0, le=1, description="是否勾选结算：1=勾选，0=取消勾选")


class CartItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="购物车行ID")
    product_id: int = Field(description="商品ID")
    product_name: str = Field(description="商品名称")
    product_image: str = Field(default="", description="商品主图")
    price: Decimal = Field(description="当前售价（元）")
    quantity: int = Field(description="数量")
    checked: int = Field(description="是否勾选结算：1=勾选，0=未勾选")
    subtotal: Decimal = Field(description="该行小计=售价×数量")
    stock: int = Field(description="商品当前库存")
    on_sale: bool = Field(description="商品是否仍在售")


class CartOut(BaseModel):
    items: list[CartItemOut] = Field(default_factory=list, description="购物车明细")
    total_quantity: int = Field(description="勾选商品总件数")
    total_amount: Decimal = Field(description="勾选商品总金额（元）")
    checked_count: int = Field(description="勾选种数")
