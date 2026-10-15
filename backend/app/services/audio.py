import asyncio
import shutil
from pathlib import Path

from app.core.limits import ValidationError


async def get_duration(path: Path) -> float:
    """Длительность медиафайла в секундах через ffprobe."""
    if shutil.which("ffprobe") is None:
        raise ValidationError("ffprobe не установлен", status_code=500)

    proc = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise ValidationError(f"Не удалось прочитать файл: {stderr.decode().strip()[:200]}")

    try:
        return float(stdout.decode().strip())
    except ValueError as e:
        raise ValidationError("Не удалось определить длительность") from e
