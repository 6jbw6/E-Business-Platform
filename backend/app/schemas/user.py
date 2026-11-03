"""用户与鉴权相关的请求/响应模型。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.models.user import ROLE_USER


class RegisterRequest(BaseModel):
    username: str = Field(min_length=4, max_length=32, description="登录名，4-32 位字母或数字")
    password: str = Field(min_length=6, max_length=64, description="登录密码，6-64 位")
    nickname: str = Field(default="", max_length=32, description="昵称，留空则取登录名")
    phone: str | None = Field(default=None, max_length=20, description="手机号")
    email: str | None = Field(default=None, max_length=128, description="邮箱")

    @field_validator("username")
    @classmethod
    def _username_pattern(cls, v: str) -> str:
        v = v.strip()
        if not v.isalnum():
            raise ValueError("登录名只能由字母和数字组成")
        return v

    @field_validator("phone")
    @classmethod
    def _phone_pattern(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v.isdigit():
            raise ValueError("手机号只能是数字")
        return v or None


class LoginRequest(BaseModel):
    username: str = Field(description="登录名")
    password: str = Field(description="登录密码")


class TokenOut(BaseModel):
    access_token: str = Field(description="JWT 访问令牌，放到 Authorization: Bearer <token> 里")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="有效期，单位秒")
    user: "UserOut" = Field(description="登录用户信息")


class UserUpdateRequest(BaseModel):
    nickname: str | None = Field(default=None, max_length=32)
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=128)
    avatar: str | None = Field(default=None, max_length=255)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="用户ID")
    username: str = Field(description="登录名")
    nickname: str = Field(description="昵称")
    phone: str | None = Field(default=None, description="手机号")
    email: str | None = Field(default=None, description="邮箱")
    avatar: str = Field(default="", description="头像地址")
    role: str = Field(default=ROLE_USER, description="角色：user=普通用户，admin=管理员")
    status: int = Field(description="状态：1=正常，0=禁用")
    created_at: datetime | None = Field(default=None, description="注册时间")


TokenOut.model_rebuild()
