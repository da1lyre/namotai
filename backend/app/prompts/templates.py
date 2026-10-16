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


def build_prompt(
    text: str,
    difficulty: str,
    question_count: int,
    source_type: str,
    include_summary: bool = True,
    include_answers: bool = True,
) -> dict:
    difficulty_instruction = DIFFICULTY_INSTRUCTIONS.get(
        difficulty, DIFFICULTY_INSTRUCTIONS["medium"]
    )

    # Задачи
    tasks = ["1. Прочитать предоставленный материал."]
    if include_summary:
        tasks.append("2. Составить краткий конспект (3–7 предложений).")
    tasks.append(f"{len(tasks) + 1}. Придумать {question_count} качественных вопросов.")

    # Поля JSON
    answer_field = (
        ',\n      "answer": "правильный ответ или массив"'
        if include_answers
        else ""
    )
    summary_field = (
        '"summary": "конспект в 3-7 предложениях",'
        if include_summary
        else '"summary": "",'
    )

    system = f"""Ты — опытный методист, который создаёт учебные задания по материалу.

Твоя задача:
{chr(10).join(tasks)}

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
  {summary_field}
  "questions": [
    {{
      "question": "текст вопроса",
      "type": "single_choice | multiple_choice | open",
      "options": ["A", "B", "C", "D"],
      "source_ref": {{"chunk": 1}}{answer_field}
    }}
  ]
}}

Никаких обёрток, никаких пояснений — только JSON."""

    return {"system": system, "user": f"Материал:\n\n{text}"}