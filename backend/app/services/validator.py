import logging

logger = logging.getLogger(__name__)


def validate_questions(
    questions: list[dict],
    expected_count: int,
    include_answers: bool = True,
) -> list[dict]:
    valid: list[dict] = []
    seen: set[str] = set()

    for q in questions:
        if not isinstance(q, dict):
            continue

        question_text = (q.get("question") or "").strip()
        if not question_text:
            continue

        normalized = question_text.lower()
        if normalized in seen:
            continue
        seen.add(normalized)

        q_type = q.get("type", "open")
        options = q.get("options") or []

        if q_type == "single_choice" and len(options) != 4:
            continue

        item = {
            "question": question_text,
            "type": q_type,
            "options": options if options else None,
            "source_ref": q.get("source_ref"),
        }

        if include_answers:
            answer = q.get("answer")
            if not answer:
                continue
            item["answer"] = answer

        valid.append(item)

    return valid[:expected_count]
