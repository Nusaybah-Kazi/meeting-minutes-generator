import pytest
from docx import Document

from src.ingest import load_transcript


def test_load_txt(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("Priya: hello", encoding="utf-8")
    assert load_transcript(f) == "Priya: hello"


def test_load_vtt_strips_timestamps(tmp_path):
    f = tmp_path / "a.vtt"
    f.write_text(
        "WEBVTT\n\n1\n00:00:01.000 --> 00:00:05.000\nPriya: hi there\n",
        encoding="utf-8",
    )
    text = load_transcript(f)
    assert text == "Priya: hi there"
    assert "-->" not in text


def test_load_srt(tmp_path):
    f = tmp_path / "a.srt"
    f.write_text("1\n00:00:01,000 --> 00:00:03,000\nRahul: ok\n", encoding="utf-8")
    assert load_transcript(f) == "Rahul: ok"


def test_load_docx(tmp_path):
    f = tmp_path / "a.docx"
    doc = Document()
    doc.add_paragraph("Meera: palette by Friday")
    doc.save(str(f))
    assert "palette by Friday" in load_transcript(f)


def test_unsupported_type(tmp_path):
    f = tmp_path / "a.xyz"
    f.write_text("x")
    with pytest.raises(ValueError):
        load_transcript(f)