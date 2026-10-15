import logging
import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from app.core.limits import ValidationError

logger = logging.getLogger(__name__)


def parse_txt(path: Path) -> str:
    """Читает txt в UTF-8."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Фолбэк на cp1251 — старая русская кодировка
        try:
            return path.read_text(encoding="cp1251")
        except Exception as e:
            raise ValidationError(f"Не удалось прочитать txt: {e}") from e


def parse_docx(path: Path) -> str:
    """Извлекает текст из docx."""
    try:
        doc = Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except Exception as e:
        raise ValidationError(f"Не удалось прочитать docx: {e}") from e


def parse_pdf(path: Path) -> str:
    """Извлекает текст из pdf."""
    try:
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                pages.append(text)
        if not pages:
            raise ValidationError(
                "PDF не содержит извлекаемого текста. Возможно, это скан — OCR не поддерживается."
            )
        return "\n\n".join(pages)
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Не удалось прочитать pdf: {e}") from e


PARSERS = {
    ".txt": parse_txt,
    ".docx": parse_docx,
    ".pdf": parse_pdf,
}


def parse_document(path: Path) -> str:
    """Определяет формат по расширению и парсит."""
    ext = path.suffix.lower()
    parser = PARSERS.get(ext)
    if parser is None:
        raise ValidationError(f"Формат {ext} не поддерживается")

    text = parser(path)
    return normalize_text(text)


def normalize_text(text: str) -> str:
    """Чистка текста: лишние пробелы, переносы, пустые строки."""
    # Множественные пробелы → один
    text = re.sub(r"[ \t]+", " ", text)
    # Множественные переносы → два
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Пробелы в начале/конце строк
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    # Пробелы в начале/конце всего текста
    return text.strip()


def chunk_text(text: str, max_chars: int = 4000) -> list[str]:
    """
    Разбивает текст на чанки по абзацам.
    Для длинных текстов (например, учебник).
    """
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para) + 2  # +2 на разделитель
        if current_len + para_len > max_chars and current:
            chunks.append("\n\n".join(current))
            current = []
            current_len = 0
        current.append(para)
        current_len += para_len

    if current:
        chunks.append("\n\n".join(current))

    return chunks
