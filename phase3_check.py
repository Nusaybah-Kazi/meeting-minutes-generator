from src.entities import extract_entities, find_participants
from src.ingest import load_transcript
from src.preprocess import prepare_transcript

AUDIO_TEXT = (
    " Project Sync 14 October 2026 Attendees Priya, Rahul, Meera, John Priya, let's start "
    "the website redesign. Where are we? Rahul, the wireframes are done. We still need "
    "the final color palette from Meera."
)

samples = [
    ("short_meeting.txt", load_transcript("samples/short_meeting.txt")),
    ("messy_meeting.vtt", load_transcript("samples/messy_meeting.vtt")),
    ("audio text (no speaker labels)", AUDIO_TEXT),
]

for name, text in samples:
    prep = prepare_transcript(text, max_chars=300, overlap_chars=60)
    ents = extract_entities(prep["clean_text"])
    print(f"=== {name}")
    print("chars before/after cleaning:", len(text), "/", len(prep["clean_text"]))
    print("speakers:", prep["speakers"])
    print("chunks:", len(prep["chunks"]))
    print("participants:", find_participants(prep["clean_text"]))
    print("dates:", ents["dates"], "| people:", ents["people"])
    print()