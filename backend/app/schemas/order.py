"""订单相关的请求/响应模型。"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrderItemInput(BaseModel):
    product_id: int = Field(description="商品ID")
    quantity: int = Field(ge=1, le=999, description="购买数量")


class OrderCreateRequest(BaseModel):
    receiver_name: str = Field(min_length=2, max_length=32, description="收货人姓名")
    receiver_phone: str = Field(min_length=6, max_length=20, description="收货电话")
    receiver_address: str = Field(min_length=5, max_length=255, description="收货地址")
    remark: str = Field(default="", max_length=255, description="买家备注")
    items: list[OrderItemInput] | None = Field(
        default=None,
        description="直接购买的商品列表；不传则结算购物车中已勾选的商品",
    )


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="明细ID")
    product_id: int = Field(description="商品ID")
    product_name: str = Field(description="下单时的商品名称快照")
    product_image: str = Field(default="", description="下单时的主图快照")
    price: Decimal = Field(description="成交单价快照（元）")
    quantity: int = Field(description="数量")
    subtotal: Decimal = Field(description="小计（元）")


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="订单ID")
    order_no: str = Field(description="订单号")
    status: int = Field(description="状态：0待付款 1待发货 2待收货 3已完成 4已取消")
    status_label: str = Field(default="", description="状态中文名称，由接口层填充")
    total_amount: Decimal = Field(description="商品总额（元）")
    freight: Decimal = Field(description="运费（元）")
    pay_amount: Decimal = Field(description="实付金额（元）")
    receiver_name: str = Field(description="收货人")
    receiver_phone: str = Field(description="收货电话")
    receiver_address: str = Field(description="收货地址")
    remark: str = Field(default="", description="买家备注")
    item_count: int = Field(default=0, description="商品种数")
    total_quantity: int = Field(default=0, description="商品总件数")
    created_at: datetime | None = Field(default=None, description="下单时间")
    paid_at: datetime | None = Field(default=None, description="支付时间")


class OrderDetailOut(OrderOut):
    items: list[OrderItemOut] = Field(default_factory=list, description="订单明细")
    shipped_at: datetime | None = Field(default=None, description="发货时间")
    finished_at: datetime | None = Field(default=None, description="完成时间")
    cancelled_at: datetime | None = Field(default=None, description="取消时间")
