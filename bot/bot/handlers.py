import asyncio
import logging
from pathlib import Path

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.states import GenerateFlow
from bot.keyboards import (
    main_menu,
    difficulty_keyboard,
    count_keyboard,
    confirm_keyboard,
    after_result_keyboard,
    cancel_keyboard,
)
from bot.api_client import generate_from_file, generate_from_text
from bot.utils import (
    DIFFICULTY_LABELS,
    format_result,
    humanize_error,
    split_message,
)

router = Router()
logger = logging.getLogger(__name__)

VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
TEXT_EXT = {".txt", ".docx", ".pdf"}


WELCOME_TEXT = (
    "👋 <b>Привет! Я Namotai</b> — помощник для активного обучения.\n\n"
    "Превращаю видео и текст в конспект и вопросы для закрепления материала.\n\n"
    "<b>Что можно отправить:</b>\n"
    "📹 Видео — mp4, mov, mkv, webm\n"
    "📄 Документ — txt, docx, pdf\n"
    "✍️ Или просто текст сообщением\n\n"
    "Погнали? 👇"
)


HELP_TEXT = (
    "ℹ️ <b>Как пользоваться</b>\n\n"
    "1. Отправь видео, документ или текст\n"
    "2. Выбери сложность вопросов\n"
    "3. Выбери количество вопросов (5–10)\n"
    "4. Подтверди запуск\n"
    "5. Дождись результата\n\n"
    "<b>Что получишь:</b>\n"
    "• Краткий конспект материала\n"
    "• Вопросы с ответами для самопроверки\n\n"
    "<b>Команды:</b>\n"
    "/start — начать заново\n"
    "/help — эта справка\n"
    "/cancel — отменить текущее действие"
)


UNKNOWN_TEXT = (
    "🤔 Не понял. Я умею работать с видео и текстом.\n\n"
    "Отправь:\n"
    "• 📹 Видеофайл\n"
    "• 📄 Документ (txt, docx, pdf)\n"
    "• ✍️ Текст сообщением\n\n"
    "Или нажми /help"
)


# ─── Команды ───────────────────────────────────────────────

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=main_menu())
    await state.set_state(GenerateFlow.waiting_for_source)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu())


