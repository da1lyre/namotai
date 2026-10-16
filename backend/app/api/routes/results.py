import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.result import Result
from app.db.session import get_db
from app.schemas.generate import GenerateResponse
from app.services.exporter import export_markdown, export_pdf

router = APIRouter()
logger = logging.getLogger(__name__)


EXPORT_FORMATS = {
    "md": ("text/markdown", "md", export_markdown),
    "pdf": ("application/pdf", "pdf", export_pdf),
}


async def _get_result_or_404(result_id: UUID, db: AsyncSession) -> Result:
    stmt = select(Result).where(Result.id == result_id)
    result = (await db.execute(stmt)).scalar_one_or_none()
    if result is None:
        raise HTTPException(404, "Результат не найден")
    return result


@router.get("/api/results/{result_id}", response_model=GenerateResponse)
async def get_result(
    result_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> GenerateResponse:
    result = await _get_result_or_404(result_id, db)
    return GenerateResponse(
        id=str(result.id),
        summary=result.summary or "",
        questions=result.questions or [],
    )


@router.get("/api/results/{result_id}/export")
async def export_result(
    result_id: UUID,
    format: str = Query("md", pattern="^(md|pdf)$"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    result = await _get_result_or_404(result_id, db)

    mime, ext, exporter = EXPORT_FORMATS[format]

    data = {
        "id": str(result.id),
        "source_type": result.source_type,
        "difficulty": result.difficulty,
        "question_count": result.question_count,
        "summary": result.summary or "",
        "questions": result.questions or [],
        "created_at": result.created_at.isoformat() if result.created_at else None,
    }

    try:
        content = exporter(data)
    except Exception as e:
        logger.exception("Ошибка экспорта в %s", format)
        raise HTTPException(500, f"Ошибка экспорта: {type(e).__name__}") from e

    filename = f"namotai-{result.id}.{ext}"

    return Response(
        content=content,
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )