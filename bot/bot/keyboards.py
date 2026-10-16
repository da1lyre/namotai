from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📹 Загрузить видео")],
            [KeyboardButton(text="📄 Загрузить текст")],
            [KeyboardButton(text="ℹ️ Помощь")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие или отправь файл",
    )


def difficulty_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Лёгкая", callback_data="diff:easy")],
            [InlineKeyboardButton(text="🟡 Средняя", callback_data="diff:medium")],
            [InlineKeyboardButton(text="🔴 Сложная", callback_data="diff:hard")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
    )


def count_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="5", callback_data="count:5"),
                InlineKeyboardButton(text="7", callback_data="count:7"),
                InlineKeyboardButton(text="10", callback_data="count:10"),
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
    )


def options_keyboard(
    include_summary: bool,
    include_answers: bool,
    delivery: str,
    file_format: str,
) -> InlineKeyboardMarkup:
    summary_mark = "✅" if include_summary else "❌"
    answers_mark = "✅" if include_answers else "❌"
    chat_mark = "✅" if delivery == "chat" else "⬜"
    file_mark = "✅" if delivery == "file" else "⬜"
    md_mark = "✅" if file_format == "md" else "⬜"
    pdf_mark = "✅" if file_format == "pdf" else "⬜"

    rows = [
        [
            InlineKeyboardButton(
                text=f"{summary_mark} Конспект",
                callback_data="opt:toggle:summary",
            ),
            InlineKeyboardButton(
                text=f"{answers_mark} Ответы",
                callback_data="opt:toggle:answers",
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{chat_mark} В чат",
                callback_data="opt:delivery:chat",
            ),
            InlineKeyboardButton(
                text=f"{file_mark} Файлом",
                callback_data="opt:delivery:file",
            ),
        ],
    ]

    if delivery == "file":
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{md_mark} MD",
                    callback_data="opt:format:md",
                ),
                InlineKeyboardButton(
                    text=f"{pdf_mark} PDF",
                    callback_data="opt:format:pdf",
                ),
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(text="▶️ Запустить", callback_data="opt:start"),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Запустить", callback_data="confirm")],
            [
                InlineKeyboardButton(text="✏️ Сложность", callback_data="edit:difficulty"),
                InlineKeyboardButton(text="✏️ Количество", callback_data="edit:count"),
            ],
            [InlineKeyboardButton(text="⚙️ Опции", callback_data="edit:options")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
    )


def after_result_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Ещё раз", callback_data="restart")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="menu")],
        ]
    )


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
    )
