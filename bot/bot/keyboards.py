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


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Запустить", callback_data="confirm")],
            [
                InlineKeyboardButton(text="✏️ Изменить сложность", callback_data="edit:difficulty"),
                InlineKeyboardButton(text="✏️ Изменить количество", callback_data="edit:count"),
            ],
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