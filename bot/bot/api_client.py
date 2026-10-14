import httpx
from bot.config import settings


async def generate_from_file(
    file_bytes: bytes,
    filename: str,
    difficulty: str,
    question_count: int,
) -> dict:
    async with httpx.AsyncClient(timeout=600) as client:
        response = await client.post(
            f"{settings.api_url}/api/generate",
            files={"file": (filename, file_bytes)},
            data={
                "source_type": "video",
                "difficulty": difficulty,
                "question_count": question_count,
            },
        )
        response.raise_for_status()
        return response.json()


async def generate_from_text(
    text: str,
    difficulty: str,
    question_count: int,
) -> dict:
    async with httpx.AsyncClient(timeout=600) as client:
        response = await client.post(
            f"{settings.api_url}/api/generate",
            data={
                "text": text,
                "source_type": "text",
                "difficulty": difficulty,
                "question_count": question_count,
            },
        )
        response.raise_for_status()
        return response.json()