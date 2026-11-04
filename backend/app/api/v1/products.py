"""商品接口。"""

from decimal import Decimal

from fastapi import APIRouter, File, Query, UploadFile, status

from backend.app.core.deps import CurrentAdmin, DbSession
from backend.app.core.storage import GOODS_SUBDIR, save_image
from backend.app.crud import product as crud
from backend.app.models.product import STATUS_ON_SALE
from backend.app.schemas.common import ApiResponse, PageData, make_page
from backend.app.schemas.product import (
    ProductCreateRequest,
    ProductDetailOut,
    ProductImageOut,
    ProductOut,
    ProductUpdateRequest,
)

router = APIRouter(prefix="/products", tags=["商品"])


def _brief(product, category_name: str) -> ProductOut:
    data = ProductOut.model_validate(product)
    return data.model_copy(update={"category_name": category_name})


@router.get("", response_model=ApiResponse[PageData[ProductOut]], summary="商品列表（分页/搜索/筛选/排序）")
def read_products(
    db: DbSession,
    keyword: str | None = Query(default=None, max_length=50, description="按商品名/副标题模糊搜索"),
    category_id: int | None = Query(default=None, description="分类ID，传一级分类会级联其子分类"),
    min_price: Decimal | None = Query(default=None, ge=0, description="价格下限"),
    max_price: Decimal | None = Query(default=None, ge=0, description="价格上限"),
    sort: str = Query(default="default", description="排序：default/price_asc/price_desc/sales_desc/newest"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    show_all: bool = Query(default=False, description="管理员可传 true 查看已下架商品"),
):
    rows, total = crud.paginate(
        db,
        keyword=keyword,
        category_id=category_id,
        status=None if show_all else STATUS_ON_SALE,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    items = [_brief(p, name) for p, name in rows]
    return ApiResponse(data=make_page(items, total, page, page_size))


@router.post(
    "/image",
    response_model=ApiResponse[ProductImageOut],
    summary="上传商品主图（管理员）",
)
async def upload_product_image(
    _: CurrentAdmin,
    file: UploadFile = File(..., description="图片文件，multipart/form-data 的 file 字段"),
):
    data = await file.read()
    url = save_image(GOODS_SUBDIR, "goods", data)
    return ApiResponse(data=ProductImageOut(url=url), message="主图已上传")


@router.get("/{product_id}", response_model=ApiResponse[ProductDetailOut], summary="商品详情")
def read_product(product_id: int, db: DbSession):
    product, category_name = crud.get_detail(db, product_id)
    data = ProductDetailOut.model_validate(product).model_copy(update={"category_name": category_name})
    return ApiResponse(data=data)


@router.post(
    "",
    response_model=ApiResponse[ProductOut],
    status_code=status.HTTP_201_CREATED,
    summary="发布商品（管理员）",
)
def create_product(payload: ProductCreateRequest, db: DbSession, _: CurrentAdmin):
    product = crud.create(db, **payload.model_dump())
    return ApiResponse(data=_brief(product, product.category.name), message="商品已上架")


@router.put("/{product_id}", response_model=ApiResponse[ProductOut], summary="修改商品（管理员）")
def update_product(product_id: int, payload: ProductUpdateRequest, db: DbSession, _: CurrentAdmin):
    product = crud.update(db, product_id, **payload.model_dump(exclude_none=True))
    return ApiResponse(data=_brief(product, product.category.name), message="商品已更新")


@router.delete("/{product_id}", response_model=ApiResponse[None], summary="下架商品（管理员）")
def delete_product(product_id: int, db: DbSession, _: CurrentAdmin):
    crud.delete(db, product_id)
    return ApiResponse(message="商品已下架")
