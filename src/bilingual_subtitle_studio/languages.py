"""Supported languages and their display labels."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    """A language the app can transcribe or translate into.

    Attributes:
        code: Short language code, such as "en" or "zh".
        name: English name of the language.
        native_name: Name written in that language.
        max_chars_per_line: Suggested line length for subtitles.
        direction: Text direction, "ltr" or "rtl".
    """
    code: str
    name: str
    native_name: str
    max_chars_per_line: int
    direction: str = "ltr"

    @property
    def label(self) -> str:
        """Return a display label such as 'English (English)'."""
        return f"{self.name} ({self.native_name})"


SUPPORTED_LANGUAGES: tuple[Language, ...] = (
    Language("auto", "Auto Detect", "Auto", 42),
    Language("en", "English", "English", 46),
    Language("zh-Hans", "Simplified Chinese", "简体中文", 22),
    Language("zh-Hant", "Traditional Chinese", "繁體中文", 22),
    Language("yue", "Cantonese", "粵語", 22),
    Language("ja", "Japanese", "日本語", 24),
    Language("ko", "Korean", "한국어", 28),
    Language("es", "Spanish", "Español", 44),
    Language("fr", "French", "Français", 44),
    Language("de", "German", "Deutsch", 42),
    Language("pt", "Portuguese", "Português", 44),
    Language("it", "Italian", "Italiano", 44),
    Language("th", "Thai", "ไทย", 34),
    Language("vi", "Vietnamese", "Tiếng Việt", 38),
    Language("id", "Indonesian", "Bahasa Indonesia", 44),
    Language("ms", "Malay", "Bahasa Melayu", 44),
    Language("ar", "Arabic", "العربية", 36, "rtl"),
    Language("hi", "Hindi", "हिन्दी", 34),
)

LANGUAGE_BY_CODE = {language.code: language for language in SUPPORTED_LANGUAGES}
LANGUAGE_LABEL_TO_CODE = {language.label: language.code for language in SUPPORTED_LANGUAGES}


def language_label(code: str) -> str:
    """Return the display label for a language code, or the code itself if unknown."""
    language = LANGUAGE_BY_CODE.get(code)
    return language.label if language else code
