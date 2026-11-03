"""商品类别接口。"""

from fastapi import APIRouter, Query, status

from backend.app.core.deps import CurrentAdmin, DbSession
from backend.app.crud import category as crud
from backend.app.models.category import Category
from backend.app.schemas.category import (
    CategoryCreateRequest,
    CategoryOut,
    CategoryTreeOut,
    CategoryUpdateRequest,
)
from backend.app.schemas.common import ApiResponse

router = APIRouter(prefix="/categories", tags=["商品类别"])


def _to_tree(categories: list[Category]) -> list[CategoryTreeOut]:
    grouped = crud.group_by_parent(categories)
    children_map = {
        parent_id: [CategoryOut.model_validate(c) for c in children]
        for parent_id, children in grouped.items()
    }
    roots = []
    for c in grouped.get(None, []):
        roots.append(
            CategoryTreeOut(
                **CategoryOut.model_validate(c).model_dump(),
                children=children_map.get(c.id, []),
            )
        )
    return roots


@router.get("/tree", response_model=ApiResponse[list[CategoryTreeOut]], summary="分类树（一级带二级）")
def read_tree(db: DbSession, include_hidden: bool = Query(default=False, description="是否包含隐藏分类，仅管理员用")):
    return ApiResponse(data=_to_tree(crud.list_all(db, include_hidden=include_hidden)))


@router.get("", response_model=ApiResponse[list[CategoryOut]], summary="分类平铺列表")
def read_list(db: DbSession, include_hidden: bool = Query(default=False)):
    return ApiResponse(data=[CategoryOut.model_validate(c) for c in crud.list_all(db, include_hidden=include_hidden)])


@router.get("/{category_id}", response_model=ApiResponse[CategoryOut], summary="分类详情")
def read_one(category_id: int, db: DbSession):
    return ApiResponse(data=CategoryOut.model_validate(crud.get_or_404(db, category_id)))


@router.post(
    "",
    response_model=ApiResponse[CategoryOut],
    status_code=status.HTTP_201_CREATED,
    summary="新建分类（管理员）",
)
def create_category(payload: CategoryCreateRequest, db: DbSession, _: CurrentAdmin):
    category = crud.create(db, **payload.model_dump())
    return ApiResponse(data=CategoryOut.model_validate(category), message="分类已创建")


@router.put("/{category_id}", response_model=ApiResponse[CategoryOut], summary="修改分类（管理员）")
def update_category(category_id: int, payload: CategoryUpdateRequest, db: DbSession, _: CurrentAdmin):
    category = crud.update(db, category_id, **payload.model_dump(exclude_none=True))
    return ApiResponse(data=CategoryOut.model_validate(category), message="分类已更新")


@router.delete("/{category_id}", response_model=ApiResponse[None], summary="删除分类（管理员）")
def delete_category(category_id: int, db: DbSession, _: CurrentAdmin):
    crud.delete(db, category_id)
    return ApiResponse(message="分类已删除")
