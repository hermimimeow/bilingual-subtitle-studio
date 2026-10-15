"""Local web API for the subtitle workflow: uploads, background jobs, and exports.

The browser page in ``web/`` talks to these endpoints. Long-running work (transcription and
translation) runs in background threads, and the page polls ``/api/jobs/{id}`` for progress.
The server listens on 127.0.0.1 only, so files never leave the machine except the subtitle text
sent to Gemini.
"""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from bilingual_subtitle_studio.app_logging import get_logger
from bilingual_subtitle_studio.audio import extract_audio, is_supported_audio, is_supported_video
from bilingual_subtitle_studio.demo_data import demo_project
from bilingual_subtitle_studio.fcpxml import render_basic_fcpxml
from bilingual_subtitle_studio.languages import LANGUAGE_BY_CODE, SUPPORTED_LANGUAGES
from bilingual_subtitle_studio.models import SubtitleProject
from bilingual_subtitle_studio.operations import OperationCancelled
from bilingual_subtitle_studio.subtitles import render_plain_text, render_srt
from bilingual_subtitle_studio.transcription import FasterWhisperTranscriptionEngine
from bilingual_subtitle_studio.translation import GeminiTranslationEngine
from bilingual_subtitle_studio.ui_logic import (
    _calculate_progress,
    _current_step,
    _format_duration,
    _is_export_ready,
    _language_order_for_output_mode,
    _mark_all_reviewed,
    _rows_to_segments,
    _safe_file_name,
    _segments_to_rows,
    _tone_mode_from_label,
)

WEB_DIR = Path(__file__).parent / "web"
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs/ui")

TONES = ["Natural", "Literal", "Funny Vlog", "Cinematic", "Short-Form", "Xiaohongshu"]
OUTPUT_MODES = ["Original + Translation", "Original only", "Translation only"]
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large-v3"]
LANGUAGE_HINTS = ["auto", "zh", "en", "yue"]
COMPUTE_TYPES = ["int8", "float32", "default"]

logger = get_logger("bilingual_subtitle_studio.api")


@dataclass
class Job:
    """State of one background transcription or translation run."""

    id: str
    kind: str
    status: str = "running"  # running | done | stopped | failed
    done: float = 0
    total: float | None = None
    message: str = ""
    result: Any = None
    error: str | None = None
    cancel: threading.Event = field(default_factory=threading.Event)


class JobStore:
    """Keeps jobs in memory and runs each one in its own thread."""

    def __init__(self) -> None:
        """Create an empty job store."""
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def start(self, kind: str, work: Callable[[Job], Any]) -> Job:
        """Start ``work`` in a background thread and return its job.

        Args:
            kind: Short job name, such as "transcribe" or "translate".
            work: Function that receives the job, updates its progress, and returns the result.

        Returns:
            The job, which is still running when this returns.
        """
        job = Job(id=uuid.uuid4().hex, kind=kind)
        with self._lock:
            self._jobs[job.id] = job

        def run() -> None:
            try:
                job.result = work(job)
                job.status = "done"
            except OperationCancelled as error:
                job.status = "stopped"
                job.message = str(error)
            except Exception as error:  # Surfaced to the page; the traceback is logged.
                logger.exception("%s job failed", kind)
                job.status = "failed"
                job.error = str(error)

        threading.Thread(target=run, daemon=True).start()
        return job

    def get(self, job_id: str) -> Job | None:
        """Return the job with this id, or None if it does not exist."""
        with self._lock:
            return self._jobs.get(job_id)


jobs = JobStore()


class RowsRequest(BaseModel):
    """Subtitle rows as the page holds them."""

    rows: list[dict[str, Any]] = Field(default_factory=list)


class ProgressRequest(RowsRequest):
    """Rows plus the workflow state needed to compute step progress."""

    subtitle_source: str = "demo"
    prepared_audio_path: str = ""
    export_complete: bool = False
    output_mode: str = "Original + Translation"


class ExtractRequest(BaseModel):
    """Path of an uploaded video to extract audio from."""

    path: str


class TranscribeRequest(BaseModel):
    """Whisper settings and the prepared audio file."""

    path: str
    model_size: str = "base"
    language: str = "auto"
    compute_type: str = "int8"


class TranslateRequest(RowsRequest):
    """Rows to translate and the Gemini settings."""

    target_language: str = "en"
    tone: str = "Natural"
    model_name: str = "gemini-2.5-flash"
    api_key: str | None = None


class ExportRequest(RowsRequest):
    """Rows and output choices for SRT, TXT, and FCPXML."""

    output_mode: str = "Original + Translation"
    target_language: str = "en"
    save: bool = False


