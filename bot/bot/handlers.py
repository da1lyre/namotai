import logging
from pathlib import Path

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.api_client import (
    export_result,
    generate_from_file,
    generate_from_text,
)
from bot.keyboards import (
    after_result_keyboard,
    cancel_keyboard,
    confirm_keyboard,
    count_keyboard,
    difficulty_keyboard,
    main_menu,
    options_keyboard,
)
from bot.states import GenerateFlow
from bot.utils import (
    DIFFICULTY_LABELS,
    format_answers_only,
    format_questions_only,
    format_summary,
    humanize_error,
    split_message,
)

router = Router()
logger = logging.getLogger(__name__)

VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


WELCOME_TEXT = (
    "👋 Привет! Я Namotai — помощник для активного обучения.\n\n"
    "Превращаю видео и текст в конспект и вопросы для закрепления материала.\n\n"
    "Что можно отправить:\n"
    "📹 Видео — mp4, mov, mkv, webm\n"
    "📄 Документ — txt, docx, pdf\n"
    "✍️ Или просто текст сообщением\n\n"
    "Погнали? 👇"
)


HELP_TEXT = (
    "ℹ️ Как пользоваться\n\n"
    "1. Отправь видео, документ или текст\n"
    "2. Выбери сложность вопросов\n"
    "3. Выбери количество вопросов (5–10)\n"
    "4. Настрой опции: конспект, ответы, доставка\n"
    "5. Подтверди запуск\n"
    "6. Дождись результата\n\n"
    "Команды:\n"
    "/start — начать заново\n"
    "/help — эта справка\n"
    "/cancel — отменить текущее действие"
)


