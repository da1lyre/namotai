import logging

import httpx

from bot.config import settings

logger = logging.getLogger(__name__)


async def generate_from_file(
    file_bytes: bytes,
    filename: str,
    difficulty: str,
    question_count: int,
    source_type: str = "video",
    include_summary: bool = True,
) -> dict:
    async with httpx.AsyncClient(timeout=600) as client:
        response = await client.post(
            f"{settings.api_url}/api/generate",
            files={"file": (filename, file_bytes)},
            data={
                "source_type": source_type,
                "difficulty": difficulty,
                "question_count": question_count,
                "include_summary": str(include_summary).lower(),
            },
        )
        if response.status_code >= 400:
            logger.error("API %d: %s", response.status_code, response.text[:500])
        response.raise_for_status()
        return response.json()


async def generate_from_text(
    text: str,
    difficulty: str,
    question_count: int,
    include_summary: bool = True,
) -> dict:
    async with httpx.AsyncClient(timeout=600) as client:
        response = await client.post(
            f"{settings.api_url}/api/generate",
            data={
                "text": text,
                "source_type": "text",
                "difficulty": difficulty,
                "question_count": question_count,
                "include_summary": str(include_summary).lower(),
            },
        )
        if response.status_code >= 400:
            logger.error("API %d: %s", response.status_code, response.text[:500])
        response.raise_for_status()
        return response.json()