MAX_MESSAGE_LENGTH = 4000

DIFFICULTY_LABELS = {
    "easy": "🟢 Лёгкая",
    "medium": "🟡 Средняя",
    "hard": "🔴 Сложная",
}


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def humanize_error(error: Exception) -> str:
    """Превращает техническую ошибку в человеческое сообщение."""
    msg = str(error).lower()

    if "413" in msg or "больше" in msg or "too large" in msg:
        return (
            "😔 Файл слишком большой. Максимум — 100 МБ.\n\n"
            "Попробуй сжать видео или отправь другой файл."
        )

    if "422" in msg or "не поддерживается" in msg:
        return (
            "😔 Не удалось обработать файл.\n\n"
            "Проверь формат: видео — mp4, mov, mkv, webm; "
            "текст — txt, docx, pdf."
        )

    if "длиннее" in msg or "2 часов" in msg or "7200" in msg:
        return "😔 Видео слишком длинное. Максимум — 2 часа.\n\nПопробуй разбить его на части."

    if "короткий" in msg or "100 символов" in msg:
        return "😔 Текст слишком короткий. Нужно минимум 100 символов."

    if "connect" in msg or "timeout" in msg or "network" in msg:
        return "😔 Не удалось связаться с сервером.\n\nПопробуй ещё раз через минуту."

    return "😔 Что-то пошло не так при обработке.\n\nПопробуй ещё раз или отправь другой материал."


def format_result(
    summary: str,
    questions: list[dict],
    include_summary: bool = True,
) -> str:
    parts: list[str] = []

    if include_summary and summary:
        parts.append(f"📝 <b>Конспект</b>\n\n{escape_html(summary)}\n")

    if questions:
        parts.append("❓ <b>Вопросы</b>\n")
        for i, q in enumerate(questions, 1):
            parts.append(_format_question(i, q))

    return "\n".join(parts)


def _format_question(index: int, q: dict) -> str:
    lines = [f"\n<b>{index}. {escape_html(q.get('question', ''))}</b>"]

    options = q.get("options") or []
    for j, opt in enumerate(options):
        letter = chr(ord("A") + j)
        lines.append(f"   {letter}) {escape_html(str(opt))}")

    answer = q.get("answer")
    if isinstance(answer, list):
        answer = ", ".join(str(a) for a in answer)
    lines.append(f"\n   ✅ <i>Ответ: {escape_html(str(answer))}</i>")

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
