import pytest

from app.services.exporter import export_markdown, export_pdf

SAMPLE = {
    "id": "test-uuid",
    "source_type": "text",
    "difficulty": "medium",
    "question_count": 2,
    "summary": "Это тестовый конспект.",
    "questions": [
        {
            "question": "Что такое тест?",
            "type": "single_choice",
            "options": ["A", "B", "C", "D"],
            "answer": "A",
        },
        {
            "question": "Как дела?",
            "type": "open",
            "answer": "Хорошо",
        },
    ],
}


SAMPLE_NO_ANSWERS = {
    "id": "test-uuid-2",
    "source_type": "text",
    "difficulty": "medium",
    "question_count": 2,
    "summary": "",
    "questions": [
        {
            "question": "Что такое тест?",
            "type": "single_choice",
            "options": ["A", "B", "C", "D"],
        },
        {
            "question": "Как дела?",
            "type": "open",
        },
    ],
}


def test_export_markdown():
    data = export_markdown(SAMPLE).decode("utf-8")
    assert "# Namotai" in data
    assert "## Конспект" in data
    assert "Что такое тест?" in data
    assert "## Ответы" in data
    assert "1. A" in data


def test_export_markdown_answers_in_end():
    """Ответы должны быть в конце, после всех вопросов."""
    data = export_markdown(SAMPLE).decode("utf-8")
    questions_pos = data.find("## Вопросы")
    answers_pos = data.find("## Ответы")
    assert questions_pos < answers_pos


def test_export_markdown_no_answers():
    """Если ответов нет — раздел «Ответы» не создаётся."""
    data = export_markdown(SAMPLE_NO_ANSWERS).decode("utf-8")
    assert "## Вопросы" in data
    assert "## Ответы" not in data


@pytest.mark.skip(reason="Requires pandoc and typst installed locally")
def test_export_pdf():
    data = export_pdf(SAMPLE)
    assert data.startswith(b"%PDF")
    assert len(data) > 1000
