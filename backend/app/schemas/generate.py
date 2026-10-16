from typing import Literal

from pydantic import BaseModel


SourceType = Literal["video", "text"]
Difficulty = Literal["easy", "medium", "hard"]
QuestionType = Literal["single_choice", "multiple_choice", "open"]


class Question(BaseModel):
    question: str
    type: QuestionType
    options: list[str] | None = None
    answer: str | list[str] | None = None
    source_ref: dict | None = None


class GenerateResponse(BaseModel):
    id: str
    summary: str
    questions: list[Question]