def create_app() -> FastAPI:
    """Build the FastAPI application with all routes mounted."""
    app = FastAPI(title="Bilingual Subtitle Studio")
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html")

    @app.get("/api/options")
    def options() -> dict[str, Any]:
        return {
            "languages": [
                {"code": language.code, "label": language.label}
                for language in SUPPORTED_LANGUAGES
                if language.code != "auto"
            ],
            "tones": TONES,
            "output_modes": OUTPUT_MODES,
            "whisper_models": WHISPER_MODELS,
            "language_hints": LANGUAGE_HINTS,
            "compute_types": COMPUTE_TYPES,
        }

    @app.get("/api/demo")
    def demo() -> dict[str, Any]:
        return {"rows": _segments_to_rows(demo_project().segments)}

    @app.post("/api/upload")
    async def upload(file: UploadFile) -> dict[str, str]:
        name = _safe_file_name(file.filename or "upload")
        candidate = Path(name)
        if is_supported_audio(candidate):
            kind = "audio"
        elif is_supported_video(candidate):
            kind = "video"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {candidate.suffix}")

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        path = UPLOAD_DIR / name
        path.write_bytes(await file.read())
        logger.info("Saved uploaded file: %s", path)
        return {"path": str(path), "name": name, "kind": kind}

    @app.post("/api/extract")
    def extract(request: ExtractRequest) -> dict[str, str]:
        source = _uploaded_path(request.path)
        target = source.parent / f"{source.stem}-transcription.mp3"
        try:
            extract_audio(source, target)
        except (FileNotFoundError, ValueError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:  # FFmpeg failures surface as CalledProcessError
            logger.exception("Audio extraction failed for %s", source)
            raise HTTPException(
                status_code=500,
                detail="FFmpeg failed to extract audio. Check that FFmpeg is installed.",
            ) from error
        return {"path": str(target)}

    @app.post("/api/transcribe")
    def transcribe(request: TranscribeRequest) -> dict[str, str]:
        audio = _uploaded_path(request.path)
        language = None if request.language == "auto" else request.language

        def work(job: Job) -> list[dict[str, Any]]:
            def on_progress(done_seconds: float, total_seconds: float | None) -> None:
                job.done = done_seconds
                job.total = total_seconds
                job.message = f"Transcribing… {_format_duration(done_seconds)} processed"

            engine = FasterWhisperTranscriptionEngine(
                model_size=request.model_size,
                device="cpu",
                compute_type=request.compute_type,
            )
            segments = engine.transcribe(
                audio,
                language=language,
                progress_callback=on_progress,
                cancel_requested=job.cancel.is_set,
            )
            return _segments_to_rows(segments)

        job = jobs.start("transcribe", work)
        return {"job_id": job.id}

    @app.post("/api/translate")
    def translate(request: TranslateRequest) -> dict[str, str]:
        if request.target_language not in LANGUAGE_BY_CODE:
            raise HTTPException(status_code=400, detail="Unknown target language.")
        try:
            source = _rows_to_segments(request.rows, target_language_code=request.target_language)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        if not source:
            raise HTTPException(status_code=400, detail="There are no subtitle rows to translate.")

        language = LANGUAGE_BY_CODE[request.target_language]
        target_label = f"{language.label} [{language.code}]"
        tone = _tone_mode_from_label(request.tone)

        def work(job: Job) -> list[dict[str, Any]]:
            def on_progress(done: int, total: int) -> None:
                job.done = done
                job.total = total
                job.message = f"Translating batch {done}/{total}"

            engine = GeminiTranslationEngine(
                model_name=request.model_name.strip() or "gemini-2.5-flash",
                api_key=(request.api_key or "").strip() or None,
            )
            translated = engine.translate(
                source,
                target_label,
                tone,
                progress_callback=on_progress,
                cancel_requested=job.cancel.is_set,
            )
            return _segments_to_rows(translated)

        job = jobs.start("translate", work)
        return {"job_id": job.id}

    @app.get("/api/jobs/{job_id}")
    def job_status(job_id: str) -> dict[str, Any]:
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Unknown job.")
        return {
            "kind": job.kind,
            "status": job.status,
            "done": job.done,
            "total": job.total,
            "message": job.message,
            "error": job.error,
            "rows": job.result if job.status == "done" else None,
        }

    @app.post("/api/jobs/{job_id}/cancel")
    def cancel_job(job_id: str) -> dict[str, bool]:
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Unknown job.")
        job.cancel.set()
        return {"cancelling": True}

    @app.post("/api/progress")
    def progress(request: ProgressRequest) -> dict[str, Any]:
        values = _calculate_progress(
            request.rows,
            request.subtitle_source,
            request.prepared_audio_path,
            request.export_complete,
            request.output_mode,
        )
        return {"progress": values, "current_step": _current_step(values)}

    @app.post("/api/review/mark-all")
    def mark_all(request: RowsRequest) -> dict[str, Any]:
        return {"rows": _mark_all_reviewed(request.rows)}

    @app.post("/api/export")
    def export(request: ExportRequest) -> dict[str, Any]:
        if request.target_language not in LANGUAGE_BY_CODE:
            raise HTTPException(status_code=400, detail="Unknown target language.")
        try:
            segments = _rows_to_segments(request.rows, target_language_code=request.target_language)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        if not _is_export_ready(segments, request.output_mode):
            raise HTTPException(status_code=400, detail="Nothing to export for this output mode.")

        order = _language_order_for_output_mode(request.output_mode, request.target_language)
        project = SubtitleProject(
            name="Edited Subtitles",
            target_language=request.target_language,
            output_languages=order,
            segments=segments,
        )
        texts = {
            "srt": render_srt(segments, order),
            "txt": render_plain_text(segments, order),
            "fcpxml": render_basic_fcpxml(project),
        }
        if request.save:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            (OUTPUT_DIR / "subtitles.srt").write_text(texts["srt"], encoding="utf-8")
            (OUTPUT_DIR / "subtitles.txt").write_text(texts["txt"], encoding="utf-8")
            (OUTPUT_DIR / "subtitles.fcpxml").write_text(texts["fcpxml"], encoding="utf-8")
            logger.info("Exported SRT/TXT/FCPXML files to %s", OUTPUT_DIR)
        return {"texts": texts, "folder": str(OUTPUT_DIR) if request.save else None}

    return app


def _uploaded_path(raw: str) -> Path:
    """Resolve a path the page sent, and refuse anything outside the upload folder."""
    upload_root = UPLOAD_DIR.resolve()
    path = Path(raw).resolve()
    if upload_root not in path.parents or not path.exists():
        raise HTTPException(status_code=400, detail="That file is not an uploaded file.")
    return path


app = create_app()


def run() -> None:
    """Start the web app on http://127.0.0.1:8000 for local use."""
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run()
