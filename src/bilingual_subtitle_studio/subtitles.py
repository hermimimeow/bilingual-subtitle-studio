from __future__ import annotations

from pathlib import Path

from bilingual_subtitle_studio.models import SubtitleSegment


def format_srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        raise ValueError("SRT timestamp cannot be negative")

    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def render_srt(
    segments: list[SubtitleSegment] | tuple[SubtitleSegment, ...],
    language_order: tuple[str, ...] | None = None,
) -> str:
    blocks: list[str] = []
    for output_index, segment in enumerate(segments, start=1):
        blocks.append(
            "\n".join(
                [
                    str(output_index),
                    f"{format_srt_timestamp(segment.start_seconds)} --> "
                    f"{format_srt_timestamp(segment.end_seconds)}",
                    segment.render_text(language_order),
                ]
            )
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def render_plain_text(
    segments: list[SubtitleSegment] | tuple[SubtitleSegment, ...],
    language_order: tuple[str, ...] | None = None,
) -> str:
    lines: list[str] = []
    for segment in segments:
        lines.append(
            f"[{segment.start_seconds:06.2f} - {segment.end_seconds:06.2f}]\n"
            f"{segment.render_text(language_order)}"
        )
    return "\n\n".join(lines) + ("\n" if lines else "")


def write_srt(
    path: Path,
    segments: list[SubtitleSegment] | tuple[SubtitleSegment, ...],
    language_order: tuple[str, ...] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_srt(segments, language_order), encoding="utf-8")


def write_plain_text(
    path: Path,
    segments: list[SubtitleSegment] | tuple[SubtitleSegment, ...],
    language_order: tuple[str, ...] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_plain_text(segments, language_order), encoding="utf-8")
