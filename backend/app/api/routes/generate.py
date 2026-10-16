import logging
import os
import shutil
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.limits import (
    ALLOWED_TEXT_EXT,
    ALLOWED_VIDEO_EXT,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    MAX_TEXT_LENGTH,
    MAX_VIDEO_DURATION_SEC,
    MIN_TEXT_LENGTH,
    ValidationError,
)
from app.db.models.result import Result
from app.db.session import get_db
from app.schemas.generate import GenerateResponse
from app.services.audio import extract_audio, get_duration
from app.services.generator import calculate_llm_cost, generate_questions
from app.services.parser import parse_document
from app.services.transcriber import calculate_whisper_cost, transcribe_audio
from app.services.validator import validate_questions

router = APIRouter()
logger = logging.getLogger(__name__)

MEDIA_ROOT = Path(os.getenv("MEDIA_DIR", "/tmp/namotai-media"))


@router.post("/api/generate", response_model=GenerateResponse, status_code=201)
async def generate(
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
    source_type: str = Form(...),
    difficulty: str = Form(...),
    question_count: int = Form(...),
    include_summary: bool = Form(True),
    include_answers: bool = Form(True),
    db: AsyncSession = Depends(get_db),
) -> GenerateResponse:
    # ─── Валидация параметров ──────────────────────────────
    if source_type not in {"video", "text"}:
        raise HTTPException(422, "source_type: video или text")
    if difficulty not in {"easy", "medium", "hard"}:
        raise HTTPException(422, "difficulty: easy, medium или hard")
    if not 5 <= question_count <= 10:
        raise HTTPException(422, "question_count: от 5 до 10")

    if source_type == "video" and not file:
        raise HTTPException(422, "Для video нужен файл")
    if source_type == "text" and not text and not file:
        raise HTTPException(422, "Для text нужен текст или файл")

    task_id = uuid4()
    task_dir = MEDIA_ROOT / str(task_id)
    task_dir.mkdir(parents=True, exist_ok=True)

    audio_duration: int | None = None
    source_text: str | None = None
    transcript: dict | None = None

    try:
        # ─── Видео ──────────────────────────────────────────
        if source_type == "video" and file:
            ext = Path(file.filename or "").suffix.lower()
            if ext not in ALLOWED_VIDEO_EXT:
                raise ValidationError(
                    f"Формат {ext} не поддерживается. "
                    f"Допустимо: {', '.join(sorted(ALLOWED_VIDEO_EXT))}"
                )

            content = await file.read()
            if len(content) > MAX_FILE_SIZE_BYTES:
                raise ValidationError(
                    f"Файл больше {MAX_FILE_SIZE_MB} МБ",
                    status_code=413,
                )

            file_path = task_dir / f"source{ext}"
            file_path.write_bytes(content)

            duration = await get_duration(file_path)
            if duration > MAX_VIDEO_DURATION_SEC:
                raise ValidationError(f"Видео длиннее {MAX_VIDEO_DURATION_SEC // 3600} часов")
            audio_duration = int(duration)

            # Извлечь аудио
            audio_path = task_dir / "audio.wav"
            await extract_audio(file_path, audio_path)

            # Транскрибировать
            logger.info("Task %s: транскрибирую аудио...", task_id)
            transcript = await transcribe_audio(audio_path)
            logger.info(
                "Task %s: транскрипт готов, %d сегментов",
                task_id,
                len(transcript["segments"]),
            )

        # ─── Текст ──────────────────────────────────────────
        elif source_type == "text":
            if text:
                source_text = text.strip()
            elif file:
                ext = Path(file.filename or "").suffix.lower()
                if ext not in ALLOWED_TEXT_EXT:
                    raise ValidationError(
                        f"Формат {ext} не поддерживается. "
                        f"Допустимо: {', '.join(sorted(ALLOWED_TEXT_EXT))}"
                    )

                content = await file.read()
                if len(content) > MAX_FILE_SIZE_BYTES:
                    raise ValidationError(
                        f"Файл больше {MAX_FILE_SIZE_MB} МБ",
                        status_code=413,
                    )

                file_path = task_dir / f"source{ext}"
                file_path.write_bytes(content)

                logger.info("Task %s: парсю документ %s", task_id, ext)
                source_text = parse_document(file_path)
                logger.info(
                    "Task %s: текст распарсен, %d символов",
                    task_id,
                    len(source_text),
                )

            if not source_text:
                raise ValidationError("Пустой текст")
            if len(source_text) < MIN_TEXT_LENGTH:
                raise ValidationError(f"Текст короче {MIN_TEXT_LENGTH} символов")
            if len(source_text) > MAX_TEXT_LENGTH:
                raise ValidationError(f"Текст длиннее {MAX_TEXT_LENGTH} символов")

        # ─── Генерация конспекта и вопросов через LLM ───────
        source_content = transcript["text"] if source_type == "video" else source_text
        if not source_content:
            raise ValidationError("Нет текста для генерации")

        logger.info("Task %s: генерирую вопросы через LLM...", task_id)
        llm_result = await generate_questions(
            text=source_content,
            difficulty=difficulty,
            question_count=question_count,
            source_type=source_type,
            include_summary=include_summary,
            include_answers=include_answers,
        )

        questions = validate_questions(
            llm_result["questions"],
            expected_count=question_count,
            include_answers=include_answers,
        )

        if not questions:
            raise ValidationError("LLM не смог сгенерировать вопросы")

        # ─── Стоимость ──────────────────────────────────────
        cost_whisper = calculate_whisper_cost(audio_duration) if audio_duration else Decimal("0")
        cost_llm = calculate_llm_cost(
            llm_result["tokens_input"],
            llm_result["tokens_output"],
        )
        cost_total = cost_whisper + cost_llm

        logger.info(
            "Task %s: готово, %d вопросов, токены %d/%d, стоимость %.2f ₽",
            task_id,
            len(questions),
            llm_result["tokens_input"],
            llm_result["tokens_output"],
            cost_total,
        )

        # ─── Сохранение в БД ────────────────────────────────
        result = Result(
            id=task_id,
            source_type=source_type,
            difficulty=difficulty,
            question_count=question_count,
            summary=llm_result["summary"] if include_summary else "",
            questions=questions,
            transcript=transcript,
            source_text=source_text,
            audio_duration_sec=audio_duration,
            cost_total=cost_total,
        )
        db.add(result)
        await db.commit()

        return GenerateResponse(
            id=str(task_id),
            summary=result.summary or "",
            questions=questions,
        )

    except ValidationError as e:
        raise HTTPException(e.status_code, e.message) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Ошибка обработки задачи %s", task_id)
        raise HTTPException(500, f"Внутренняя ошибка: {type(e).__name__}") from e
    finally:
        if task_dir.exists():
            shutil.rmtree(task_dir, ignore_errors=True)
