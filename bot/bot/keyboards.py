from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def difficulty_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Лёгкая", callback_data="diff:easy")],
            [InlineKeyboardButton(text="Средняя", callback_data="diff:medium")],
            [InlineKeyboardButton(text="Сложная", callback_data="diff:hard")],
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
        ]
    )
