from pathlib import Path

from src import config
from src.llm import get_client

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm", ".ogg", ".flac"}
MAX_BYTES = 25 * 1024 * 1024  # Groq free-tier upload limit


def transcribe_audio(path, language: str | None = None) -> str:
    """Transcribe an audio file with Groq Whisper and return the text."""
    path = Path(path)
    if path.suffix.lower() not in AUDIO_EXTS:
        raise ValueError(f"Unsupported audio type '{path.suffix}'.")
    size = path.stat().st_size
    if size > MAX_BYTES:
        raise ValueError(
            f"File is {size / 1024 / 1024:.1f} MB; the limit is 25 MB. "
            "Compress it (lower bitrate / mono) or split it."
        )

    kwargs = {"model": config.WHISPER_MODEL, "temperature": 0.0}
    if language:
        kwargs["language"] = language  # e.g. "en", "hi"

    with open(path, "rb") as f:
        result = get_client().audio.transcriptions.create(
            file=(path.name, f.read()), **kwargs
        )
    return result.text