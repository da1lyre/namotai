from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.states import GenerateFlow
from bot.keyboards import difficulty_keyboard, count_keyboard
from bot.api_client import generate_from_file, generate_from_text

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Привет! Я Namotai.\n\n"
        "Отправь мне видео или текст — я сделаю конспект и вопросы."
    )
    await state.set_state(GenerateFlow.waiting_for_source)


@router.message(GenerateFlow.waiting_for_source, F.video | F.document)
async def handle_file(message: Message, state: FSMContext) -> None:
    if message.video:
        file_id = message.video.file_id
        filename = "video.mp4"
    else:
        file_id = message.document.file_id
        filename = message.document.file_name or "file"

    await state.update_data(file_id=file_id, filename=filename, source_type="video")
    await state.set_state(GenerateFlow.waiting_for_difficulty)
    await message.answer("Выбери сложность:", reply_markup=difficulty_keyboard())


@router.message(GenerateFlow.waiting_for_source, F.text)
async def handle_text(message: Message, state: FSMContext) -> None:
    if not message.text or message.text.startswith("/"):
        return

    await state.update_data(text=message.text, source_type="text")
    await state.set_state(GenerateFlow.waiting_for_difficulty)
    await message.answer("Выбери сложность:", reply_markup=difficulty_keyboard())


@router.callback_query(GenerateFlow.waiting_for_difficulty, F.data.startswith("diff:"))
async def handle_difficulty(callback: CallbackQuery, state: FSMContext) -> None:
    difficulty = callback.data.split(":")[1]
    await state.update_data(difficulty=difficulty)
    await state.set_state(GenerateFlow.waiting_for_count)
    await callback.message.edit_text("Сколько вопросов?", reply_markup=count_keyboard())
    await callback.answer()


@router.callback_query(GenerateFlow.waiting_for_count, F.data.startswith("count:"))
async def handle_count(callback: CallbackQuery, state: FSMContext) -> None:
    count = int(callback.data.split(":")[1])
    data = await state.get_data()
    await callback.message.edit_text("Обрабатываю... Это может занять 1–3 минуты.")
    await callback.answer()

    try:
        if data["source_type"] == "text":
            result = await generate_from_text(
                text=data["text"],
                difficulty=data["difficulty"],
                question_count=count,
            )
        else:
            file = await callback.bot.get_file(data["file_id"])
            file_bytes = await callback.bot.download_file(file.file_path)
            result = await generate_from_file(
                file_bytes=file_bytes.read(),
                filename=data["filename"],
                difficulty=data["difficulty"],
                question_count=count,
            )

        await send_result(callback.message, result)
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")

    await state.clear()


async def send_result(message: Message, result: dict) -> None:
    summary = result.get("summary", "")
    questions = result.get("questions", [])

    text = f"📝 Конспект:\n{summary}\n\n❓ Вопросы:\n\n"
    for i, q in enumerate(questions, 1):
        text += f"{i}. {q['question']}\n"
        if q.get("options"):
            for opt in q["options"]:
                text += f"   • {opt}\n"
        text += f"   ✅ Ответ: {q['answer']}\n\n"

    # Telegram limit — 4096 символов
    for chunk in [text[i:i + 4000] for i in range(0, len(text), 4000)]:
        await message.answer(chunk)