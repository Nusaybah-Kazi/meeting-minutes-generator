import json
import re
import time
import sys
from pathlib import Path


from src.ingest import load_transcript
from src.minutes import generate_minutes

SAMPLES = Path("samples")
OUT = Path("eval_outputs")
OUT.mkdir(exist_ok=True)

# Expectations are written by hand from reading each transcript.
LONG = {
    "file": "long_planning.txt",
    "actions": (6, 8),
    "decisions": (3, 6),
    "pairs": [
        ("job description", "Marcus"),
        ("interview", "Sunita"),
        ("roadmap", "Elena"),
        ("quote", "Marcus"),
        ("customer", "Tom"),
    ],
    "next": "6 November",
}

CASES = [
    {"file": "short_meeting.txt", "label": "default", "kwargs": {},
     "actions": (2, 2), "decisions": (1, 2),
     "pairs": [("palette", "Meera"), ("staging", "John")], "next": "21 October"},
    {"file": "messy_meeting.vtt", "label": "default", "kwargs": {},
     "actions": (1, 1), "pairs": [("test", "Rahul")]},
    {"file": "no_actions_meeting.txt", "label": "default", "kwargs": {},
     "actions": (0, 0), "decisions": (0, 0)},
    {"file": "unlabelled_meeting.txt", "label": "default", "kwargs": {},
     "actions": (2, 3), "pairs": [("release notes", "Sam"), ("email", "Dana")]},
    {"file": "product_review.txt", "label": "default", "kwargs": {},
     "actions": (3, 4), "decisions": (1, 3),
     "pairs": [("caching", "Kabir"), ("article", "Arjun"), ("dark mode", "Leela")],
     "next": "2 November"},
    {**LONG, "label": "single call", "kwargs": {}},
    {**LONG, "label": "map-reduce (1200 chars)", "kwargs": {"max_chars": 1200}},
]


def words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))

STOP = {"the", "a", "an", "to", "of", "and", "in", "on", "for", "by", "will", "be",
        "is", "at", "that", "with", "this", "it", "as", "are", "was"}


def content_words(text):
    return words(text) - STOP

def evaluate(m, transcript, exp):
    """Return a list of (level, message). FAIL = likely hallucination or hard error."""
    issues = []
    tw = words(transcript)

    if not m.summary.strip():
        issues.append(("FAIL", "summary is empty"))

    for name in m.attendees:
        if not words(name) <= tw:
            issues.append(("FAIL", f"attendee not found in transcript: {name}"))

    for a in m.action_items:
        if a.owner and not words(a.owner) <= tw:
            issues.append(("FAIL", f"owner not in transcript: {a.owner} (task: {a.task})"))
        if a.due and not words(a.due) <= tw:
            issues.append(("FAIL", f"due wording not in transcript: '{a.due}' (task: {a.task})"))

    for key, items in (("actions", m.action_items), ("decisions", m.decisions)):
        if key in exp:
            lo, hi = exp[key]
            if not lo <= len(items) <= hi:
                issues.append(("WARN", f"{len(items)} {key}, expected {lo}-{hi}"))

    for keyword, owner in exp.get("pairs", []):
        found = [a for a in m.action_items if keyword in a.task.lower()]
        if not found:
            issues.append(("WARN", f"no action item mentioning '{keyword}' (expected owner {owner})"))
        elif not any((a.owner or "").lower() == owner.lower() for a in found):
            got = ", ".join(str(a.owner) for a in found)
            issues.append(("FAIL", f"'{keyword}' owner should be {owner}, got: {got}"))

    if "next" in exp and exp["next"].lower() not in (m.next_meeting or "").lower():
        issues.append(("WARN", f"next_meeting is '{m.next_meeting}', expected '{exp['next']}'"))

    for a in m.action_items:
        aw = content_words(a.task)
        for d in m.decisions:
            dw = content_words(d)
            if aw and dw and len(aw & dw) / min(len(aw), len(dw)) >= 0.6:
                issues.append(("WARN", f"action item also in decisions: '{a.task}' ~ '{d}'"))
                break
        owners = {a.owner.lower() for a in m.action_items if a.owner}
    for d in m.decisions:
        first_word = d.split()[0].lower() if d.split() else ""
        if first_word in owners and re.match(r"\w+ will\b", d, re.IGNORECASE):
            issues.append(("WARN", f"decision looks like a task: '{d}'"))
        if re.search(r"next (review |sync )?meeting|re-?convene|to be (made|decided)|decided on \d", d, re.IGNORECASE):
            issues.append(("WARN", f"scheduling in decisions: '{d}'"))
    return issues


def main():
    rows, details = [], []
    wanted = sys.argv[1:]
    selected = [c for c in CASES if not wanted or any(w in c["file"] for w in wanted)]
    for case in selected:
        path = SAMPLES / case["file"]
        transcript = load_transcript(path)
        name = f"{case['file']} [{case['label']}]"
        print(f"\n=== {name}")

        start = time.time()
        try:
            m = generate_minutes(transcript, **case["kwargs"])
            seconds = time.time() - start
            slug = re.sub(r"\W+", "_", case["label"]).strip("_")
            (OUT / f"{path.stem}__{slug}.json").write_text(
                m.model_dump_json(indent=2), encoding="utf-8"
            )
            issues = evaluate(m, transcript, case)
            n_actions, n_decisions = len(m.action_items), len(m.decisions)
        except Exception as e:  # keep going so one failure doesn't hide the others
            seconds = time.time() - start
            issues = [("FAIL", f"run crashed: {e}")]
            n_actions = n_decisions = "-"

        fails = sum(1 for lvl, _ in issues if lvl == "FAIL")
        warns = sum(1 for lvl, _ in issues if lvl == "WARN")
        print(f"  actions={n_actions} decisions={n_decisions} time={seconds:.1f}s "
              f"FAIL={fails} WARN={warns}")
        for lvl, msg in issues:
            print(f"  [{lvl}] {msg}")
        rows.append(f"| {case['file']} | {case['label']} | {seconds:.1f} | {n_actions} | "
                    f"{n_decisions} | {fails} | {warns} |")
        details.append((name, issues))
        time.sleep(3)  # be gentle with free-tier rate limits

    lines = [
        "# Evaluation results", "",
        "| Sample | Mode | Time (s) | Actions | Decisions | FAIL | WARN |",
        "|---|---|---|---|---|---|---|",
        *rows, "", "## Details", "",
    ]
    for name, issues in details:
        lines.append(f"**{name}**")
        lines += [f"- [{lvl}] {msg}" for lvl, msg in issues] or ["- all checks passed"]
        lines.append("")
    Path("eval_results.md").write_text("\n".join(lines), encoding="utf-8")
    print("\nWrote eval_results.md and eval_outputs/*.json")


if __name__ == "__main__":
    main()