UNKNOWN_TEXT = (
    "🤔 Не понял. Я умею работать с видео и текстом.\n\n"
    "Отправь:\n"
    "📹 Видеофайл\n"
    "📄 Документ (txt, docx, pdf)\n"
    "✍️ Текст сообщением\n\n"
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
    await callback.message.answer("Скидывай новый материал 👇", reply_markup=main_menu())
    await callback.answer()
    await state.set_state(GenerateFlow.waiting_for_source)


# ─── Кнопки-подсказки ──────────────────────────────────────


@router.message(F.text == "📹 Загрузить видео")
async def prompt_video(message: Message, state: FSMContext) -> None:
    await state.set_state(GenerateFlow.waiting_for_source)
    await message.answer(
        "📹 Отправь видеофайл (mp4, mov, mkv, webm).",
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
        f"📎 Получил: {filename} ({size_mb:.1f} МБ)\n\nВыбери сложность:",
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
        f"📝 Получил текст ({len(text)} символов)\n\nВыбери сложность:",
        reply_markup=difficulty_keyboard(),
    )


@router.message(GenerateFlow.waiting_for_source)
async def unknown_message(message: Message) -> None:
    await message.answer(UNKNOWN_TEXT, reply_markup=main_menu())


# ─── Сложность ─────────────────────────────────────────────


@router.callback_query(GenerateFlow.waiting_for_difficulty, F.data.startswith("diff:"))
async def handle_difficulty(callback: CallbackQuery, state: FSMContext) -> None:
    difficulty = callback.data.split(":")[1]
    await state.update_data(difficulty=difficulty)
    await state.set_state(GenerateFlow.waiting_for_count)
    await callback.message.edit_text(
        f"Сложность: {DIFFICULTY_LABELS[difficulty]}\n\nСколько вопросов сгенерировать?",
        reply_markup=count_keyboard(),
    )
    await callback.answer()


# ─── Количество ────────────────────────────────────────────


@router.callback_query(GenerateFlow.waiting_for_count, F.data.startswith("count:"))
async def handle_count(callback: CallbackQuery, state: FSMContext) -> None:
    count = int(callback.data.split(":")[1])
    await state.update_data(
        question_count=count,
        include_summary=True,
        include_answers=True,
        delivery="chat",
        file_format="md",
    )
    await state.set_state(GenerateFlow.waiting_for_options)
    await callback.message.edit_text(
        "⚙️ Настройки результата\n\nНажми на опции, чтобы изменить.",
        reply_markup=options_keyboard(True, True, "chat", "md"),
    )
    await callback.answer()


# ─── Опции ─────────────────────────────────────────────────


async def _refresh_options(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    try:
        await callback.message.edit_reply_markup(
            reply_markup=options_keyboard(
                include_summary=data.get("include_summary", True),
                include_answers=data.get("include_answers", True),
                delivery=data.get("delivery", "chat"),
                file_format=data.get("file_format", "md"),
            )
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@router.callback_query(GenerateFlow.waiting_for_options, F.data == "opt:toggle:summary")
async def toggle_summary(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.update_data(include_summary=not data.get("include_summary", True))
    await _refresh_options(callback, state)
    await callback.answer()


@router.callback_query(GenerateFlow.waiting_for_options, F.data == "opt:toggle:answers")
async def toggle_answers(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.update_data(include_answers=not data.get("include_answers", True))
    await _refresh_options(callback, state)
    await callback.answer()


@router.callback_query(GenerateFlow.waiting_for_options, F.data == "opt:delivery:chat")
async def set_delivery_chat(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(delivery="chat")
    await _refresh_options(callback, state)
    await callback.answer()


@router.callback_query(GenerateFlow.waiting_for_options, F.data == "opt:delivery:file")
async def set_delivery_file(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(delivery="file")
    await _refresh_options(callback, state)
    await callback.answer()


@router.callback_query(GenerateFlow.waiting_for_options, F.data == "opt:format:md")
async def set_format_md(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(file_format="md")
    await _refresh_options(callback, state)
    await callback.answer()


@router.callback_query(GenerateFlow.waiting_for_options, F.data == "opt:format:pdf")
async def set_format_pdf(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(file_format="pdf")
    await _refresh_options(callback, state)
    await callback.answer()


@router.callback_query(GenerateFlow.waiting_for_options, F.data == "opt:start")
async def options_done(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(GenerateFlow.waiting_for_confirmation)
    await callback.message.edit_text(
        _confirmation_text(data),
        reply_markup=confirm_keyboard(),
    )
    await callback.answer()


def _confirmation_text(data: dict) -> str:
    if data["source_type"] == "text_input":
        source_info = f"📄 Текст: {len(data['text'])} символов"
    else:
        source_info = f"📎 Файл: {data['filename']} ({data['size_mb']:.1f} МБ)"

    summary_mark = "✅" if data.get("include_summary", True) else "❌"
    answers_mark = "✅" if data.get("include_answers", True) else "❌"

    delivery = data.get("delivery", "chat")
    if delivery == "chat":
        delivery_info = "💬 В чат"
    else:
        fmt = data.get("file_format", "md").upper()
        delivery_info = f"📥 Файлом ({fmt})"

    return (
        "📋 Проверь перед запуском\n\n"
        f"{source_info}\n"
        f"🎯 Сложность: {DIFFICULTY_LABELS[data['difficulty']]}\n"
        f"❓ Вопросов: {data['question_count']}\n"
        f"📝 Конспект: {summary_mark}\n"
        f"✅ Ответы: {answers_mark}\n"
        f"📤 Доставка: {delivery_info}\n\n"
        "Всё верно?"
    )


# ─── Редактирование ────────────────────────────────────────


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


@router.callback_query(GenerateFlow.waiting_for_confirmation, F.data == "edit:options")
async def edit_options(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(GenerateFlow.waiting_for_options)
    await callback.message.edit_text(
        "⚙️ Настройки результата",
        reply_markup=options_keyboard(
            data.get("include_summary", True),
            data.get("include_answers", True),
            data.get("delivery", "chat"),
            data.get("file_format", "md"),
        ),
    )
    await callback.answer()


# ─── Запуск ────────────────────────────────────────────────


@router.callback_query(GenerateFlow.waiting_for_confirmation, F.data == "confirm")
async def handle_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    await state.set_state(GenerateFlow.processing)

    try:
        include_summary = data.get("include_summary", True)
        include_answers = data.get("include_answers", True)

        if data["source_type"] == "text_input":
            result = await generate_from_text(
                text=data["text"],
                difficulty=data["difficulty"],
                question_count=data["question_count"],
                include_summary=include_summary,
                include_answers=include_answers,
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
                include_summary=include_summary,
                include_answers=include_answers,
            )

        try:
            await callback.message.delete()
        except Exception:
            pass

        await send_result(callback.message, result, data)

    except Exception as e:
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


# ─── Результат ─────────────────────────────────────────────


async def send_result(message: Message, result: dict, data: dict) -> None:
    result_id = result.get("id", "")
    delivery = data.get("delivery", "chat")

    # Доставка файлом
    if delivery == "file":
        file_format = data.get("file_format", "md")
        try:
            file_bytes = await export_result(result_id, file_format)
            file = BufferedInputFile(
                file_bytes,
                filename=f"namotai-{result_id[:8]}.{file_format}",
            )
            await message.answer_document(
                file,
                caption="Готово! Что дальше?",
                reply_markup=after_result_keyboard(),
            )
        except Exception as e:
            logger.exception("Ошибка экспорта")
            await message.answer(
                f"😔 Не удалось сформировать файл ({type(e).__name__})",
                reply_markup=after_result_keyboard(),
            )
        return

    # Доставка в чат
    summary = result.get("summary", "")
    questions = result.get("questions", [])
    include_summary = data.get("include_summary", True)
    include_answers = data.get("include_answers", True)

    if not summary and not questions:
        await message.answer(
            "⚠️ Не удалось сгенерировать результат. Попробуй другой материал.",
            reply_markup=after_result_keyboard(),
        )
        return

    if include_summary and summary:
        for chunk in split_message(format_summary(summary)):
            await message.answer(chunk)

    if questions:
        for chunk in split_message(format_questions_only(questions)):
            await message.answer(chunk)

        if include_answers and any(q.get("answer") for q in questions):
            for chunk in split_message(format_answers_only(questions)):
                await message.answer(chunk)

    await message.answer(
        "Что дальше?",
        reply_markup=after_result_keyboard(),
    )
