import pytest

from src.preprocess import (
    chunk_text,
    clean_text,
    get_speakers,
    parse_attendee_line,
    parse_turns,
)


def test_clean_removes_fillers_and_stutters():
    assert clean_text("Priya: Okay so, um, let's get started.") == "Priya: Okay so, let's get started."
    assert (
        clean_text("Rahul: Yeah so the, the API is basically done, uh, just testing left.")
        == "Rahul: Yeah so the API is basically done, just testing left."
    )


def test_clean_removes_timestamps_but_keeps_meeting_times():
    assert clean_text("[00:01:23] Priya: hi") == "Priya: hi"
    assert clean_text("00:01:23 Priya: hi") == "Priya: hi"
    assert clean_text("Meeting at 10:30 AM") == "Meeting at 10:30 AM"


def test_parse_turns_and_speakers():
    text = "Project Sync - 14 October 2026\nAttendees: Priya, Rahul\n\nPriya: Hello\nRahul: Hi there"
    turns = parse_turns(text)
    assert turns[0].speaker is None
    assert get_speakers(turns) == ["Priya", "Rahul"]


def test_continuation_lines_join_previous_speaker():
    turns = parse_turns("Priya: first\nsecond line\nRahul: ok")
    assert turns[0].text == "first second line"
    assert turns[1].speaker == "Rahul"


def test_parse_attendee_line():
    assert parse_attendee_line("Attendees: Priya, Rahul and Meera") == ["Priya", "Rahul", "Meera"]
    assert parse_attendee_line("no attendees here") == []


def test_chunking_with_overlap():
    text = "\n".join(f"line {i:03d} " + "x" * 90 for i in range(50))
    chunks = chunk_text(text, max_chars=1000, overlap_chars=200)
    assert len(chunks) > 1
    assert all(len(c) <= 1000 for c in chunks)
    assert chunks[0].splitlines()[-1] in chunks[1].splitlines()


def test_short_text_is_one_chunk():
    assert chunk_text("hello\nworld") == ["hello\nworld"]


def test_long_single_line_is_split():
    text = ("word. " * 1000).strip()
    chunks = chunk_text(text, max_chars=1000, overlap_chars=200)
    assert len(chunks) > 1
    assert all(len(c) <= 1000 for c in chunks)


def test_bad_overlap_raises():
    with pytest.raises(ValueError):
        chunk_text("x", max_chars=100, overlap_chars=100)

def test_prepare_transcript_clamps_overlap_for_small_chunks():
    from src.preprocess import prepare_transcript

    text = "\n".join(f"Priya: spoken line {i} " + "word " * 10 for i in range(20))
    prep = prepare_transcript(text, max_chars=300)  # default overlap would be too big
    assert len(prep["chunks"]) > 1