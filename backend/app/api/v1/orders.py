"""订单接口：下单、查询与状态流转。"""

from fastapi import APIRouter, Query, status

from backend.app.core.deps import CurrentAdmin, CurrentUser, DbSession
from backend.app.core.exceptions import forbidden
from backend.app.crud import order as crud
from backend.app.models.order import Order
from backend.app.models.user import ROLE_ADMIN
from backend.app.schemas.common import ApiResponse, PageData, make_page
from backend.app.schemas.order import (
    OrderCreateRequest,
    OrderDetailOut,
    OrderOut,
)

router = APIRouter(prefix="/orders", tags=["订单"])


def _to_out(order: Order) -> OrderOut:
    data = OrderOut.model_validate(order)
    return data.model_copy(
        update={
            "status_label": crud.status_label(order.status),
            "item_count": len(order.items),
            "total_quantity": sum(i.quantity for i in order.items),
        }
    )


def _to_detail(order: Order) -> OrderDetailOut:
    data = OrderDetailOut.model_validate(order)
    return data.model_copy(
        update={
            "status_label": crud.status_label(order.status),
            "item_count": len(order.items),
            "total_quantity": sum(i.quantity for i in order.items),
        }
    )


@router.post(
    "",
    response_model=ApiResponse[OrderDetailOut],
    status_code=status.HTTP_201_CREATED,
    summary="提交订单",
)
def create_order(payload: OrderCreateRequest, db: DbSession, user: CurrentUser):
    items = None
    if payload.items is not None:
        items = [(i.product_id, i.quantity) for i in payload.items]
    order = crud.create_order(
        db,
        user,
        receiver_name=payload.receiver_name,
        receiver_phone=payload.receiver_phone,
        receiver_address=payload.receiver_address,
        remark=payload.remark,
        items=items,
    )
    return ApiResponse(data=_to_detail(order), message="下单成功，请在有效期内付款")


@router.get("", response_model=ApiResponse[PageData[OrderOut]], summary="我的订单列表")
def read_orders(
    db: DbSession,
    user: CurrentUser,
    status_: int | None = Query(default=None, alias="status", ge=0, le=4, description="按状态筛选"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    all_users: bool = Query(
        default=False, alias="all", description="管理员传 true 查看全站订单，用于发货台"
    ),
):
    if all_users and user.role != ROLE_ADMIN:
        raise forbidden("查看全站订单仅管理员可用")
    scope = None if all_users else user.id
    orders, total = crud.list_orders(db, scope, status=status_, page=page, page_size=page_size)
    return ApiResponse(data=make_page([_to_out(o) for o in orders], total, page, page_size))


@router.get("/{order_id}", response_model=ApiResponse[OrderDetailOut], summary="订单详情")
def read_order(order_id: int, db: DbSession, user: CurrentUser):
    return ApiResponse(data=_to_detail(crud.get_order(db, user, order_id)))


@router.put("/{order_id}/payment", response_model=ApiResponse[OrderDetailOut], summary="支付订单（模拟）")
def pay_order(order_id: int, db: DbSession, user: CurrentUser):
    order = crud.get_order(db, user, order_id)
    return ApiResponse(data=_to_detail(crud.pay(db, order)), message="支付成功")


@router.put("/{order_id}/shipment", response_model=ApiResponse[OrderDetailOut], summary="发货（管理员）")
def ship_order(order_id: int, db: DbSession, admin: CurrentAdmin):
    order = crud.get_order(db, admin, order_id)
    return ApiResponse(data=_to_detail(crud.ship(db, order)), message="已发货")


@router.put("/{order_id}/receipt", response_model=ApiResponse[OrderDetailOut], summary="确认收货")
def receive_order(order_id: int, db: DbSession, user: CurrentUser):
    order = crud.get_order(db, user, order_id)
    return ApiResponse(data=_to_detail(crud.receive(db, order)), message="交易完成")


@router.put("/{order_id}/cancellation", response_model=ApiResponse[OrderDetailOut], summary="取消订单（回滚库存）")
def cancel_order(order_id: int, db: DbSession, user: CurrentUser):
    order = crud.get_order(db, user, order_id)
    return ApiResponse(data=_to_detail(crud.cancel(db, order)), message="订单已取消")
