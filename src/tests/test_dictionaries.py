import json
import re
from pathlib import Path

DICTS = Path(__file__).resolve().parents[1] / "web" / "lib" / "dictionaries"


def _load(lang: str) -> dict[str, str]:
    return json.loads((DICTS / f"{lang}.json").read_text(encoding="utf-8"))


def _placeholders(text: str) -> list[str]:
    return sorted(re.findall(r"\{(\w+)\}", text))


def test_english_covers_every_arabic_key():
    ar, en = _load("ar"), _load("en")
    assert sorted(set(ar) - set(en)) == []
    assert sorted(set(en) - set(ar)) == []


def test_english_has_no_empty_values():
    assert [k for k, v in _load("en").items() if not v.strip()] == []


def test_placeholders_match_between_languages():
    ar, en = _load("ar"), _load("en")
    assert {k: _placeholders(v) for k, v in ar.items()} == {k: _placeholders(en.get(k, "")) for k in ar}
