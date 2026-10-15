from src.entities import extract_entities, find_participants


def test_extract_entities_finds_dates():
    ents = extract_entities("The team met Google on 14 October 2026.")
    assert any("2026" in d for d in ents["dates"])


def test_find_participants_merges_sources_without_duplicates():
    text = "Attendees: Priya, Rahul\nPriya: hi\nMeera: hello"
    people = find_participants(text)
    for name in ["Priya", "Rahul", "Meera"]:
        assert name in people
    assert len(people) == len({p.lower() for p in people})