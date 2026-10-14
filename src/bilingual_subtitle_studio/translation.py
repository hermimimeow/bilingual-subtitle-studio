from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace
from typing import Protocol

from bilingual_subtitle_studio.models import SubtitleSegment, SubtitleStatus, ToneMode
from bilingual_subtitle_studio.operations import OperationCancelled

_TRANSLATION_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "translations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "translated_text": {"type": "string"},
                    "needs_review": {"type": "boolean"},
                },
                "required": ["index", "translated_text", "needs_review"],
            },
        }
    },
    "required": ["translations"],
}


class TranslationEngine(Protocol):
    def translate(
        self,
        segments: tuple[SubtitleSegment, ...],
        target_language: str,
        tone: ToneMode,
        progress_callback: Callable[[int, int], None] | None = None,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> tuple[SubtitleSegment, ...]:
        """Return segments with translated_text populated while preserving timing."""


class PassthroughTranslationEngine:
    def translate(
        self,
        segments: tuple[SubtitleSegment, ...],
        target_language: str,
        tone: ToneMode,
        progress_callback: Callable[[int, int], None] | None = None,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> tuple[SubtitleSegment, ...]:
        return segments


class GeminiTranslationEngine:
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        api_key: str | None = None,
        batch_size: int = 25,
    ) -> None:
        self.model_name = model_name
        self.api_key = api_key
        self.batch_size = batch_size

    def translate(
        self,
        segments: tuple[SubtitleSegment, ...],
        target_language: str,
        tone: ToneMode,
        progress_callback: Callable[[int, int], None] | None = None,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> tuple[SubtitleSegment, ...]:
        if not segments:
            return segments

        try:
            from google import genai
        except ImportError as error:
            raise RuntimeError("google-genai is not installed. Run `uv sync` first.") from error

        client = genai.Client(api_key=self.api_key) if self.api_key else genai.Client()
        translated_batches: list[SubtitleSegment] = []
        batches = _batch_segments(segments, self.batch_size)
        for batch_index, batch in enumerate(batches, start=1):
            if cancel_requested is not None and cancel_requested():
                translated_batches.extend(_cancelled_segments(batch))
                for remaining_batch in batches[batch_index:]:
                    translated_batches.extend(_cancelled_segments(remaining_batch))
                raise OperationCancelled("Translation stopped by user.")

            translated_batches.extend(self._translate_batch(client, batch, target_language, tone))
            if progress_callback is not None:
                progress_callback(batch_index, len(batches))

        return tuple(translated_batches)

    def _translate_batch(
        self,
        client: object,
        segments: tuple[SubtitleSegment, ...],
        target_language: str,
        tone: ToneMode,
    ) -> tuple[SubtitleSegment, ...]:
        response = client.models.generate_content(
            model=self.model_name,
            contents=_build_translation_prompt(segments, target_language, tone),
            config={
                "temperature": 0.35,
                "response_mime_type": "application/json",
                "response_json_schema": _TRANSLATION_RESPONSE_SCHEMA,
            },
        )
        payload = response.parsed if response.parsed is not None else json.loads(response.text or "{}")
        return _apply_translation_payload(segments, payload)


def _build_translation_prompt(
    segments: tuple[SubtitleSegment, ...],
    target_language: str,
    tone: ToneMode,
) -> str:
    source_rows = [
        {
            "index": segment.index,
            "source_text": segment.source_text,
            "existing_translation": segment.translated_text,
        }
        for segment in segments
    ]
    return f"""
You are translating and rewriting subtitles for a bilingual creator video.

Target language: {target_language}
Tone mode: {tone.value}

Rules:
- Preserve each input index exactly.
- Return one translation for every input row.
- Translate/rewrite only the subtitle text; do not mention timestamps.
- Preserve meaning and avoid adding facts that are not in the source.
- Keep wording concise and subtitle-readable.
- Mark needs_review=true if the source text is ambiguous or mixed-language meaning is uncertain.
- For literal tone, prioritize accuracy over style.
- For natural tone, use smooth native phrasing.
- For funny_vlog tone, use casual creator phrasing without changing meaning.
- For cinematic tone, use polished minimal wording.
- For short_form tone, use punchy concise wording.
- For xiaohongshu tone, use friendly lifestyle-oriented wording.

Subtitle rows:
{json.dumps(source_rows, ensure_ascii=False, indent=2)}
""".strip()


def _apply_translation_payload(
    segments: tuple[SubtitleSegment, ...],
    payload: object,
) -> tuple[SubtitleSegment, ...]:
    if not isinstance(payload, dict):
        raise TypeError("Gemini returned an invalid translation payload.")

    translations = payload.get("translations")
    if not isinstance(translations, list):
        raise TypeError("Gemini response did not include a translations list.")

    by_index: dict[int, tuple[str, bool]] = {}
    for item in translations:
        if not isinstance(item, dict):
            continue
        try:
            index = int(item["index"])
        except (KeyError, TypeError, ValueError):
            continue
        translated_text = str(item.get("translated_text") or "").strip()
        needs_review = bool(item.get("needs_review")) or not translated_text
        by_index[index] = (translated_text, needs_review)

    translated_segments: list[SubtitleSegment] = []
    for segment in segments:
        translated_text, needs_review = by_index.get(segment.index, ("", True))
        translated_segments.append(
            replace(
                segment,
                translated_text=translated_text,
                status=SubtitleStatus.NEEDS_REVIEW if needs_review else SubtitleStatus.AI_DRAFT,
                lines=(),
            )
        )

    return tuple(translated_segments)


def _batch_segments(
    segments: tuple[SubtitleSegment, ...],
    batch_size: int,
) -> tuple[tuple[SubtitleSegment, ...], ...]:
    safe_batch_size = max(batch_size, 1)
    return tuple(
        segments[index : index + safe_batch_size]
        for index in range(0, len(segments), safe_batch_size)
    )


def _cancelled_segments(segments: tuple[SubtitleSegment, ...]) -> tuple[SubtitleSegment, ...]:
    return tuple(
        replace(segment, translated_text=segment.translated_text, status=SubtitleStatus.NEEDS_REVIEW)
        for segment in segments
    )
