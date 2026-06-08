from __future__ import annotations

from bilingual_subtitle_studio.models import SubtitleProject, SubtitleSegment


def demo_segments() -> tuple[SubtitleSegment, ...]:
    return (
        SubtitleSegment(
            index=1,
            start_seconds=1.2,
            end_seconds=3.8,
            source_text="我突然脑子一热报了个帆船课",
            translated_text="So I randomly signed up for a sailing class.",
        ),
        SubtitleSegment(
            index=2,
            start_seconds=4.1,
            end_seconds=6.6,
            source_text="唯一希望就是别掉进查尔斯河",
            translated_text="My only goal: don't fall into the Charles River.",
        ),
    )


def demo_project() -> SubtitleProject:
    return SubtitleProject(name="Demo Bilingual Subtitles", segments=demo_segments())
