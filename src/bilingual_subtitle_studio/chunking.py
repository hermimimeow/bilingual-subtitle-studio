from __future__ import annotations

from bilingual_subtitle_studio.models import SubtitleSegment


MAX_CHINESE_CHARS = 22
MAX_ENGLISH_CHARS = 46
MAX_DURATION_SECONDS = 5.0


def needs_review(segment: SubtitleSegment) -> bool:
    text_length = max(len(segment.source_text), len(segment.translated_text))
    max_chars = MAX_CHINESE_CHARS if _contains_cjk(segment.source_text) else MAX_ENGLISH_CHARS
    return segment.duration_seconds > MAX_DURATION_SECONDS or text_length > max_chars * 2


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= character <= "\u9fff" for character in text)
