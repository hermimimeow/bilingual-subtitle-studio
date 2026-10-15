"""Render subtitles as SRT and plain text, and write them to disk."""

from __future__ import annotations

from pathlib import Path

from bilingual_subtitle_studio.models import SubtitleSegment


def format_srt_timestamp(seconds: float) -> str:
    """Format seconds as an SRT timestamp, such as 00:01:02,500.

    Raises:
        ValueError: If seconds is negative.
    """
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
    """Render segments as an SRT document.

    Args:
        segments: Subtitle segments to render.
        language_order: Languages to include in each block. None includes every language.

    Returns:
        SRT text with numbered blocks.
    """
    blocks: list[str] = []
    for output_index, segment in enumerate(segments, start=1):
        blocks.append(
            "\n".join(
                [
                    str(output_index),
                    (
                        f"{format_srt_timestamp(segment.start_seconds)} --> "
                        f"{format_srt_timestamp(segment.end_seconds)}"
                    ),
                    segment.render_text(language_order),
                ]
            )
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def render_plain_text(
    segments: list[SubtitleSegment] | tuple[SubtitleSegment, ...],
    language_order: tuple[str, ...] | None = None,
) -> str:
    """Render segments as readable text, with a timestamp header for each block.

    Args:
        segments: Subtitle segments to render.
        language_order: Languages to include in each block. None includes every language.

    Returns:
        Blocks separated by blank lines.
    """
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
    """Render segments as SRT and write them to a file.

    Args:
        path: Destination .srt file. Parent folders are created as needed.
        segments: Subtitle segments to render.
        language_order: Languages to include in each block. None includes every language.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_srt(segments, language_order), encoding="utf-8")


def write_plain_text(
    path: Path,
    segments: list[SubtitleSegment] | tuple[SubtitleSegment, ...],
    language_order: tuple[str, ...] | None = None,
) -> None:
    """Render segments as plain text and write them to a file.

    Args:
        path: Destination .txt file. Parent folders are created as needed.
        segments: Subtitle segments to render.
        language_order: Languages to include in each block. None includes every language.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_plain_text(segments, language_order), encoding="utf-8")
