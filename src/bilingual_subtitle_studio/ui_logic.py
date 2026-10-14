"""Pure helpers for the Streamlit UI.

Nothing here imports Streamlit, so these functions can be tested directly."""

from __future__ import annotations

from pathlib import Path

from bilingual_subtitle_studio.languages import SUPPORTED_LANGUAGES
from bilingual_subtitle_studio.models import (
    SubtitleLine,
    SubtitleLineRole,
    SubtitleSegment,
    SubtitleStatus,
    ToneMode,
)


def _calculate_progress(
    rows: list[dict[str, object]],
    subtitle_source: str,
    prepared_audio_path: str,
    export_complete: bool,
    output_mode: str = "Original + Translation",
) -> dict[str, int]:
    is_user_project = subtitle_source != "demo"
    try:
        segments = _rows_to_segments(rows) if is_user_project else ()
    except ValueError:
        segments = ()

    total_rows = len(segments)
    translation_rows = sum(1 for segment in segments if segment.translated_text.strip())
    if _output_mode_uses_translation(output_mode):
        reviewed_rows = sum(
            1
            for segment in segments
            if segment.translated_text.strip() and segment.status != SubtitleStatus.NEEDS_REVIEW
        )
        translate_percent = _percent(translation_rows, total_rows)
        review_percent = _percent(reviewed_rows, total_rows)
    else:
        translate_percent = 100 if total_rows else 0
        review_percent = 100 if total_rows else 0

    return {
        "Import": 100 if prepared_audio_path else 0,
        "Transcribe": 100 if total_rows else 0,
        "Translate": translate_percent,
        "Review": review_percent,
        "Export": 100 if export_complete else 0,
    }


def _current_task(progress: dict[str, int]) -> tuple[str, str]:
    if progress["Import"] < 100:
        return "Import media", "Upload audio or video to begin."
    if progress["Transcribe"] < 100:
        return "Transcribe", "Run Whisper to create subtitle rows."
    if progress["Translate"] < 100:
        return "Translate", "Run Gemini to fill translation rows."
    if progress["Review"] < 100:
        return "Review", "Check rows marked needs_review."
    if progress["Export"] < 100:
        return "Export", "Download or write files locally."
    return "Complete", "Files are ready."


def _operation_is_active(status: str) -> bool:
    return status in {"running", "stopping"}


def _start_operation(session_state: object) -> None:
    session_state.operation_status = "running"
    session_state.operation_running = True
    session_state.operation_cancel_requested = False


def _finish_operation(session_state: object, status: str, summary: str) -> None:
    session_state.operation_status = status
    session_state.operation_running = False
    session_state.operation_cancel_requested = False
    session_state.last_operation_summary = summary


def _reset_operation_state(session_state: object) -> None:
    session_state.operation_status = "idle"
    session_state.operation_running = False
    session_state.operation_cancel_requested = False
    session_state.last_operation_summary = "Ready"


def _percent(part: int, total: int) -> int:
    if total <= 0:
        return 0
    return round((part / total) * 100)


def _estimate_eta(elapsed_seconds: float, completed: int, total: int) -> float:
    if completed <= 0 or total <= completed:
        return 0.0
    seconds_per_item = elapsed_seconds / completed
    return seconds_per_item * (total - completed)


def _format_duration(seconds: float) -> str:
    rounded_seconds = max(round(seconds), 0)
    minutes, seconds_part = divmod(rounded_seconds, 60)
    hours, minutes_part = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes_part}m {seconds_part}s"
    if minutes_part:
        return f"{minutes_part}m {seconds_part}s"
    return f"{seconds_part}s"


def _segments_to_rows(segments: tuple[SubtitleSegment, ...]) -> list[dict[str, object]]:
    return [
        {
            "index": segment.index,
            "start_seconds": segment.start_seconds,
            "end_seconds": segment.end_seconds,
            "source_text": segment.source_text,
            "translated_text": segment.translated_text,
            "status": segment.status.value,
        }
        for segment in segments
    ]


