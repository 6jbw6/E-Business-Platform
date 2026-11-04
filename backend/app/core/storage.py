"""本地文件存储：图片落盘、类型校验与静态暴露路径。"""

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
GOODS_SUBDIR = "goods"

# 只接受我们自己生成的那批文件名，防止 URL 里带 ../
_SAFE_FILENAME = re.compile(r"[a-zA-Z0-9_-]+\.(jpg|png|gif|webp)")


def upload_root() -> Path:
    root = Path(settings.upload_dir)
    if not root.is_absolute():
        root = PROJECT_ROOT / root
    return root


def image_dir(subdir: str) -> Path:
    path = upload_root() / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path


def detect_image_extension(data: bytes) -> str | None:
    for magic, ext, _ in _SIGNATURES:
        if data.startswith(magic):
            return ext
    if _RIFF_WEBP.match(data[:16]):
        return "webp"
    return None


def save_image(subdir: str, name_prefix: str, data: bytes) -> str:
    """写入 uploads/<subdir>/ 并返回可直接放进 <img src> 的 URL 路径。"""
    if not data:
        raise BizError("上传的文件是空的", code=CODE_BAD_REQUEST, http_status=400)
    if len(data) > settings.max_upload_bytes:
        raise BizError(
            f"图片太大，请控制在 {settings.max_upload_bytes // 1024 // 1024} MB 以内",
            code=CODE_BAD_REQUEST,
            http_status=400,
        )

    extension = detect_image_extension(data)
    if extension is None:
        raise BizError("只支持 JPG / PNG / GIF / WebP 图片", code=CODE_BAD_REQUEST, http_status=400)

    # 文件名完全由服务端生成，绝不使用客户端传来的名字，避免路径穿越
    filename = f"{name_prefix}-{uuid.uuid4().hex[:12]}.{extension}"
    (image_dir(subdir) / filename).write_bytes(data)
    return f"{settings.upload_url_prefix}/{subdir}/{filename}"


def delete_image(subdir: str, url: str | None) -> None:
    """清理用户换掉的旧图片；只认我们自己生成的那批文件名。"""
    if not url:
        return
    prefix = f"{settings.upload_url_prefix}/{subdir}/"
    if not url.startswith(prefix):
        return
    filename = url[len(prefix) :]
    if not _SAFE_FILENAME.fullmatch(filename):
        return
    target = image_dir(subdir) / filename
    if target.is_file():
        target.unlink(missing_ok=True)
