# Meeting Minutes Generator

Turn a meeting transcript or recording into structured minutes: summary, decisions,
action items with owners and due dates, and open questions. Edit the result, then
export to Markdown or Word.

**Live demo:** <add URL after deployment>

## How it works
1. **Input:** audio (Groq Whisper) or text/.docx/.vtt/.srt, or pasted text.
2. **Preprocessing:** clean filler words and timestamps, detect speakers, chunk long text.
3. **NLP hints:** spaCy extracts people, dates and organizations.
4. **Generation:** Groq `gpt-oss` models. Long meetings use map-reduce (notes per chunk, then merge).
5. **Validation:** JSON parsed and validated with Pydantic, with automatic retry.
6. **Review and export:** edit in the UI, download `.md` or `.docx`.

## Run locally
    uv venv --python 3.11
    .venv\Scripts\activate
    uv pip install -r requirements.txt
    copy .env.example .env      # then put your free Groq key in .env
    python -m streamlit run app.py

Get a free key (no card) at https://console.groq.com.

## Tests and evaluation
    python -m pytest -q         # unit tests, no API calls
    python evaluate.py          # runs 7 sample meetings, checks for hallucinated owners/dates

Latest results are in `eval_results.md`.

## Limitations
- Audio has no speaker labels, so owners are only assigned when the text makes them clear.
- The model occasionally restates an action item as a decision. Review before sharing.
- Free-tier limits: 25 MB audio files and Groq rate limits.
- Transcripts are sent to Groq's API for processing. Do not use confidential recordings.

## Stack
Python, Streamlit, Groq API, spaCy, Pydantic, python-docx, pytest.