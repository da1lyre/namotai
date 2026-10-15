import logging
from decimal import Decimal
from pathlib import Path

import httpx

from app.config import settings
from app.core.limits import ValidationError

logger = logging.getLogger(__name__)

WHISPER_PRICE_PER_SEC = Decimal("0.01")  # ₽ без НДС [citation:1]


async def transcribe_audio(audio_path: Path) -> dict:
    """
    Отправляет аудио в Whisper (Cloud.ru Foundation Models).
    Возвращает {"text": str, "segments": [...], "language": str}.
    """
    url = f"{settings.cloud_ru_base_url.rstrip('/')}/audio/transcriptions"

    headers = {"Authorization": f"Bearer {settings.cloud_ru_api_key}"}

    # Whisper на Cloud.ru — OpenAI-совместимый API
    # model: openai/whisper-large-v3 [citation:7]
    async with httpx.AsyncClient(timeout=600) as client:
        for attempt in range(1, 3):  # 2 попытки
            try:
                with open(audio_path, "rb") as f:
                    response = await client.post(
                        url,
                        headers=headers,
                        files={"file": (audio_path.name, f, "audio/wav")},
                        data={
                            "model": settings.whisper_model or "openai/whisper-large-v3",
                            "language": "ru",
                            "response_format": "verbose_json",
                        },
                    )

                if response.status_code >= 500:
                    logger.warning(
                        "Whisper вернул %d, попытка %d/2",
                        response.status_code,
                        attempt,
                    )
                    if attempt == 2:
                        raise ValidationError(
                            f"Whisper недоступен: {response.status_code}",
                            status_code=502,
                        )
                    continue

                response.raise_for_status()
                data = response.json()
                break

            except httpx.TimeoutException as e:
                if attempt == 2:
                    raise ValidationError("Whisper: таймаут", status_code=504) from e
                logger.warning("Whisper timeout, попытка %d/2", attempt)

    text = data.get("text", "").strip()
    segments = data.get("segments", [])
    language = data.get("language", "ru")

    if not text:
        raise ValidationError("Whisper вернул пустой транскрипт")

    # Нормализуем сегменты под наш формат
    normalized = [
        {
            "start": float(seg.get("start", 0)),
            "end": float(seg.get("end", 0)),
            "text": seg.get("text", "").strip(),
        }
        for seg in segments
        if seg.get("text", "").strip()
    ]

    return {
        "text": text,
        "segments": normalized,
        "language": language,
    }


def calculate_whisper_cost(duration_sec: int) -> Decimal:
    """Стоимость Whisper: 0.1 ₽ за секунду аудио (без НДС) [citation:1]."""
    return (Decimal(duration_sec) * WHISPER_PRICE_PER_SEC).quantize(Decimal("0.01"))
