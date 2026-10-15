import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from src.ingest import SUPPORTED_EXTS, load_transcript
from src.minutes import generate_minutes
from src.schema import ActionItem, Minutes
from src.transcribe import AUDIO_EXTS, transcribe_audio

st.set_page_config(page_title="Meeting Minutes Generator", page_icon="📝", layout="wide")
st.title("📝 Meeting Minutes Generator")
st.caption("Upload a transcript or audio file, or paste text. Review and edit the minutes before exporting.")

st.session_state.setdefault("transcript", None)
st.session_state.setdefault("minutes", None)
st.session_state.setdefault("edited", None)
st.session_state.setdefault("version", 0)

LANGUAGES = {"Auto-detect": None, "English": "en", "Hindi": "hi"}


def lines_to_list(text: str) -> list[str]:
    return [line.strip(" -•\t") for line in text.splitlines() if line.strip(" -•\t")]


def clean_cell(value) -> str:
    return "" if pd.isna(value) else str(value).strip()


def read_input(uploaded, pasted: str, language) -> str:
    """Uploaded file wins over pasted text. Audio goes to Whisper; other files are parsed."""
    if uploaded is None:
        return pasted.strip()
    suffix = Path(uploaded.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getbuffer())
        tmp_path = Path(tmp.name)
    try:
        if suffix in AUDIO_EXTS:
            return transcribe_audio(tmp_path, language=language)
        return load_transcript(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("Meeting details (optional)")
    meeting_title = st.text_input("Title")
    meeting_date = st.text_input("Date", placeholder="e.g. 14 October 2026")
    attendees_raw = st.text_area("Attendees (comma-separated)", placeholder="Priya, Rahul, Meera")
    language_label = st.selectbox("Audio language", list(LANGUAGES))
    st.caption("Anything you fill in here overrides what the AI finds in the transcript.")

# ---------------- Input ----------------
tab_upload, tab_paste = st.tabs(["Upload file", "Paste text"])
with tab_upload:
    uploaded = st.file_uploader(
        "Transcript (.txt .md .docx .vtt .srt) or audio (max 25 MB)",
        type=[e.lstrip(".") for e in sorted(SUPPORTED_EXTS | AUDIO_EXTS)],
    )
with tab_paste:
    pasted = st.text_area("Paste transcript", height=250)
st.caption("If you provide both, the uploaded file is used.")

if st.button("Generate minutes", type="primary"):
    if uploaded is None and not pasted.strip():
        st.warning("Upload a file or paste a transcript first.")
    else:
        try:
            with st.status("Working...", expanded=True) as status:
                st.write("Reading input")
                transcript = read_input(uploaded, pasted, LANGUAGES[language_label])
                if not transcript.strip():
                    raise ValueError("No text found in the input.")

                def progress(step, total, message):
                    st.write(f"{message} ({step}/{total})")

                attendees = [a.strip() for a in attendees_raw.split(",") if a.strip()] or None
                minutes = generate_minutes(
                    transcript,
                    meeting_title=meeting_title.strip() or None,
                    meeting_date=meeting_date.strip() or None,
                    attendees=attendees,
                    on_progress=progress,
                )
                status.update(label="Minutes ready", state="complete", expanded=False)
            st.session_state["transcript"] = transcript
            st.session_state["minutes"] = minutes
            st.session_state["version"] += 1  # new widget keys, so old edits don't linger
        except Exception as e:
            st.error(f"Something went wrong: {e}")

# ---------------- Review & edit ----------------
minutes = st.session_state["minutes"]
if minutes is not None:
    v = st.session_state["version"]
    st.divider()
    st.subheader("Review and edit")

    c1, c2 = st.columns(2)
    e_title = c1.text_input("Title", minutes.title, key=f"title_{v}")
    e_date = c2.text_input("Date", minutes.date or "", key=f"date_{v}")

    e_attendees = st.text_area("Attendees (one per line)", "\n".join(minutes.attendees), key=f"att_{v}")
    e_agenda = st.text_area("Agenda (one per line)", "\n".join(minutes.agenda), key=f"agenda_{v}")
    e_summary = st.text_area("Summary", minutes.summary, height=150, key=f"summary_{v}")
    e_discussion = st.text_area(
        "Discussion points (one per line)", "\n".join(minutes.discussion_points), height=150, key=f"disc_{v}"
    )
    e_decisions = st.text_area("Decisions (one per line)", "\n".join(minutes.decisions), key=f"dec_{v}")

    st.markdown("**Action items** (click a cell to edit; use the + row to add)")
    df = pd.DataFrame([a.model_dump() for a in minutes.action_items], columns=["task", "owner", "due"])
    edited_df = st.data_editor(df, num_rows="dynamic", key=f"actions_{v}")

    e_questions = st.text_area("Open questions (one per line)", "\n".join(minutes.open_questions), key=f"q_{v}")
    e_next = st.text_input("Next meeting", minutes.next_meeting or "", key=f"next_{v}")

    items = []
    for _, row in edited_df.iterrows():
        task = clean_cell(row["task"])
        if task:
            items.append(
                ActionItem(
                    task=task,
                    owner=clean_cell(row["owner"]) or None,
                    due=clean_cell(row["due"]) or None,
                )
            )

    st.session_state["edited"] = Minutes(
        title=e_title.strip() or "Meeting Minutes",
        date=e_date.strip() or None,
        attendees=lines_to_list(e_attendees),
        agenda=lines_to_list(e_agenda),
        summary=e_summary.strip(),
        discussion_points=lines_to_list(e_discussion),
        decisions=lines_to_list(e_decisions),
        action_items=items,
        open_questions=lines_to_list(e_questions),
        next_meeting=e_next.strip() or None,
    )

    with st.expander("Transcript used"):
        st.text_area("Transcript", st.session_state["transcript"], height=250, disabled=True,
                     label_visibility="collapsed")