def _mark_all_reviewed(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    reviewed_rows: list[dict[str, object]] = []
    for row in rows:
        reviewed_row = dict(row)
        if reviewed_row.get("source_text") or reviewed_row.get("translated_text"):
            reviewed_row["status"] = SubtitleStatus.EDITED.value
        reviewed_rows.append(reviewed_row)
    return reviewed_rows


def _download_payload(
    download_format: str,
    srt_text: str,
    plain_text: str,
    fcpxml_text: str,
) -> tuple[str, str, str]:
    if download_format == "TXT":
        return plain_text, "subtitles.txt", "text/plain"
    if download_format == "FCPXML":
        return fcpxml_text, "subtitles.fcpxml", "application/xml"
    return srt_text, "subtitles.srt", "text/plain"


def _save_uploaded_file(uploaded_file: object, upload_dir: Path) -> Path:
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_name = _safe_file_name(getattr(uploaded_file, "name", "upload"))
    uploaded_path = upload_dir / file_name
    uploaded_path.write_bytes(uploaded_file.getbuffer())
    return uploaded_path


def _read_log_tail(path: Path, max_lines: int = 80) -> str:
    if not path.exists():
        return "No logs yet. Actions will appear here after upload, extraction, transcription, or export."

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-max_lines:]) or "Log file is empty."


def _safe_file_name(file_name: str) -> str:
    safe_name = Path(file_name).name.strip().replace(" ", "_")
    return "".join(character for character in safe_name if character.isalnum() or character in "._-")


def _tone_mode_from_label(label: str) -> ToneMode:
    return {
        "Literal": ToneMode.LITERAL,
        "Natural": ToneMode.NATURAL,
        "Funny Vlog": ToneMode.FUNNY_VLOG,
        "Cinematic": ToneMode.CINEMATIC,
        "Short-Form": ToneMode.SHORT_FORM,
        "Xiaohongshu": ToneMode.XIAOHONGSHU,
    }[label]


def _target_language_index(target_language_code: str) -> int:
    language_codes = [language.code for language in SUPPORTED_LANGUAGES if language.code != "auto"]
    try:
        return language_codes.index(target_language_code)
    except ValueError:
        return language_codes.index("en")


def _output_mode_index(output_mode: str) -> int:
    output_modes = ["Original + Translation", "Original only", "Translation only"]
    try:
        return output_modes.index(output_mode)
    except ValueError:
        return 0


def _output_mode_uses_translation(output_mode: str) -> bool:
    return output_mode in {"Original + Translation", "Translation only"}


def _language_order_for_output_mode(
    output_mode: str,
    target_language_code: str,
) -> tuple[str, ...]:
    if output_mode == "Original only":
        return ("source",)
    if output_mode == "Translation only":
        return (target_language_code,)
    return ("source", target_language_code)


def _subtitle_status_from_value(value: object) -> SubtitleStatus:
    try:
        return SubtitleStatus(str(value or SubtitleStatus.AI_DRAFT.value))
    except ValueError:
        return SubtitleStatus.NEEDS_REVIEW


def _is_export_ready(
    segments: tuple[SubtitleSegment, ...],
    output_mode: str = "Original + Translation",
) -> bool:
    if not segments:
        return False
    if not _output_mode_uses_translation(output_mode):
        return any(segment.source_text.strip() for segment in segments)
    return any(segment.translated_text.strip() for segment in segments)


def _rows_to_segments(
    rows: list[dict[str, object]],
    target_language_code: str = "en",
) -> tuple[SubtitleSegment, ...]:
    segments: list[SubtitleSegment] = []
    for fallback_index, row in enumerate(rows, start=1):
        if not row.get("source_text") and not row.get("translated_text"):
            continue

        index = int(row.get("index") or fallback_index)
        start_seconds = float(row.get("start_seconds") or 0)
        end_seconds = float(row.get("end_seconds") or 0)
        source_text = str(row.get("source_text") or "").strip()
        translated_text = str(row.get("translated_text") or "").strip()
        status = _subtitle_status_from_value(row.get("status"))
        lines = [
            SubtitleLine(language="source", text=source_text, role=SubtitleLineRole.SOURCE),
        ]
        if translated_text:
            lines.append(
                SubtitleLine(
                    language=target_language_code,
                    text=translated_text,
                    role=SubtitleLineRole.TRANSLATION,
                )
            )

        try:
            segments.append(
                SubtitleSegment(
                    index=index,
                    start_seconds=start_seconds,
                    end_seconds=end_seconds,
                    source_text=source_text,
                    translated_text=translated_text,
                    lines=tuple(lines),
                    status=status,
                )
            )
        except ValueError as error:
            raise ValueError(f"Row {fallback_index}: {error}") from error

    return tuple(segments)
