from pathlib import Path

from docx import Document

TEXT_EXTS = {".txt", ".md"}
DOCX_EXTS = {".docx"}
SUBTITLE_EXTS = {".vtt", ".srt"}
SUPPORTED_EXTS = TEXT_EXTS | DOCX_EXTS | SUBTITLE_EXTS


def read_text_file(path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def read_docx(path) -> str:
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def read_subtitles(path) -> str:
    """Strip WEBVTT header, cue numbers and timestamps; keep spoken lines."""
    lines = []
    for line in read_text_file(path).splitlines():
        line = line.strip()
        if not line or line.upper().startswith(("WEBVTT", "NOTE")):
            continue
        if line.isdigit() or "-->" in line:
            continue
        lines.append(line)
    return "\n".join(lines)


def load_transcript(path) -> str:
    """Read a transcript file of any supported type and return plain text."""
    path = Path(path)
    ext = path.suffix.lower()
    if ext in TEXT_EXTS:
        return read_text_file(path)
    if ext in DOCX_EXTS:
        return read_docx(path)
    if ext in SUBTITLE_EXTS:
        return read_subtitles(path)
    raise ValueError(
        f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTS))}"
    )