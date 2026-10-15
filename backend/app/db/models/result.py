from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Result(Base):
    __tablename__ = "results"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_type: Mapped[str] = mapped_column(String(16))
    difficulty: Mapped[str] = mapped_column(String(16))
    question_count: Mapped[int] = mapped_column(Integer)

    summary: Mapped[str | None] = mapped_column(String, nullable=True)
    questions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    transcript: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    source_text: Mapped[str | None] = mapped_column(String, nullable=True)

    audio_duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_total: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
