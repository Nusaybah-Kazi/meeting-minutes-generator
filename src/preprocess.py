import re
from dataclasses import dataclass

# --- Cleaning -------------------------------------------------------------

FILLER_RE = re.compile(r"\b(?:u+h+m*|u+m+|e+r+m+|h+m+)\b[,.]?[ \t]*", re.IGNORECASE)
REPEAT_RE = re.compile(r"\b(\w+)(?:,?\s+\1\b)+", re.IGNORECASE)  # "the, the" -> "the"
BRACKET_TS_RE = re.compile(r"\[\d{1,2}:\d{2}(?::\d{2})?\][ \t]*")
LINE_TS_RE = re.compile(r"^[ \t]*\d{1,2}:\d{2}:\d{2}[ \t]+", re.MULTILINE)


def clean_text(text: str) -> str:
    """Remove timestamps, filler words and stutters; normalise whitespace."""
    text = BRACKET_TS_RE.sub("", text)
    text = LINE_TS_RE.sub("", text)
    text = FILLER_RE.sub("", text)
    text = REPEAT_RE.sub(r"\1", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"[ \t]+([,.?!])", r"\1", text)
    text = re.sub(r",\s*,", ",", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# --- Speaker parsing -------------------------------------------------------

SPEAKER_RE = re.compile(r"^([A-Z][A-Za-z0-9 .'\-]{0,40}?):\s+(.+)$")
METADATA_KEYS = {
    "attendees", "attendee", "participants", "present", "absent", "apologies",
    "agenda", "date", "time", "location", "venue", "subject", "title", "topic",
    "meeting", "note", "notes", "decision", "decisions", "action", "summary",
}
ATTENDEE_RE = re.compile(
    r"^\s*(?:attendees?|participants?|present)\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE
)


@dataclass
class Turn:
    speaker: str | None
    text: str


def parse_turns(text: str) -> list[Turn]:
    """Split a transcript into speaker turns. Lines without a speaker get speaker=None."""
    turns: list[Turn] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = SPEAKER_RE.match(line)
        if m:
            speaker, spoken = m.group(1).strip(), m.group(2).strip()
            if speaker.lower() not in METADATA_KEYS and len(speaker.split()) <= 4:
                turns.append(Turn(speaker, spoken))
                continue
            turns.append(Turn(None, line))
        elif turns and turns[-1].speaker is not None:
            turns[-1].text += " " + line  # continuation of the previous speaker
        else:
            turns.append(Turn(None, line))
    return turns


def get_speakers(turns: list[Turn]) -> list[str]:
    seen: list[str] = []
    for t in turns:
        if t.speaker and t.speaker not in seen:
            seen.append(t.speaker)
    return seen


def parse_attendee_line(text: str) -> list[str]:
    """Read names from a line like 'Attendees: Priya, Rahul and Meera'."""
    m = ATTENDEE_RE.search(text)
    if not m:
        return []
    parts = re.split(r",|;|\band\b", m.group(1))
    return [p.strip() for p in parts if p.strip()]


# --- Chunking --------------------------------------------------------------

def _split_long_line(line: str, max_chars: int) -> list[str]:
    """Break one very long line (e.g. Whisper output) at sentence boundaries."""
    out: list[str] = []
    cur = ""
    for s in re.split(r"(?<=[.!?])\s+", line):
        while len(s) > max_chars:  # no punctuation at all: hard split
            if cur:
                out.append(cur)
                cur = ""
            out.append(s[:max_chars])
            s = s[max_chars:]
        if cur and len(cur) + 1 + len(s) > max_chars:
            out.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        out.append(cur)
    return out


def chunk_text(text: str, max_chars: int = 6000, overlap_chars: int = 300) -> list[str]:
    """Split text into chunks of about max_chars on line boundaries, with overlap."""
    if overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be smaller than max_chars")

    lines: list[str] = []
    for line in text.splitlines():
        if len(line) > max_chars:
            lines.extend(_split_long_line(line, max_chars))
        else:
            lines.append(line)

    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for line in lines:
        add = len(line) + 1
        if current and size + add > max_chars:
            chunks.append("\n".join(current))
            tail: list[str] = []
            tsize = 0
            for prev in reversed(current):  # carry the last few lines into the next chunk
                if tsize + len(prev) + 1 > overlap_chars:
                    break
                tail.insert(0, prev)
                tsize += len(prev) + 1
            current, size = tail, tsize
        current.append(line)
        size += add
    if current:
        chunks.append("\n".join(current))
    return [c.strip() for c in chunks if c.strip()]


# --- One-call pipeline -----------------------------------------------------

def prepare_transcript(text: str, max_chars: int = 6000, overlap_chars: int = 300) -> dict:
    cleaned = clean_text(text)
    turns = parse_turns(cleaned)
    return {
        "clean_text": cleaned,
        "turns": turns,
        "speakers": get_speakers(turns),
        "chunks": chunk_text(cleaned, max_chars, overlap_chars),
    }