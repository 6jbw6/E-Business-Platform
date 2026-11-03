"""本地文件存储：头像落盘、类型校验与静态暴露路径。"""

import re
import uuid
from pathlib import Path

from backend.app.core.config import PROJECT_ROOT, settings
from backend.app.core.exceptions import CODE_BAD_REQUEST, BizError

# 按文件头判断真实类型，不能相信客户端报的 Content-Type
_SIGNATURES: list[tuple[bytes, str, int]] = [
    (b"\xff\xd8\xff", "jpg", 3),
    (b"\x89PNG\r\n\x1a\n", "png", 8),
    (b"GIF87a", "gif", 6),
    (b"GIF89a", "gif", 6),
]

_RIFF_WEBP = re.compile(rb"^RIFF.{4}WEBP$", re.DOTALL)

AVATAR_SUBDIR = "avatars"


def upload_root() -> Path:
    root = Path(settings.upload_dir)
    if not root.is_absolute():
        root = PROJECT_ROOT / root
    return root


def avatar_dir() -> Path:
    path = upload_root() / AVATAR_SUBDIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def detect_image_extension(data: bytes) -> str | None:
    for magic, ext, _ in _SIGNATURES:
        if data.startswith(magic):
            return ext
    if _RIFF_WEBP.match(data[:16]):
        return "webp"
    return None


def save_avatar(user_id: int, data: bytes) -> str:
    """写入 uploads/avatars/ 并返回可直接放进 <img src> 的 URL 路径。"""
    if not data:
        raise BizError("上传的文件是空的", code=CODE_BAD_REQUEST, http_status=400)
    if len(data) > settings.max_avatar_bytes:
        raise BizError(
            f"图片太大，请控制在 {settings.max_avatar_bytes // 1024 // 1024} MB 以内",
            code=CODE_BAD_REQUEST,
            http_status=400,
        )

    extension = detect_image_extension(data)
    if extension is None:
        raise BizError("只支持 JPG / PNG / GIF / WebP 图片", code=CODE_BAD_REQUEST, http_status=400)

    # 文件名完全由服务端生成，绝不使用客户端传来的名字，避免路径穿越
    filename = f"{user_id}-{uuid.uuid4().hex[:12]}.{extension}"
    (avatar_dir() / filename).write_bytes(data)
    return f"{settings.upload_url_prefix}/{AVATAR_SUBDIR}/{filename}"


def delete_avatar(url: str | None) -> None:
    """清理用户换掉的旧头像；只认我们自己生成的那批文件名。"""
    if not url:
        return
    prefix = f"{settings.upload_url_prefix}/{AVATAR_SUBDIR}/"
    if not url.startswith(prefix):
        return
    filename = url[len(prefix) :]
    if not re.fullmatch(r"[a-zA-Z0-9_-]+\.(jpg|png|gif|webp)", filename):
        return
    target = avatar_dir() / filename
    if target.is_file():
        target.unlink(missing_ok=True)
