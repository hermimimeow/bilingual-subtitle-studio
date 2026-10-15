"""Speech-to-text engine interface and the local faster-whisper implementation."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from bilingual_subtitle_studio.models import SubtitleSegment
from bilingual_subtitle_studio.operations import OperationCancelled


class TranscriptionEngine(Protocol):
    """Interface for any engine that turns audio into timed subtitle segments."""
    def transcribe(self, audio_path: Path) -> tuple[SubtitleSegment, ...]:
        """Return timestamped subtitle segments from local audio."""


class NotConfiguredTranscriptionEngine:
    """Placeholder engine that raises until a real transcription engine is configured."""
    def transcribe(self, audio_path: Path) -> tuple[SubtitleSegment, ...]:
        """Raise, because no transcription engine is configured."""
        raise RuntimeError(
            "No transcription engine is configured yet. "
            "Add faster-whisper or whisper.cpp integration before running transcription."
        )


class FasterWhisperTranscriptionEngine:
    """Transcribe local audio on this machine with faster-whisper."""
    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        """Store the model settings used by transcribe().

        Args:
            model_size: Whisper model name, such as "base".
            device: Compute device, such as "cpu".
            compute_type: Quantization type, such as "int8".
        """
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
        """Transcribe an audio file into timed subtitle segments.

        Args:
            audio_path: Local audio file.
            language: Language code hint, or None to detect the language.
            vad_filter: Skip silent stretches before transcribing.
            progress_callback: Called with (seconds_done, total_seconds) after each segment.
            cancel_requested: Checked between segments. When it returns True, transcription stops.

        Returns:
            Non-empty segments, numbered from 1.

        Raises:
            FileNotFoundError: If the audio file does not exist.
            RuntimeError: If faster-whisper is not installed.
            OperationCancelled: If cancel_requested returns True.
        """
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
