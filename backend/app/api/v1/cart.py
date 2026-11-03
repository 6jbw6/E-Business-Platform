"""购物车接口。"""

from decimal import Decimal

from fastapi import APIRouter, status

from backend.app.core.deps import CurrentUser, DbSession
from backend.app.crud import cart as crud
from backend.app.models.cart import CartItem
from backend.app.models.product import STATUS_ON_SALE
from backend.app.schemas.cart import CartAddRequest, CartItemOut, CartOut, CartUpdateRequest
from backend.app.schemas.common import ApiResponse

router = APIRouter(prefix="/cart", tags=["购物车"])


def _item_out(item: CartItem) -> CartItemOut:
    product = item.product
    return CartItemOut(
        id=item.id,
        product_id=product.id,
        product_name=product.name,
        product_image=product.main_image,
        price=product.price,
        quantity=item.quantity,
        checked=item.checked,
        subtotal=product.price * item.quantity,
        stock=product.stock,
        on_sale=product.status == STATUS_ON_SALE,
    )


def _cart_out(items: list[CartItem]) -> CartOut:
    total_quantity, total_amount, checked_count = crud.totals(items)
    return CartOut(
        items=[_item_out(i) for i in items],
        total_quantity=total_quantity,
        total_amount=total_amount,
        checked_count=checked_count,
    )


@router.get("", response_model=ApiResponse[CartOut], summary="查看购物车")
def read_cart(db: DbSession, user: CurrentUser):
    return ApiResponse(data=_cart_out(crud.list_items(db, user.id)))


@router.post(
    "",
    response_model=ApiResponse[CartOut],
    status_code=status.HTTP_201_CREATED,
    summary="加入购物车（重复加购则累加数量）",
)
def add_to_cart(payload: CartAddRequest, db: DbSession, user: CurrentUser):
    crud.add(db, user.id, payload.product_id, payload.quantity)
    return ApiResponse(data=_cart_out(crud.list_items(db, user.id)), message="已加入购物车")


@router.put("/{item_id}", response_model=ApiResponse[CartOut], summary="修改数量或勾选状态")
def update_cart_item(item_id: int, payload: CartUpdateRequest, db: DbSession, user: CurrentUser):
    crud.update_item(db, user.id, item_id, payload.quantity, payload.checked)
    return ApiResponse(data=_cart_out(crud.list_items(db, user.id)), message="购物车已更新")


@router.delete("/{item_id}", response_model=ApiResponse[CartOut], summary="移除一件商品")
def remove_cart_item(item_id: int, db: DbSession, user: CurrentUser):
    crud.remove(db, user.id, item_id)
    return ApiResponse(data=_cart_out(crud.list_items(db, user.id)), message="已移出购物车")


@router.delete("", response_model=ApiResponse[CartOut], summary="清空购物车")
def clear_cart(db: DbSession, user: CurrentUser):
    crud.clear(db, user.id)
    return ApiResponse(
        data=CartOut(items=[], total_quantity=0, total_amount=Decimal("0.00"), checked_count=0),
        message="购物车已清空",
    )
