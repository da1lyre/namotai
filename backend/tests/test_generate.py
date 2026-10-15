import pytest
from httpx import AsyncClient
from starlette.status import HTTP_201_CREATED, HTTP_422_UNPROCESSABLE_ENTITY

# --- Успешные сценарии ---

@pytest.mark.asyncio
async def test_generate_text_success(client: AsyncClient):
    """Успешная генерация из текста"""
    payload = {
        "text": "Это достаточный по длине текст для теста. " * 10,
        "source_type": "text",
        "difficulty": "medium",
        "question_count": "5"
    }

    response = await client.post("/api/generate", data=payload)

    assert response.status_code == HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["summary"] == "TODO: здесь будет конспект"
    assert data["questions"] == []


@pytest.mark.asyncio
async def test_generate_video_success_mocked(client: AsyncClient, tmp_path):
    """Успешная генерация из видео (с моком длительности)"""
    # Создаем фейковый видеофайл
    fake_video_path = tmp_path / "test.mp4"
    fake_video_path.write_bytes(b"fake video content")

    # Мокаем функцию получения длительности, чтобы не нужен был ffmpeg/реальный файл
    with patch('app.services.audio.get_duration', new_callable=lambda: AsyncMock(return_value=60)):
        with open(fake_video_path, "rb") as f:
            files = {"file": ("test.mp4", f, "video/mp4")}
            data = {
                "source_type": "video",
                "difficulty": "hard",
                "question_count": "8"
            }

            response = await client.post("/api/generate", data=data, files=files)

    assert response.status_code == HTTP_201_CREATED
    data = response.json()
    assert "id" in data


# --- Валидация параметров ---

@pytest.mark.asyncio
async def test_invalid_source_type(client: AsyncClient):
    """Ошибка при неверном source_type"""
    payload = {
        "text": "Some text",
        "source_type": "audio",  # Недопустимо
        "difficulty": "medium",
        "question_count": "5"
    }
    response = await client.post("/api/generate", data=payload)
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY
    assert "source_type" in response.text


@pytest.mark.asyncio
async def test_invalid_difficulty(client: AsyncClient):
    """Ошибка при неверной сложности"""
    payload = {
        "text": "Some text",
        "source_type": "text",
        "difficulty": "expert",  # Недопустимо
        "question_count": "5"
    }
    response = await client.post("/api/generate", data=payload)
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_question_count_out_of_range_low(client: AsyncClient):
    """Ошибка, если вопросов меньше 5"""
    payload = {
        "text": "Some text",
        "source_type": "text",
        "difficulty": "easy",
        "question_count": "2"
    }
    response = await client.post("/api/generate", data=payload)
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_question_count_out_of_range_high(client: AsyncClient):
    """Ошибка, если вопросов больше 10"""
    payload = {
        "text": "Some text",
        "source_type": "text",
        "difficulty": "easy",
        "question_count": "15"
    }
    response = await client.post("/api/generate", data=payload)
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY


# --- Валидация контента (Текст) ---

@pytest.mark.asyncio
async def test_missing_text_for_text_source(client: AsyncClient):
    """Ошибка, если source_type=text, но нет ни текста, ни файла"""
    payload = {
        "source_type": "text",
        "difficulty": "medium",
        "question_count": "5"
    }
    response = await client.post("/api/generate", data=payload)
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY
    assert "нужен текст или файл" in response.text


@pytest.mark.asyncio
async def test_text_too_short(client: AsyncClient):
    """Ошибка, если текст слишком короткий"""
    # Предполагаем MIN_TEXT_LENGTH > 5, например 100
    payload = {
        "text": "Short",
        "source_type": "text",
        "difficulty": "medium",
        "question_count": "5"
    }
    response = await client.post("/api/generate", data=payload)
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY
    assert "короче" in response.text.lower() or "Validation" in response.text


# --- Валидация контента (Видео/Файлы) ---

@pytest.mark.asyncio
async def test_missing_file_for_video_source(client: AsyncClient):
    """Ошибка, если source_type=video, но файл не прикреплен"""
    payload = {
        "source_type": "video",
        "difficulty": "medium",
        "question_count": "5"
    }
    response = await client.post("/api/generate", data=payload)
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY
    assert "нужен файл" in response.text


@pytest.mark.asyncio
async def test_unsupported_file_extension(client: AsyncClient, tmp_path):
    """Ошибка при загрузке файла с неподдерживаемым расширением"""
    fake_file_path = tmp_path / "test.exe"
    fake_file_path.write_bytes(b"fake content")

    with open(fake_file_path, "rb") as f:
        files = {"file": ("test.exe", f, "application/octet-stream")}
        data = {
            "source_type": "video",  # Пытаемся загрузить exe как видео
            "difficulty": "medium",
            "question_count": "5"
        }
        response = await client.post("/api/generate", data=data, files=files)

    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY
    assert "не поддерживается" in response.text


@pytest.mark.asyncio
async def test_text_file_upload_success(client: AsyncClient, tmp_path):
    """Успешная загрузка текста через файл (.txt)"""
    fake_txt_path = tmp_path / "notes.txt"
    long_text = "Valid text content. " * 20
    fake_txt_path.write_text(long_text)

    with open(fake_txt_path, "rb") as f:
        files = {"file": ("notes.txt", f, "text/plain")}
        data = {
            "source_type": "text",
            "difficulty": "easy",
            "question_count": "5"
        }
        response = await client.post("/api/generate", data=data, files=files)

    assert response.status_code == HTTP_201_CREATED
