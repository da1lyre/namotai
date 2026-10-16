import json

from app.services.exporter import export_json, export_markdown, export_pdf

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


def test_export_json():
    data = export_json(SAMPLE)
    parsed = json.loads(data)
    assert parsed["id"] == "test-uuid"
    assert len(parsed["questions"]) == 2


def test_export_markdown():
    data = export_markdown(SAMPLE).decode("utf-8")
    assert "# Namotai" in data
    assert "## Конспект" in data
    assert "Что такое тест?" in data
    assert "**Ответ:** A" in data


def test_export_pdf():
    data = export_pdf(SAMPLE)
    assert data.startswith(b"%PDF")
    assert len(data) > 1000