from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
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


def options_keyboard(include_summary: bool, include_answers: bool) -> InlineKeyboardMarkup:
    summary_mark = "✅" if include_summary else "❌"
    answers_mark = "✅" if include_answers else "❌"
    can_start = include_summary or include_answers

    rows = [
        [
            InlineKeyboardButton(
                text=f"{summary_mark} Конспект",
                callback_data="opt:summary",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{answers_mark} Ответы к вопросам",
                callback_data="opt:answers",
            )
        ],
    ]

    if can_start:
        rows.append(
            [InlineKeyboardButton(text="▶️ Запустить", callback_data="opt:start")]
        )
    else:
        rows.append(
            [InlineKeyboardButton(text="⛔ Нужно выбрать хотя бы одно", callback_data="opt:nope")]
        )

    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])

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