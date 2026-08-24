"""Audio language extraction, ISO-639 normalization, and synonym matching."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LanguageEntry:
    """Canonical ISO-639 language specification and lookup aliases."""

    code_2: str | None  # e.g., "en", "ja", "fr"
    code_3: str  # e.g., "eng", "jpn", "fre"/"fra"
    name: str  # e.g., "English", "Japanese", "French"
    synonyms: tuple[str, ...] = ()


# Regex splitting common audio language delimiters: '/', ',', '+', '|', ';', '\'
LANGUAGE_DELIMITERS_REGEX = re.compile(r"[/,+\|;\\]+")


class LanguageNormalizer:
    """Canonical ISO-639 language resolver with bidirectional lookup."""

    def __init__(self) -> None:
        self._lookup: dict[str, LanguageEntry] = {}
        self._build_table()

    def _build_table(self) -> None:
        """Register ISO-639 standard mappings and common synonyms."""
        entries: list[LanguageEntry] = [
            LanguageEntry("en", "eng", "English", ("en-us", "en-gb")),
            LanguageEntry("ja", "jpn", "Japanese", ("jap", "nihongo")),
            LanguageEntry("fr", "fre", "French", ("fra", "francais")),
            LanguageEntry("de", "ger", "German", ("deu", "deutsch")),
            LanguageEntry("es", "spa", "Spanish", ("espanol", "castilian")),
            LanguageEntry("it", "ita", "Italian", ("italiano",)),
            LanguageEntry("ko", "kor", "Korean", ("korean",)),
            LanguageEntry("zh", "chi", "Chinese", ("zho", "mandarin", "cantonese")),
            LanguageEntry("ru", "rus", "Russian", ("russkiy",)),
            LanguageEntry("pt", "por", "Portuguese", ("portugues", "pt-br")),
            LanguageEntry("hi", "hin", "Hindi", ()),
            LanguageEntry("ar", "ara", "Arabic", ()),
            LanguageEntry(None, "und", "Undetermined", ("unknown", "undetermined")),
        ]
        for entry in entries:
            self._register_entry(entry)

    def _register_entry(self, entry: LanguageEntry) -> None:
        if entry.code_2:
            self._lookup[entry.code_2.lower()] = entry
        self._lookup[entry.code_3.lower()] = entry
        self._lookup[entry.name.lower()] = entry
        for syn in entry.synonyms:
            self._lookup[syn.lower()] = entry

    def extract_languages(self, raw_audio_languages: str | None) -> list[str]:
        """Extract, split, and normalize audio languages from mediaInfo string."""
        if not raw_audio_languages or not raw_audio_languages.strip():
            return []

        tokens = LANGUAGE_DELIMITERS_REGEX.split(raw_audio_languages.strip())
        results: list[str] = []
        seen: set[str] = set()

        for token in tokens:
            clean = token.strip().strip("[]()").lower()
            if not clean:
                continue
            entry = self._lookup.get(clean)
            canonical = entry.name if entry else token.strip().strip("[]()")
            if canonical.lower() not in seen:
                seen.add(canonical.lower())
                results.append(canonical)

        return results

    def matches(self, item_languages: list[str], target_query: str) -> bool:
        """Check if any item language matches the user query (by code or name)."""
        clean_target = target_query.strip().lower()
        if not clean_target:
            return False

        target_entry = self._lookup.get(clean_target)

        target_identifiers: set[str] = {clean_target}
        if target_entry:
            if target_entry.code_2:
                target_identifiers.add(target_entry.code_2.lower())
            target_identifiers.add(target_entry.code_3.lower())
            target_identifiers.add(target_entry.name.lower())
            target_identifiers.update(s.lower() for s in target_entry.synonyms)

        for lang in item_languages:
            clean_lang = lang.strip().lower()
            if clean_lang in target_identifiers:
                return True
            entry = self._lookup.get(clean_lang)
            if entry and (
                entry.name.lower() in target_identifiers
                or entry.code_3.lower() in target_identifiers
                or (entry.code_2 and entry.code_2.lower() in target_identifiers)
                or any(s.lower() in target_identifiers for s in entry.synonyms)
            ):
                return True

        return False

