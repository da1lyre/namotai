import json
import logging
from decimal import Decimal

import httpx

from app.config import settings
from app.core.limits import ValidationError
from app.prompts.templates import build_prompt

logger = logging.getLogger(__name__)

# Тариф Selectel для Qwen-3.8-27B (₽ за 1M токенов, без НДС)
PRICE_INPUT_PER_1M = Decimal("31.01")
PRICE_OUTPUT_PER_1M = Decimal("206.50")


async def generate_questions(
    text: str,
    difficulty: str,
    question_count: int,
    source_type: str,
        include_summary: bool = True,
) -> dict:
    """
    Отправляет текст в Selectel LLM (Token Factory).
    Возвращает: {"summary": str, "questions": list, "tokens_input": int, "tokens_output": int}
    """
    prompt = build_prompt(
        text=text,
        difficulty=difficulty,
        question_count=question_count,
        source_type=source_type,
        include_summary=include_summary
    )

    url = f"{settings.selectel_base_url.rstrip('/')}/chat/completions"

    headers = {
        "Authorization": f"Bearer {settings.selectel_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.selectel_llm_model,
        "messages": [
            {"role": "developer", "content": prompt["system"]},
            {"role": "user", "content": prompt["user"]},
        ],
    }

    logger.info(
        "LLM request: url=%s model=%s tokens~=%d",
        url,
        settings.selectel_llm_model,
        len(text) // 4,
    )

    async with httpx.AsyncClient(timeout=300) as client:
        for attempt in range(1, 3):
            try:
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code >= 500:
                    logger.warning(
                        "Selectel вернул %d, попытка %d/2",
                        response.status_code, attempt,
                    )
                    if attempt == 2:
                        raise ValidationError(
                            f"LLM недоступен: {response.status_code}",
                            status_code=502,
                        )
                    continue

                if response.status_code >= 400:
                    logger.error(
                        "Selectel %d: %s",
                        response.status_code,
                        response.text[:500],
                    )
                    raise ValidationError(
                        f"LLM ошибка: {response.status_code}",
                        status_code=502,
                    )

                data = response.json()
                break

            except httpx.TimeoutException as e:
                if attempt == 2:
                    raise ValidationError("LLM: таймаут", status_code=504) from e
                logger.warning("LLM timeout, попытка %d/2", attempt)

    # Извлекаем ответ
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        logger.error("Неожиданный формат ответа: %s", str(data)[:500])
        raise ValidationError("LLM вернул неожиданный формат") from e

    # Парсим JSON (модель может обернуть в ```json ... ```)
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("LLM вернул невалидный JSON: %s", content[:500])
        raise ValidationError("LLM вернул невалидный JSON") from e

    usage = data.get("usage", {})
    tokens_input = usage.get("prompt_tokens", 0)
    tokens_output = usage.get("completion_tokens", 0)

    return {
        "summary": parsed.get("summary", ""),
        "questions": parsed.get("questions", []),
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
    }


def calculate_llm_cost(tokens_input: int, tokens_output: int) -> Decimal:
    """Стоимость LLM в рублях."""
    cost_in = Decimal(tokens_input) / Decimal(1_000_000) * PRICE_INPUT_PER_1M
    cost_out = Decimal(tokens_output) / Decimal(1_000_000) * PRICE_OUTPUT_PER_1M
    return (cost_in + cost_out).quantize(Decimal("0.01"))