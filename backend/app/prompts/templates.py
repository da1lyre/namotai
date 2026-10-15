DIFFICULTY_INSTRUCTIONS = {
    "easy": (
        "Составь вопросы на проверку базовых фактов и определений. "
        "Простые формулировки, прямой ответ из текста."
    ),
    "medium": (
        "Составь вопросы на понимание и связи между понятиями. "
        "Требуют осмысления, а не простого воспроизведения."
    ),
    "hard": (
        "Составь вопросы на анализ, синтез и оценку. "
        "Нестандартные формулировки, требуют размышления."
    ),
}


SYSTEM_PROMPT = """Ты — опытный методист, который создаёт учебные задания по материалу.

Твоя задача:
1. Прочитать предоставленный материал.
{summary_instruction}
3. Придумать {count} качественных вопросов для проверки понимания.

Требования к вопросам:
- {difficulty_instruction}
- Язык вопросов = язык материала.
- Вопросы НЕ дублируются.
- Вопросы осмысленные, НЕ шаблонные.
- Каждый вопрос опирается на конкретный фрагмент материала.
- Для типа single_choice — ровно 4 варианта ответа.
- Типы вопросов: single_choice, multiple_choice, open.

Формат ответа — строго JSON:
{{
  "summary": "конспект или пустая строка, если не нужен",
  "questions": [
    {{
      "question": "текст вопроса",
      "type": "single_choice | multiple_choice | open",
      "options": ["A", "B", "C", "D"],
      "answer": "правильный ответ или массив",
      "source_ref": {{"chunk": 1}}
    }}
  ]
}}

Никаких обёрток, никаких пояснений — только JSON."""

def build_prompt(
    text: str,
    difficulty: str,
    question_count: int,
    source_type: str,
    include_summary: bool = True,
) -> dict:
    difficulty_instruction = DIFFICULTY_INSTRUCTIONS.get(
        difficulty, DIFFICULTY_INSTRUCTIONS["medium"]
    )

    summary_instruction = (
        "2. Составить краткий конспект (3–7 предложений)."
        if include_summary
        else "2. Конспект НЕ нужен — пропусти этот шаг."
    )

    system = SYSTEM_PROMPT.format(
        count=question_count,
        difficulty_instruction=difficulty_instruction,
        summary_instruction=summary_instruction,
    )

    return {"system": system, "user": f"Материал:\n\n{text}"}