import logging

logger = logging.getLogger(__name__)


def validate_questions(questions: list[dict], expected_count: int) -> list[dict]:
    """Проверяет и чистит вопросы."""
    valid: list[dict] = []
    seen: set[str] = set()

    for q in questions:
        if not isinstance(q, dict):
            continue

        question_text = (q.get("question") or "").strip()
        if not question_text:
            continue

        # Дубликаты
        normalized = question_text.lower()
        if normalized in seen:
            logger.warning("Дубликат вопроса: %s", question_text[:50])
            continue
        seen.add(normalized)

        q_type = q.get("type", "open")
        options = q.get("options") or []

        # Для single_choice — ровно 4 опции
        if q_type == "single_choice" and len(options) != 4:
            logger.warning("single_choice с %d опциями: %s", len(options), question_text[:50])
            continue

        answer = q.get("answer")
        if not answer:
            continue

        valid.append({
            "question": question_text,
            "type": q_type,
            "options": options if options else None,
            "answer": answer,
            "source_ref": q.get("source_ref"),
        })

    return valid[:expected_count]