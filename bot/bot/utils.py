MAX_MESSAGE_LENGTH = 4000

DIFFICULTY_LABELS = {
    "easy": "Лёгкая",
    "medium": "Средняя",
    "hard": "Сложная",
}


def humanize_error(error: Exception) -> str:
    msg = str(error).lower()

    if "413" in msg or "больше" in msg or "too large" in msg:
        return "😔 Файл слишком большой. Максимум — 100 МБ."

    if "422" in msg or "не поддерживается" in msg:
        return "😔 Не удалось обработать файл. Проверь формат."

    if "длиннее" in msg or "7200" in msg:
        return "😔 Видео слишком длинное. Максимум — 2 часа."

    if "короткий" in msg or "100 символов" in msg:
        return "😔 Текст слишком короткий. Нужно минимум 100 символов."

    if "connect" in msg or "timeout" in msg or "network" in msg:
        return "😔 Не удалось связаться с сервером. Попробуй ещё раз."

    if "json" in msg:
        return "😔 Модель вернула некорректный ответ. Попробуй ещё раз."

    return "😔 Что-то пошло не так при обработке."


def format_summary(summary: str) -> str:
    return f"📝 Конспект\n\n{summary}"


def format_questions_only(questions: list[dict]) -> str:
    lines = ["❓ Вопросы\n"]
    for i, q in enumerate(questions, 1):
        lines.append(f"\n{i}. {q.get('question', '')}")
        options = q.get("options") or []
        for j, opt in enumerate(options):
            letter = chr(ord("A") + j)
            lines.append(f"   {letter}) {opt}")
    return "\n".join(lines)


def format_answers_only(questions: list[dict]) -> str:
    lines = ["✅ Ответы\n"]
    for i, q in enumerate(questions, 1):
        answer = q.get("answer")
        if not answer:
            continue
        if isinstance(answer, list):
            answer = ", ".join(str(a) for a in answer)
        lines.append(f"{i}. {answer}")
    return "\n".join(lines)


def split_message(text: str, limit: int = MAX_MESSAGE_LENGTH) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in text.split("\n"):
        line_len = len(line) + 1
        if current_len + line_len > limit and current:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += line_len

    if current:
        chunks.append("\n".join(current))

    return chunks