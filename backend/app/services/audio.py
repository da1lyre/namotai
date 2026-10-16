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


async def extract_audio(video_path: Path, audio_path: Path) -> None:
    """Извлекает аудио из видео в WAV 16kHz mono через ffmpeg."""
    if shutil.which("ffmpeg") is None:
        raise ValidationError("ffmpeg не установлен", status_code=500)

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-i",
        str(video_path),
        "-vn",  # без видео
        "-ac",
        "1",  # mono
        "-ar",
        "16000",  # 16 kHz
        "-f",
        "wav",
        "-y",  # перезаписать
        str(audio_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise ValidationError(f"ffmpeg error: {stderr.decode().strip()[:300]}")

    if not audio_path.exists() or audio_path.stat().st_size == 0:
        raise ValidationError("Не удалось извлечь аудио из видео")
