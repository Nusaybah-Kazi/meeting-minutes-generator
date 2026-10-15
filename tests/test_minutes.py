import json

import pytest

from src.minutes import call_json, extract_json, generate_minutes
from src.schema import Minutes

GOOD = {
    "title": "T",
    "summary": "s",
    "key_points": ["k"],
    "decisions": ["d"],
    "action_items": [{"task": "t", "owner": None, "due": None}],
    "open_questions": [],
}


def test_extract_json_handles_fences_and_extra_text():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Here you go: {"a": 1} Hope it helps') == {"a": 1}
    with pytest.raises(ValueError):
        extract_json("no json here")


def test_null_lists_become_empty():
    m = Minutes.model_validate({"attendees": None, "decisions": None, "date": None})
    assert m.attendees == [] and m.decisions == []


def test_call_json_retries_then_succeeds():
    replies = iter(["not json", json.dumps(GOOD)])
    calls = []

    def fake(prompt, **kwargs):
        calls.append(prompt)
        return next(replies)

    result = call_json("prompt", "model", Minutes, llm=fake)
    assert result.title == "T"
    assert len(calls) == 2
    assert "invalid" in calls[1]


def test_call_json_gives_up():
    with pytest.raises(RuntimeError):
        call_json("p", "m", Minutes, llm=lambda p, **k: "nope", attempts=2)


def test_short_transcript_uses_one_call_and_user_overrides():
    calls = []

    def fake(prompt, **kwargs):
        calls.append(prompt)
        return json.dumps(GOOD)

    m = generate_minutes(
        "Priya: hello\nRahul: hi",
        meeting_title="Sync",
        meeting_date="14 Oct 2026",
        attendees=["Priya", "Rahul"],
        llm=fake,
    )
    assert len(calls) == 1
    assert m.title == "Sync" and m.date == "14 Oct 2026"
    assert m.attendees == ["Priya", "Rahul"]


def test_long_transcript_uses_map_reduce():
    calls = []

    def fake(prompt, **kwargs):
        calls.append(prompt)
        return json.dumps(GOOD)

    text = "\n".join(f"Priya: this is spoken line number {i} " + "word " * 20 for i in range(30))
    m = generate_minutes(text, llm=fake, max_chars=500)
    assert len(calls) > 2  # several chunk calls + one final call
    assert "NOTES (JSON)" in calls[-1]
    assert m.action_items[0].task == "t"


def test_empty_transcript_raises():
    with pytest.raises(ValueError):
        generate_minutes("   ", llm=lambda p, **k: "{}")

def test_empty_title_falls_back():
    reply = json.dumps({**GOOD, "title": ""})
    m = generate_minutes("Priya: hello", llm=lambda p, **k: reply)
    assert m.title == "Meeting Minutes"

def test_normalize_text_replaces_odd_spaces():
    from src.minutes import normalize_text

    data = {"a": ["over\u202fbudget", "a\u00a010%"], "b": "x\u2011y"}
    assert normalize_text(data) == {"a": ["over budget", "a 10%"], "b": "x-y"}