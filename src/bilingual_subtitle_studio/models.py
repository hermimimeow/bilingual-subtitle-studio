from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SubtitleStatus(str, Enum):
    AI_DRAFT = "ai_draft"
    EDITED = "edited"
    NEEDS_REVIEW = "needs_review"


class ToneMode(str, Enum):
    LITERAL = "literal"
    NATURAL = "natural"
    FUNNY_VLOG = "funny_vlog"
    CINEMATIC = "cinematic"
    SHORT_FORM = "short_form"
    XIAOHONGSHU = "xiaohongshu"


class OutputMode(str, Enum):
    ORIGINAL_ONLY = "original_only"
    TRANSLATED_ONLY = "translated_only"
    BILINGUAL = "bilingual"
    TRILINGUAL = "trilingual"


class SubtitleLineRole(str, Enum):
    SOURCE = "source"
    TRANSLATION = "translation"


@dataclass(frozen=True)
class SubtitleLine:
    language: str
    text: str
    role: SubtitleLineRole = SubtitleLineRole.TRANSLATION


@dataclass(frozen=True)
class SubtitleSegment:
    index: int
    start_seconds: float
    end_seconds: float
    source_text: str
    translated_text: str = ""
    lines: tuple[SubtitleLine, ...] = ()
    status: SubtitleStatus = SubtitleStatus.AI_DRAFT

    def __post_init__(self) -> None:
        if self.index < 1:
            raise ValueError("subtitle index must start at 1")
        if self.start_seconds < 0:
            raise ValueError("start_seconds cannot be negative")
        if self.end_seconds <= self.start_seconds:
            raise ValueError("end_seconds must be greater than start_seconds")
        if not self.lines:
            lines = [
                SubtitleLine(language="source", text=self.source_text, role=SubtitleLineRole.SOURCE)
            ]
            if self.translated_text:
                lines.append(SubtitleLine(language="en", text=self.translated_text))
            object.__setattr__(self, "lines", tuple(lines))

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds

    @property
    def bilingual_text(self) -> str:
        return self.render_text()

    def render_text(self, language_order: tuple[str, ...] | None = None) -> str:
        lines = self.lines
        if language_order is not None:
            ordered_lines: list[SubtitleLine] = []
            for language in language_order:
                ordered_lines.extend(line for line in lines if line.language == language)
            lines = tuple(ordered_lines)

        return "\n".join(line.text for line in lines if line.text.strip())


@dataclass(frozen=True)
class StylePreset:
    name: str
    font_family: str = "Helvetica Neue"
    source_font_size: int = 48
    translated_font_size: int = 34
    text_color: str = "#FFFFFF"
    outline_color: str = "#000000"
    position: str = "bottom_center"


@dataclass(frozen=True)
class SubtitleProject:
    name: str
    source_language: str = "auto"
    target_language: str = "en"
    output_mode: OutputMode = OutputMode.BILINGUAL
    output_languages: tuple[str, ...] = ("source", "en")
    tone: ToneMode = ToneMode.NATURAL
    style: StylePreset = field(default_factory=lambda: StylePreset(name="Clean YouTube"))
    segments: tuple[SubtitleSegment, ...] = ()
