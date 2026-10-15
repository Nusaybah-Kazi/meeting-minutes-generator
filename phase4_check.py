from src.ingest import load_transcript
from src.minutes import generate_minutes

AUDIO_TEXT = (
    " Project Sync 14 October 2026 Attendees Priya, Rahul, Meera, John Priya, let's start "
    "the website redesign. Where are we? Rahul, the wireframes are done. We still need "
    "the final color palette from Meera."
)
short = load_transcript("samples/short_meeting.txt")


def progress(step, total, message):
    print(f"  [{step}/{total}] {message}")


print("##### RUN 1: short meeting (single call)")
print(generate_minutes(short, on_progress=progress).model_dump_json(indent=2))

print("\n##### RUN 2: same meeting, forced map-reduce (small chunks)")
print(generate_minutes(short, max_chars=300, on_progress=progress).model_dump_json(indent=2))

print("\n##### RUN 3: audio text without speaker labels")
print(generate_minutes(AUDIO_TEXT, on_progress=progress).model_dump_json(indent=2))