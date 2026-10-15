from functools import lru_cache

import spacy

from src.preprocess import get_speakers, parse_attendee_line, parse_turns

LABELS = {
    "PERSON": "people",
    "ORG": "organizations",
    "DATE": "dates",
    "TIME": "times",
    "GPE": "places",
}


@lru_cache(maxsize=1)
def get_nlp():
    return spacy.load("en_core_web_sm")


def extract_entities(text: str) -> dict[str, list[str]]:
    """Run spaCy NER and group the entities we care about."""
    doc = get_nlp()(text)
    result = {name: [] for name in LABELS.values()}
    for ent in doc.ents:
        key = LABELS.get(ent.label_)
        name = ent.text.strip()
        if key and name and name not in result[key]:
            result[key].append(name)
    return result


def find_participants(text: str) -> list[str]:
    """Combine the Attendees line, speaker labels and spaCy PERSON entities (deduplicated)."""
    candidates = (
        parse_attendee_line(text)
        + get_speakers(parse_turns(text))
        + extract_entities(text)["people"]
    )
    seen: set[str] = set()
    people: list[str] = []
    for name in candidates:
        if name.lower() not in seen:
            seen.add(name.lower())
            people.append(name)
    return people