@router.message(Command("cancel"))
@router.callback_query(F.data == "cancel")
async def cmd_cancel(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if isinstance(event, CallbackQuery):
        await event.message.edit_text("❌ Действие отменено.")
        await event.answer()
    else:
        await event.answer("❌ Действие отменено.", reply_markup=main_menu())
    await state.set_state(GenerateFlow.waiting_for_source)


@router.callback_query(F.data == "menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Главное меню 👇", reply_markup=main_menu())
    await callback.answer()
    await state.set_state(GenerateFlow.waiting_for_source)


@router.callback_query(F.data == "restart")
async def restart(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(
        "Скидывай новый материал 👇",
        reply_markup=main_menu(),
    )
    await callback.answer()
    await state.set_state(GenerateFlow.waiting_for_source)


# ─── Кнопки-подсказки ──────────────────────────────────────

@router.message(F.text == "📹 Загрузить видео")
async def prompt_video(message: Message, state: FSMContext) -> None:
    await state.set_state(GenerateFlow.waiting_for_source)
    await message.answer(
        "📹 Отправь видеофайл (mp4, mov, mkv, webm).\n\n"
        "Можно прикрепить как видео или как документ.",
        reply_markup=cancel_keyboard(),
    )


@router.message(F.text == "📄 Загрузить текст")
async def prompt_text(message: Message, state: FSMContext) -> None:
    await state.set_state(GenerateFlow.waiting_for_source)
    await message.answer(
        "📄 Отправь текст сообщением, или прикрепи файл (txt, docx, pdf).",
        reply_markup=cancel_keyboard(),
    )


@router.message(F.text == "ℹ️ Помощь")
async def prompt_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu())


# ─── Приём материала ───────────────────────────────────────

@router.message(GenerateFlow.waiting_for_source, F.video)
@router.message(GenerateFlow.waiting_for_source, F.document)
@router.message(GenerateFlow.waiting_for_source, F.audio)
async def handle_file(message: Message, state: FSMContext) -> None:
    if message.video:
        file_id = message.video.file_id
        filename = message.video.file_name or "video.mp4"
        size_mb = (message.video.file_size or 0) / (1024 * 1024)
    elif message.audio:
        file_id = message.audio.file_id
        filename = message.audio.file_name or "audio.mp3"
        size_mb = (message.audio.file_size or 0) / (1024 * 1024)
    else:
        file_id = message.document.file_id
        filename = message.document.file_name or "file"
        size_mb = (message.document.file_size or 0) / (1024 * 1024)

    await state.update_data(
        file_id=file_id,
        filename=filename,
        size_mb=size_mb,
        source_type="file",
    )
    await state.set_state(GenerateFlow.waiting_for_difficulty)
    await message.answer(
        f"📎 Получил: <b>{filename}</b> ({size_mb:.1f} МБ)\n\n"
        "<b>Что дальше:</b>\n"
        "1. Выбери сложность вопросов\n"
        "2. Выбери количество\n"
        "3. Подтверди запуск\n\n"
        "Выбери сложность:",
        reply_markup=difficulty_keyboard(),
    )


@router.message(GenerateFlow.waiting_for_source, F.text)
async def handle_text(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text.startswith("/"):
        return

    if len(text) < 100:
        await message.answer(
            "⚠️ Текст слишком короткий. Отправь хотя бы пару абзацев.",
            reply_markup=cancel_keyboard(),
        )
        return

    await state.update_data(text=text, source_type="text_input")
    await state.set_state(GenerateFlow.waiting_for_difficulty)
    await message.answer(
        f"📝 Получил текст ({len(text)} символов)\n\n"
        "<b>Что дальше:</b>\n"
        "1. Выбери сложность вопросов\n"
        "2. Выбери количество\n"
        "3. Подтверди запуск\n\n"
        "Выбери сложность:",
        reply_markup=difficulty_keyboard(),
    )


@router.message(GenerateFlow.waiting_for_source)
async def unknown_message(message: Message) -> None:
    await message.answer(UNKNOWN_TEXT, reply_markup=main_menu())


# ─── Выбор параметров ──────────────────────────────────────

@router.callback_query(GenerateFlow.waiting_for_difficulty, F.data.startswith("diff:"))
async def handle_difficulty(callback: CallbackQuery, state: FSMContext) -> None:
    difficulty = callback.data.split(":")[1]
    await state.update_data(difficulty=difficulty)
    await state.set_state(GenerateFlow.waiting_for_count)
    await callback.message.edit_text(
        f"Сложность: <b>{DIFFICULTY_LABELS[difficulty]}</b>\n\n"
        "Сколько вопросов сгенерировать?",
        reply_markup=count_keyboard(),
    )
    await callback.answer()


@router.callback_query(GenerateFlow.waiting_for_count, F.data.startswith("count:"))
async def handle_count(callback: CallbackQuery, state: FSMContext) -> None:
    count = int(callback.data.split(":")[1])
    await state.update_data(question_count=count)
    await state.set_state(GenerateFlow.waiting_for_confirmation)

    data = await state.get_data()
    await callback.message.edit_text(
        _confirmation_text(data),
        reply_markup=confirm_keyboard(),
    )
    await callback.answer()


def _confirmation_text(data: dict) -> str:
    if data["source_type"] == "text_input":
        source_info = f"📄 Текст: {len(data['text'])} символов"
    else:
        source_info = (
            f"📎 Файл: <b>{data['filename']}</b> ({data['size_mb']:.1f} МБ)"
        )

    return (
        "📋 <b>Проверь перед запуском</b>\n\n"
        f"{source_info}\n"
        f"🎯 Сложность: <b>{DIFFICULTY_LABELS[data['difficulty']]}</b>\n"
        f"❓ Вопросов: <b>{data['question_count']}</b>\n\n"
        "Всё верно?"
    )


# ─── Редактирование параметров ─────────────────────────────

@router.callback_query(GenerateFlow.waiting_for_confirmation, F.data == "edit:difficulty")
async def edit_difficulty(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(GenerateFlow.waiting_for_difficulty)
    await callback.message.edit_text(
        "Выбери сложность:",
        reply_markup=difficulty_keyboard(),
    )
    await callback.answer()


@router.callback_query(GenerateFlow.waiting_for_confirmation, F.data == "edit:count")
async def edit_count(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(GenerateFlow.waiting_for_count)
    await callback.message.edit_text(
        "Сколько вопросов?",
        reply_markup=count_keyboard(),
    )
    await callback.answer()


# ─── Запуск обработки ──────────────────────────────────────

@router.callback_query(GenerateFlow.waiting_for_confirmation, F.data == "confirm")
async def handle_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    await state.set_state(GenerateFlow.processing)

    try:
        progress_msg = await callback.message.edit_text(
            "⏳ <b>Обрабатываю материал...</b>\n\n"
            "▓░░░░░░░░░ 10%\n"
            "Читаю материал...",
        )
    except Exception:
        progress_msg = callback.message

    progress_task = asyncio.create_task(
        _update_progress(progress_msg, callback.bot)
    )

    try:
        if data["source_type"] == "text_input":
            result = await generate_from_text(
                text=data["text"],
                difficulty=data["difficulty"],
                question_count=data["question_count"],
            )
        else:
            file = await callback.bot.get_file(data["file_id"])
            file_bytes = await callback.bot.download_file(file.file_path)

            filename = data["filename"]
            ext = Path(filename).suffix.lower()
            source_type = "video" if ext in VIDEO_EXT else "text"

            result = await generate_from_file(
                file_bytes=file_bytes.read(),
                filename=filename,
                difficulty=data["difficulty"],
                question_count=data["question_count"],
                source_type=source_type,
            )

        progress_task.cancel()

        try:
            await callback.message.delete()
        except Exception:
            pass

        await send_result(callback.message, result)

    except Exception as e:
        progress_task.cancel()
        logger.exception("Ошибка при обработке")
        try:
            await callback.message.edit_text(
                humanize_error(e),
                reply_markup=after_result_keyboard(),
            )
        except Exception:
            await callback.message.answer(
                humanize_error(e),
                reply_markup=after_result_keyboard(),
            )
    finally:
        await state.clear()


async def _update_progress(message: Message, bot) -> None:
    stages = [
        (10, "▓░░░░░░░░░ 10%\nЧитаю материал..."),
        (30, "▓▓▓░░░░░░░ 30%\nРазбираю содержимое..."),
        (60, "▓▓▓▓▓░░░░░ 50%\nГотовлю конспект..."),
        (90, "▓▓▓▓▓▓▓░░░ 70%\nГенерирую вопросы..."),
    ]
    try:
        for delay, text in stages:
            await asyncio.sleep(delay)
            try:
                await message.edit_text(
                    f"⏳ <b>Обрабатываю материал...</b>\n\n{text}"
                )
            except Exception:
                pass
    except asyncio.CancelledError:
        pass


# ─── Отправка результата ───────────────────────────────────

async def send_result(message: Message, result: dict) -> None:
    summary = result.get("summary", "")
    questions = result.get("questions", [])

    if not summary and not questions:
        await message.answer(
            "⚠️ Не удалось сгенерировать результат. Попробуй другой материал.",
            reply_markup=after_result_keyboard(),
        )
        return

    header = f"✅ <b>Готово!</b> Конспект и {len(questions)} вопросов.\n"
    await message.answer(header)

    if summary:
        await message.answer(f"📝 <b>Конспект</b>\n\n{summary}")

    if questions:
        for chunk in split_message(format_result("", questions, include_summary=False)):
            if chunk.strip():
                await message.answer(chunk)

    await message.answer(
        "Что дальше?",
        reply_markup=after_result_keyboard(),
    )