from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from bilingual_subtitle_studio.models import SubtitleSegment
from bilingual_subtitle_studio.operations import OperationCancelled


class TranscriptionEngine(Protocol):
    def transcribe(self, audio_path: Path) -> tuple[SubtitleSegment, ...]:
        """Return timestamped subtitle segments from local audio."""


class NotConfiguredTranscriptionEngine:
    def transcribe(self, audio_path: Path) -> tuple[SubtitleSegment, ...]:
        raise RuntimeError(
            "No transcription engine is configured yet. "
            "Add faster-whisper or whisper.cpp integration before running transcription."
        )


class FasterWhisperTranscriptionEngine:
    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type

    def transcribe(
        self,
        audio_path: Path,
        language: str | None = None,
        vad_filter: bool = True,
        progress_callback: Callable[[float, float | None], None] | None = None,
        cancel_requested: Callable[[], bool] | None = None,
    ) -> tuple[SubtitleSegment, ...]:
        if not audio_path.exists():
            raise FileNotFoundError(audio_path)

        try:
            from faster_whisper import WhisperModel
        except ImportError as error:
            raise RuntimeError(
                "faster-whisper is not installed. Run `uv sync` before transcribing."
            ) from error

        model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        whisper_segments, _info = model.transcribe(
            str(audio_path),
            language=language or None,
            vad_filter=vad_filter,
        )
        duration = float(getattr(_info, "duration", 0.0) or 0.0) or None

        segments: list[SubtitleSegment] = []
        for index, segment in enumerate(whisper_segments, start=1):
            if cancel_requested is not None and cancel_requested():
                raise OperationCancelled("Transcription stopped by user.")

            text = segment.text.strip()
            if not text:
                continue

            start_seconds = max(float(segment.start), 0.0)
            end_seconds = max(float(segment.end), start_seconds + 0.1)
            segments.append(
                SubtitleSegment(
                    index=index,
                    start_seconds=start_seconds,
                    end_seconds=end_seconds,
                    source_text=text,
                )
            )
            if progress_callback is not None:
                progress_callback(end_seconds, duration)

        return tuple(segments)
