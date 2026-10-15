# Meeting Minutes Generator: Progress Tracker

**Stack (all free, no card):** Python, Streamlit, Groq API (free tier), spaCy, python-docx, pytest, GitHub, Streamlit Community Cloud
**Workflow:** Claude gives steps -> I run them in VS Code -> push to GitHub -> validate with Claude -> tick the boxes below.

**Legend:** `[ ]` todo, `[x]` done

---

## Architecture (target)

```
Audio (.mp3/.wav/.m4a)  --> Groq Whisper --> transcript
Text/.txt/.docx/.vtt    --------------------> transcript
                                   |
                         Preprocessing (clean, speakers, chunk)
                                   |
                         spaCy NER (people, dates, orgs)
                                   |
                  Groq LLM (map: chunk notes -> reduce: final minutes JSON)
                                   |
                  Streamlit UI  -->  Export (Markdown / DOCX)
```

**Target folder layout**

```
meeting-minutes-generator/
├── app.py                  # Streamlit UI
├── src/
│   ├── __init__.py
│   ├── config.py           # env + constants
│   ├── llm.py              # Groq client wrapper
│   ├── transcribe.py       # audio -> text (Whisper on Groq)
│   ├── ingest.py           # file readers
│   ├── preprocess.py       # cleaning, speaker parsing, chunking
│   ├── entities.py         # spaCy NER
│   ├── minutes.py          # map-reduce minutes generation
│   └── export.py           # md / docx writers
├── tests/
├── samples/                # sample transcripts
├── .env                    # NEVER commit
├── .gitignore
├── requirements.txt
├── README.md
└── progress.md
```

---

##SETUP
uv venv --python 3.11
.venv\Scripts\activate
uv pip install -r requirements.txt
uv pip install pip
python -m spacy download en_core_web_sm

## Phase 0: Environment & Repo Setup ✅
- [x] Install Python 3.10+, Git, VS Code (using uv-managed Python 3.11)
- [x] Create GitHub repo `meeting-minutes-generator` (public, with README + Python .gitignore)
- [x] Clone it, open in VS Code
- [x] Create and activate virtual environment (uv, `.venv`)
- [x] Create Groq account (free, no card) and generate API key
- [x] Create `.env` with the key, confirm `.env` is git-ignored
- [x] Create folder structure + `requirements.txt`
- [x] Install dependencies, first commit and push

**Validation checkpoint:** share `git log --oneline`, `pip list` (short), and confirm `.env` is NOT in the repo.

---

## Phase 1: Groq Connectivity
- [ ] `src/config.py` loads `GROQ_API_KEY` via python-dotenv
- [ ] `src/llm.py` with a `chat()` helper (retry + error handling)
- [ ] Smoke test script prints a model response
- [ ] Check available model names in the Groq console and pin them in `config.py`

**Validation checkpoint:** share the smoke test output.

---

## Phase 2: Transcript Ingestion
- [ ] Add 2-3 sample transcripts in `samples/` (short, medium, messy)
- [ ] `ingest.py`: read `.txt`, `.docx`, `.vtt`/`.srt`
- [ ] `transcribe.py`: audio -> text with Groq Whisper (handle the 25 MB free-tier file limit)
- [ ] Unit tests for ingest

**Validation checkpoint:** `pytest` output + a sample transcript printed.

---

## Phase 3: NLP Preprocessing
- [ ] Clean text (filler words, timestamps, whitespace)
- [ ] Detect speaker labels (`Alice: ...`)
- [ ] Chunk long transcripts by tokens/characters with overlap
- [ ] spaCy NER: extract people, organizations, dates
- [ ] Unit tests for cleaning, chunking, entities

**Validation checkpoint:** show chunk counts and extracted entities for a sample.

---

## Phase 4: Minutes Generation (core)
- [ ] Design JSON schema: title, date, attendees, agenda, summary, discussion points, decisions, action items (owner, task, due), open questions
- [ ] Prompt for per-chunk notes (map step)
- [ ] Prompt to merge into final minutes (reduce step)
- [ ] Force/validate JSON output (parse + retry on failure)
- [ ] Pydantic validation of the result
- [ ] Tests with a mocked LLM

**Validation checkpoint:** share generated JSON for a sample transcript.

---

## Phase 5: Streamlit Frontend
- [ ] `app.py`: upload (audio/text) or paste transcript
- [ ] Sidebar: model choice, meeting title/date, language
- [ ] Progress spinner and error messages
- [ ] Render minutes in sections (summary, decisions, action items table)
- [ ] Editable output before export

**Validation checkpoint:** screenshot of the running app.

---

## Phase 6: Export
- [ ] Markdown export
- [ ] DOCX export with python-docx
- [ ] Download buttons in Streamlit

**Validation checkpoint:** share an exported file.

---

## Phase 7: Quality & Evaluation
- [ ] Test on 5+ varied transcripts (short, long, noisy, multi-speaker)
- [ ] Check for hallucinated action items or owners
- [ ] Prompt tuning notes recorded below
- [ ] Rate-limit handling (Groq free-tier limits)

**Validation checkpoint:** share a short evaluation table.

---

## Phase 8: Deploy & Docs
- [ ] README with setup, screenshots, usage
- [ ] Deploy on Streamlit Community Cloud (GitHub login, add `GROQ_API_KEY` in Secrets)
- [ ] Final repo cleanup, tag `v1.0`

**Validation checkpoint:** share the live app URL.

---

## Notes / Decisions Log
| Date | Note |
|------|------|
| 2026-10-15 | Switched from conda to uv for the environment (conda env had no pip, so installs fell back to system Python 3.9). Python 3.11 via `uv venv`. |
| 2026-10-15 | Always install with `uv pip install ...` or `python -m pip install ...`, never bare `pip`. |

## Issues / Blockers
| Date | Issue | Resolution |
|------|-------|------------|
|      |       |            |
| 2026-10-15 | spaCy install failed on Python 3.9 (thinc version not found) | Used Python 3.11 in a uv venv |