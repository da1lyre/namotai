from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.services.transcriber import calculate_whisper_cost, transcribe_audio


def test_calculate_whisper_cost():
    assert calculate_whisper_cost(100) == Decimal("1.00")
    assert calculate_whisper_cost(1800) == Decimal("18.00")
    assert calculate_whisper_cost(7200) == Decimal("72.00")


@pytest.mark.asyncio
async def test_transcribe_audio_success(tmp_path):
    """Мок httpx.AsyncClient.post."""
    fake_response = AsyncMock()
    fake_response.status_code = 200
    fake_response.json = lambda: {
        "text": "привет мир",
        "segments": [
            {"start": 0.0, "end": 2.5, "text": "привет"},
            {"start": 2.5, "end": 5.0, "text": "мир"},
        ],
        "language": "ru",
    }
    fake_response.raise_for_status = lambda: None

    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"fake")

    with patch("httpx.AsyncClient.post", return_value=fake_response):
        result = await transcribe_audio(audio_file)

    assert result["text"] == "привет мир"
    assert len(result["segments"]) == 2
    assert result["segments"][0]["start"] == 0.0
