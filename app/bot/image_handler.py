import io, os, base64
from telethon.tl.types import MessageMediaPhoto

def _sniff_mime(data: bytes) -> str | None:
    if data.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    if data.startswith(b'GIF87a') or data.startswith(b'GIF89a'):
        return 'image/gif'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'image/webp'
    return None  # не угадали — лучше отфейлиться, чем врать

async def download_image_as_data_url(msg):
    # 1) Пытаемся скачать в память
    buf = io.BytesIO()
    try:
        await msg.download_media(file=buf)  # НЕ через client
        data = buf.getvalue()
    except Exception:
        data = b""

    # 2) Фолбэк: путь на диск
    if not data:
        path = await msg.download_media()  # вернёт путь
        if not path:
            return None
        try:
            with open(path, "rb") as f:
                data = f.read()
        finally:
            try:
                os.remove(path)
            except Exception:
                pass

    if not data:
        return None

    mime = _sniff_mime(data)
    if not mime:
        return None

    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"

def is_image(msg) -> bool:
    # вариант 1: фото
    if isinstance(msg.media, MessageMediaPhoto):
        return True

    # вариант 2: документ с image/*
    if msg.document and msg.document.mime_type:
        return msg.document.mime_type.startswith("image/")

    return False