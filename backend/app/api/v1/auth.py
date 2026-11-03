"""登录、注册与个人资料。"""

from fastapi import APIRouter, status

from backend.app.core.config import settings
from backend.app.core.deps import CurrentUser, DbSession
from backend.app.core.security import create_access_token
from backend.app.crud import user as crud_user
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.user import (
    LoginRequest,
    RegisterRequest,
    TokenOut,
    UserOut,
    UserUpdateRequest,
)

router = APIRouter(prefix="/auth", tags=["用户与登录"])


@router.post(
    "/register",
    response_model=ApiResponse[UserOut],
    status_code=status.HTTP_201_CREATED,
    summary="注册新用户",
)
def register(payload: RegisterRequest, db: DbSession):
    user = crud_user.register(
        db,
        username=payload.username,
        password=payload.password,
        nickname=payload.nickname,
        phone=payload.phone,
        email=payload.email,
    )
    return ApiResponse(data=UserOut.model_validate(user), message="注册成功")


@router.post("/login", response_model=ApiResponse[TokenOut], summary="登录换取访问令牌")
def login(payload: LoginRequest, db: DbSession):
    user = crud_user.authenticate(db, payload.username, payload.password)
    token = create_access_token(user.id, role=user.role)
    data = TokenOut(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
        user=UserOut.model_validate(user),
    )
    return ApiResponse(data=data, message="登录成功")


@router.get("/me", response_model=ApiResponse[UserOut], summary="查看当前登录用户")
def read_me(user: CurrentUser):
    return ApiResponse(data=UserOut.model_validate(user))


@router.put("/me", response_model=ApiResponse[UserOut], summary="修改个人资料")
def update_me(payload: UserUpdateRequest, user: CurrentUser, db: DbSession):
    updated = crud_user.update_profile(db, user, **payload.model_dump(exclude_none=True))
    return ApiResponse(data=UserOut.model_validate(updated), message="资料已更新")
