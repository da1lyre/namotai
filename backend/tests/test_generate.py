VALID_TEXT = "Это тестовый текст для проверки эндпоинта. " * 10


def test_text_too_short(client):
    response = client.post(
        "/api/generate",
        data={
            "text": "коротко",
            "source_type": "text",
            "difficulty": "medium",
            "question_count": 5,
        },
    )
    assert response.status_code == 422
    assert "100" in response.json()["detail"]


def test_invalid_difficulty(client):
    response = client.post(
        "/api/generate",
        data={
            "text": VALID_TEXT,
            "source_type": "text",
            "difficulty": "impossible",
            "question_count": 5,
        },
    )
    assert response.status_code == 422


def test_invalid_source_type(client):
    response = client.post(
        "/api/generate",
        data={
            "text": VALID_TEXT,
            "source_type": "audio",
            "difficulty": "medium",
            "question_count": 5,
        },
    )
    assert response.status_code == 422


def test_question_count_too_low(client):
    response = client.post(
        "/api/generate",
        data={
            "text": VALID_TEXT,
            "source_type": "text",
            "difficulty": "medium",
            "question_count": 3,
        },
    )
    assert response.status_code == 422


def test_question_count_too_high(client):
    response = client.post(
        "/api/generate",
        data={
            "text": VALID_TEXT,
            "source_type": "text",
            "difficulty": "medium",
            "question_count": 20,
        },
    )
    assert response.status_code == 422


def test_video_without_file(client):
    response = client.post(
        "/api/generate",
        data={
            "source_type": "video",
            "difficulty": "medium",
            "question_count": 5,
        },
    )
    assert response.status_code == 422


def test_text_without_content(client):
    response = client.post(
        "/api/generate",
        data={
            "source_type": "text",
            "difficulty": "medium",
            "question_count": 5,
        },
    )
    assert response.status_code == 422

def test_invalid_video_extension(client):
    import io

    response = client.post(
        "/api/generate",
        files={"file": ("malware.exe", io.BytesIO(b"data"), "application/octet-stream")},
        data={
            "source_type": "video",
            "difficulty": "medium",
            "question_count": 5,
        },
    )
    assert response.status_code == 422
