import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def export_markdown(result: dict) -> bytes:
    lines: list[str] = []

    lines.append("# Namotai — результат\n")
    lines.append(f"**ID:** `{result['id']}`\n")
    lines.append(f"**Тип:** {result['source_type']}")
    lines.append(f"**Сложность:** {result['difficulty']}")
    lines.append(f"**Вопросов:** {result['question_count']}\n")

    summary = result.get("summary", "").strip()
    if summary:
        lines.append("## Конспект\n")
        lines.append(summary + "\n")

    questions = result.get("questions") or []
    has_answers = any(q.get("answer") for q in questions)

    if questions:
        lines.append("## Вопросы\n")
        for i, q in enumerate(questions, 1):
            lines.append(f"### {i}. {q.get('question', '')}\n")
            options = q.get("options") or []
            for j, opt in enumerate(options):
                letter = chr(ord("A") + j)
                lines.append(f"- **{letter})** {opt}")
            lines.append("")

        if has_answers:
            lines.append("## Ответы\n")
            for i, q in enumerate(questions, 1):
                answer = q.get("answer")
                if not answer:
                    continue
                if isinstance(answer, list):
                    answer = ", ".join(str(a) for a in answer)
                lines.append(f"{i}. {answer}")
            lines.append("")

    return "\n".join(lines).encode("utf-8")


def export_pdf(result: dict) -> bytes:
    md_content = export_markdown(result).decode("utf-8")

    with tempfile.TemporaryDirectory() as tmpdir:
        md_path = Path(tmpdir) / "input.md"
        pdf_path = Path(tmpdir) / "output.pdf"

        md_path.write_text(md_content, encoding="utf-8")

        cmd = [
            "pandoc",
            str(md_path),
            "-o",
            str(pdf_path),
            "--pdf-engine=typst",
            "-V",
            "mainfont=DejaVu Sans",
            "-V",
            "lang=ru",
        ]

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if proc.returncode != 0:
            logger.error("Pandoc/Typst error: %s", proc.stderr[:500])
            raise RuntimeError(f"PDF generation failed: {proc.stderr[:200]}")

        return pdf_path.read_bytes()
