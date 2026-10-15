import json
import re

from pydantic import ValidationError

from src import config
from src.entities import find_participants
from src.llm import chat
from src.schema import ChunkNotes, Minutes

_SPACE_RE = re.compile(r"[\u00a0\u1680\u2000-\u200b\u202f\u205f\u3000]")
_INVISIBLE_RE = re.compile(r"[\u200c\u200d\u2060\ufeff]")
_DASH_RE = re.compile(r"[\u2010\u2011\u2012]")


def normalize_text(value):
    """Replace odd Unicode spaces/dashes the model may emit with plain ones (recursive)."""
    if isinstance(value, str):
        value = _SPACE_RE.sub(" ", value)
        value = _INVISIBLE_RE.sub("", value)
        value = _DASH_RE.sub("-", value)
        return re.sub(r" {2,}", " ", value).strip()
    if isinstance(value, list):
        return [normalize_text(v) for v in value]
    if isinstance(value, dict):
        return {k: normalize_text(v) for k, v in value.items()}
    return value

SYSTEM = (
    "You are an expert meeting secretary. You turn raw meeting transcripts into "
    "accurate, concise, well-structured minutes."
)

RULES = """Rules:
- Use ONLY information stated in the transcript. Never invent facts, names, owners or dates.
- If an action item has no clearly stated owner, set owner to null. If no due date is stated, set due to null.
- Keep dates as spoken (e.g. "next Wednesday", "Friday"); do not convert them.
- Speaker labels may be missing (audio transcripts). Never guess who said what.
- The participants hint may contain errors; list only people who are actually in the meeting.
- Use neutral, professional, past-tense language. Be concise.
- decisions: only things the group explicitly agreed or chose. A task given to a person is an action item, not a decision. A topic postponed to a later meeting is an open question, not a decision.
- action_items: only concrete tasks someone was assigned or volunteered for. Never list "decide X later" as an action item.
- Put each item in exactly one section; do not repeat it across decisions, action_items and open_questions.
- A need or mention ("we still need X from Y") is not an action item unless someone was assigned the task or agreed to do it. Never infer an owner.
- Return ONLY a JSON object. No markdown, no commentary."""

CHUNK_TEMPLATE = """{
  "title": string or null (only if stated in this part),
  "date": string or null (only if stated in this part),
  "attendees": [string] (only people listed or clearly present in this part),
  "agenda": [string],
  "key_points": [string],
  "decisions": [string],
  "action_items": [{"task": string, "owner": string or null, "due": string or null}],
  "open_questions": [string],
  "next_meeting": string or null
}"""

MINUTES_TEMPLATE = """{
  "title": string,
  "date": string or null,
  "attendees": [string],
  "agenda": [string],
  "summary": string (3 to 5 sentences),
  "discussion_points": [string],
  "decisions": [string],
  "action_items": [{"task": string, "owner": string or null, "due": string or null}],
  "open_questions": [string],
  "next_meeting": string or null
}"""


def extract_json(text: str) -> dict:
    """Pull a JSON object out of a model reply, tolerating code fences and extra text."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("No JSON object found in reply")
    return json.loads(text[start : end + 1])


def call_json(prompt, model, schema, llm=chat, attempts=3):
    """Call the model, parse and validate JSON, and retry with feedback if invalid."""
    current = prompt
    last_err = None
    for _ in range(attempts):
        reply = llm(
            current,
            system=SYSTEM,
            model=model,
            temperature=0.1,
            max_tokens=4096,
            json_mode=True,
        )
        try:
            return schema.model_validate(normalize_text(extract_json(reply)))
        except (ValueError, ValidationError) as e:
            last_err = e
            current = (
                prompt
                + f"\n\nYour previous reply was invalid ({str(e)[:300]}). "
                "Return ONLY one valid JSON object that follows the template."
            )
    raise RuntimeError(f"Model did not return valid JSON after {attempts} attempts: {last_err}")


def _chunk_notes(chunk, idx, total, llm):
    prompt = f"""{RULES}

This is part {idx} of {total} of one meeting transcript. Extract notes from this part only.
Return JSON in exactly this shape:
{CHUNK_TEMPLATE}

TRANSCRIPT PART:
\"\"\"
{chunk}
\"\"\""""
    return call_json(prompt, config.FAST_MODEL, ChunkNotes, llm)


def _final_prompt(source, is_notes, title, date, people):
    context = []
    if title:
        context.append(f"Meeting title: {title}")
    if date:
        context.append(f"Meeting date: {date}")
    if people:
        context.append(f"Participants hint (may contain errors): {', '.join(people)}")
    context_block = "\n".join(context) or "No extra context provided."

    if is_notes:
        intro = (
            "Below are notes extracted from consecutive parts of one meeting. "
            "The parts overlap slightly, so merge and remove duplicates."
        )
        label = "NOTES (JSON)"
    else:
        intro = "Below is the full meeting transcript."
        label = "TRANSCRIPT"

    return f"""{RULES}

{intro}
Write the final meeting minutes as JSON in exactly this shape:
{MINUTES_TEMPLATE}

CONTEXT:
{context_block}

{label}:
\"\"\"
{source}
\"\"\""""


def generate_minutes(
    text,
    meeting_title=None,
    meeting_date=None,
    attendees=None,
    llm=chat,
    max_chars=6000,
    on_progress=None,
) -> Minutes:
    """Transcript text -> structured Minutes. Uses map-reduce when the text is long."""
    from src.preprocess import prepare_transcript

    def report(step, total, message):
        if on_progress:
            on_progress(step, total, message)

    prep = prepare_transcript(text, max_chars=max_chars)
    if not prep["chunks"]:
        raise ValueError("The transcript is empty.")
    chunks = prep["chunks"]
    people = attendees or find_participants(prep["clean_text"])
    total = len(chunks) + 1

    if len(chunks) == 1:
        source, is_notes = chunks[0], False
    else:
        notes = []
        for i, chunk in enumerate(chunks, 1):
            report(i, total, f"Reading part {i} of {len(chunks)}")
            notes.append(_chunk_notes(chunk, i, len(chunks), llm).model_dump())
        source, is_notes = json.dumps(notes, indent=1), True

    report(total, total, "Writing final minutes")
    prompt = _final_prompt(source, is_notes, meeting_title, meeting_date, people)
    minutes = call_json(prompt, config.LLM_MODEL, Minutes, llm)

    # User-provided values win over the model's guesses.
    if meeting_title:
        minutes.title = meeting_title
    if meeting_date:
        minutes.date = meeting_date
    if attendees:
        minutes.attendees = attendees
    if not minutes.title.strip():
        minutes.title = "Meeting Minutes"
    return minutes