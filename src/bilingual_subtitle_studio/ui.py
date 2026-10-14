from __future__ import annotations

import time
from pathlib import Path
from subprocess import CalledProcessError

from bilingual_subtitle_studio.app_logging import LOG_PATH, get_logger
from bilingual_subtitle_studio.audio import extract_audio, is_supported_audio, is_supported_video
from bilingual_subtitle_studio.demo_data import demo_project
from bilingual_subtitle_studio.fcpxml import render_basic_fcpxml, write_basic_fcpxml
from bilingual_subtitle_studio.languages import LANGUAGE_BY_CODE, LANGUAGE_LABEL_TO_CODE, SUPPORTED_LANGUAGES
from bilingual_subtitle_studio.models import (
    SubtitleLine,
    SubtitleLineRole,
    SubtitleProject,
    SubtitleSegment,
    SubtitleStatus,
    ToneMode,
)
from bilingual_subtitle_studio.operations import OperationCancelled
from bilingual_subtitle_studio.subtitles import render_plain_text, render_srt
from bilingual_subtitle_studio.transcription import FasterWhisperTranscriptionEngine
from bilingual_subtitle_studio.translation import GeminiTranslationEngine


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="Bilingual Subtitle Studio", layout="wide")
    _inject_dark_style(st)
    logger = get_logger("bilingual_subtitle_studio.ui")

    if "rows" not in st.session_state:
        st.session_state.rows = _segments_to_rows(demo_project().segments)
    if "subtitle_source" not in st.session_state:
        st.session_state.subtitle_source = "demo"
    if "prepared_audio_path" not in st.session_state:
        st.session_state.prepared_audio_path = ""
    if "review_count" not in st.session_state:
        st.session_state.review_count = 0
    if "srt_base_text" not in st.session_state:
        st.session_state.srt_base_text = ""
    if "srt_edit_text" not in st.session_state:
        st.session_state.srt_edit_text = ""
    if "export_complete" not in st.session_state:
        st.session_state.export_complete = False
    if "target_language_code" not in st.session_state:
        st.session_state.target_language_code = "en"
    if "output_mode" not in st.session_state:
        st.session_state.output_mode = "Original + Translation"
    if "last_operation_summary" not in st.session_state:
        st.session_state.last_operation_summary = "Idle"
    if "operation_running" not in st.session_state:
        st.session_state.operation_running = False
    if "operation_cancel_requested" not in st.session_state:
        st.session_state.operation_cancel_requested = False
    if "operation_status" not in st.session_state:
        st.session_state.operation_status = "idle"

    st.markdown(
        """
<div class="top-title">Bilingual Subtitle Studio</div>
""",
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("<div class='side-logo'>BSS</div>", unsafe_allow_html=True)
        progress = _calculate_progress(
            st.session_state.rows,
            st.session_state.subtitle_source,
            st.session_state.prepared_audio_path,
            st.session_state.export_complete,
            st.session_state.output_mode,
        )
        _render_current_task_panel(st, _current_task(progress))
        _render_progress_panel(
            st,
            progress,
        )
        operation_placeholder = st.empty()
        operation_placeholder.info(st.session_state.last_operation_summary)
        if _operation_is_active(st.session_state.operation_status):
            stop_disabled = st.session_state.operation_status == "stopping"
            if st.button("Stop current task", type="primary", disabled=stop_disabled):
                st.session_state.operation_status = "stopping"
                st.session_state.operation_running = True
                st.session_state.operation_cancel_requested = True
                st.session_state.last_operation_summary = "Stopping..."
                operation_placeholder.warning("Stopping at the next safe checkpoint...")
        elif st.session_state.operation_status in {"stopped", "failed", "done"}:
            if st.button("Ready for next task"):
                _reset_operation_state(st.session_state)
                st.rerun()

        if st.session_state.operation_status == "idle" and st.session_state.operation_cancel_requested:
            st.session_state.operation_cancel_requested = False
        with st.expander("Folders"):
            output_dir = st.text_input("Output directory", value="outputs/ui")
            upload_dir = st.text_input("Upload directory", value="uploads")
        with st.expander("Latest Logs"):
            st.caption(f"Log file: `{LOG_PATH}`")
            st.code(_read_log_tail(LOG_PATH), language="text")
        if st.button("Reset Demo"):
            st.session_state.rows = _segments_to_rows(demo_project().segments)
            st.session_state.subtitle_source = "demo"
            st.session_state.review_count = 0
            st.session_state.export_complete = False
            st.session_state.output_mode = "Original + Translation"
            st.session_state.operation_running = False
            st.session_state.operation_cancel_requested = False
            st.session_state.operation_status = "idle"
            logger.info("Reset subtitle rows to demo data")
            st.rerun()

    st.markdown(
        """
<div class="section-heading">
  <span class="section-index">01</span>
  <div>
    <h2>Import Media</h2>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader(
        "Upload audio or video",
        type=["wav", "mp3", "m4a", "aac", "mp4", "mov", "m4v"],
    )

    if uploaded_file is not None:
        uploaded_path = _save_uploaded_file(uploaded_file, Path(upload_dir))
        logger.info("Saved uploaded file: %s", uploaded_path)
        st.success(f"Saved upload locally: {uploaded_path}")

        if is_supported_audio(uploaded_path):
            st.session_state.prepared_audio_path = str(uploaded_path)
            st.session_state.export_complete = False
            st.audio(str(uploaded_path))
            st.success("Audio ready.")
        elif is_supported_video(uploaded_path):
            st.video(str(uploaded_path))
            extracted_audio_path = Path(upload_dir) / f"{uploaded_path.stem}-transcription.mp3"
            if extracted_audio_path.exists():
                st.session_state.prepared_audio_path = str(extracted_audio_path)
                st.session_state.export_complete = False
                st.success(f"Audio ready: {extracted_audio_path}")
                st.audio(str(extracted_audio_path))
            if st.button("Extract Audio"):
                try:
                    extract_audio(uploaded_path, extracted_audio_path)
                except FileNotFoundError:
                    st.error("Uploaded file was not found on disk.")
                except CalledProcessError:
                    logger.exception("FFmpeg failed to extract audio from %s", uploaded_path)
                    st.error("FFmpeg failed to extract audio. Check that FFmpeg is installed.")
                except ValueError as error:
                    logger.exception("Unsupported upload for extraction: %s", uploaded_path)
                    st.error(str(error))
                else:
                    st.session_state.prepared_audio_path = str(extracted_audio_path)
                    st.session_state.export_complete = False
                    logger.info("Extracted audio for transcription: %s", extracted_audio_path)
                    st.success(f"Extracted audio: {extracted_audio_path}")
                    st.audio(str(extracted_audio_path))
        else:
            logger.warning("Unsupported uploaded file type: %s", uploaded_path)
            st.error(f"Unsupported file type: {uploaded_path.suffix}")

    st.markdown(
        """
<div class="section-heading">
  <span class="section-index">02</span>
  <div>
    <h2>Transcription</h2>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    transcribe_col, settings_col = st.columns([1.1, 0.9], gap="large")
    with settings_col:
        model_size = st.selectbox("Whisper model", ["tiny", "base", "small", "medium", "large-v3"], index=1)
        language_choice = st.selectbox("Language hint", ["auto", "zh", "en", "yue"], index=0)
        compute_type = st.selectbox("Compute type", ["int8", "float32", "default"], index=0)
    with transcribe_col:
        prepared_audio_path = Path(st.session_state.prepared_audio_path) if st.session_state.prepared_audio_path else None
        if prepared_audio_path:
            st.success(f"Ready to transcribe: {prepared_audio_path}")
        else:
            st.info("Upload audio first.")

        if st.button(
            "Transcribe",
            disabled=prepared_audio_path is None or _operation_is_active(st.session_state.operation_status),
        ):
            assert prepared_audio_path is not None
            _start_operation(st.session_state)
            logger.info(
                "Starting transcription: path=%s model=%s language=%s compute_type=%s",
                prepared_audio_path,
                model_size,
                language_choice,
                compute_type,
            )
            try:
                operation_start = time.monotonic()
                operation_placeholder.info("Transcribing... elapsed 0s")

                def update_transcription_progress(done_seconds: float, total_seconds: float | None) -> None:
                    elapsed = time.monotonic() - operation_start
                    if total_seconds:
                        percent = min(_percent(round(done_seconds), round(total_seconds)), 100)
                        eta = _estimate_eta(elapsed, max(done_seconds, 0.1), total_seconds)
                        operation_placeholder.progress(
                            percent,
                            text=(
                                f"Transcribing · elapsed {_format_duration(elapsed)} · "
                                f"ETA {_format_duration(eta)}"
                            ),
                        )
                    else:
                        operation_placeholder.info(
                            f"Transcribing... elapsed {_format_duration(elapsed)} · ETA estimating"
                        )

                with st.spinner("Transcribing..."):
                    engine = FasterWhisperTranscriptionEngine(
                        model_size=model_size,
                        device="cpu",
                        compute_type=compute_type,
                    )
                    language = None if language_choice == "auto" else language_choice
                    transcribed_segments = engine.transcribe(
                        prepared_audio_path,
                        language=language,
                        progress_callback=update_transcription_progress,
                        cancel_requested=lambda: bool(st.session_state.operation_cancel_requested),
                    )
                elapsed = time.monotonic() - operation_start
                st.session_state.last_operation_summary = f"Transcription finished in {_format_duration(elapsed)}"
                operation_placeholder.success(st.session_state.last_operation_summary)
            except OperationCancelled as error:
                logger.warning("Transcription stopped for %s", prepared_audio_path)
                _finish_operation(st.session_state, "stopped", "Transcription stopped. Ready for next task.")
                operation_placeholder.warning(str(error))
                st.warning(str(error))
            except Exception as error:
                logger.exception("Transcription failed for %s", prepared_audio_path)
                _finish_operation(st.session_state, "failed", "Transcription failed")
                operation_placeholder.error(st.session_state.last_operation_summary)
                st.error(f"Transcription failed: {error}")
                st.info(f"Check the log file for details: {LOG_PATH}")
            else:
                if not transcribed_segments:
                    logger.warning("Transcription produced no segments: %s", prepared_audio_path)
                    st.warning("No speech detected.")
                else:
                    st.session_state.rows = _segments_to_rows(transcribed_segments)
                    st.session_state.subtitle_source = "transcription"
                    st.session_state.review_count = 0
                    st.session_state.export_complete = False
                    logger.info("Transcription completed with %s segments", len(transcribed_segments))
                    st.success(f"Loaded {len(transcribed_segments)} rows.")
                    _finish_operation(st.session_state, "done", st.session_state.last_operation_summary)
                    st.rerun()
            finally:
                if st.session_state.operation_status in {"running", "stopping"}:
                    _finish_operation(st.session_state, "done", st.session_state.last_operation_summary)

    st.markdown(
        """
<div class="section-heading">
  <span class="section-index">03</span>
  <div>
    <h2>Gemini Translation</h2>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    translate_col, translate_settings_col = st.columns([1.1, 0.9], gap="large")
    with translate_settings_col:
        gemini_api_key = st.text_input(
            "Gemini API key",
            type="password",
        )
        gemini_model = st.text_input("Gemini model", value="gemini-2.5-flash")
        target_language_label = st.selectbox(
            "Target language",
            [language.label for language in SUPPORTED_LANGUAGES if language.code != "auto"],
            index=_target_language_index(st.session_state.target_language_code),
        )
        target_language_code = LANGUAGE_LABEL_TO_CODE[target_language_label]
        st.session_state.target_language_code = target_language_code
        target_language = f"{target_language_label} [{target_language_code}]"
        tone_label = st.selectbox(
            "Tone",
            ["Natural", "Literal", "Funny Vlog", "Cinematic", "Short-Form", "Xiaohongshu"],
            index=0,
        )
    with translate_col:
        if st.button(
            "Translate",
            disabled=not st.session_state.rows or _operation_is_active(st.session_state.operation_status),
        ):
            _start_operation(st.session_state)
            try:
                source_segments = _rows_to_segments(
                    st.session_state.rows,
                    target_language_code=st.session_state.target_language_code,
                )
                tone = _tone_mode_from_label(tone_label)
                engine = GeminiTranslationEngine(
                    model_name=gemini_model.strip() or "gemini-2.5-flash",
                    api_key=gemini_api_key.strip() or None,
                )
                operation_start = time.monotonic()

                def update_translation_progress(done: int, total: int) -> None:
                    elapsed = time.monotonic() - operation_start
                    percent = _percent(done, total)
                    eta = _estimate_eta(elapsed, done, total)
                    operation_placeholder.progress(
                        percent,
                        text=(
                            f"Translating batch {done}/{total} · "
                            f"elapsed {_format_duration(elapsed)} · ETA {_format_duration(eta)}"
                        ),
                    )

                with st.spinner("Translating..."):
                    translated_segments = engine.translate(
                        source_segments,
                        target_language,
                        tone,
                        progress_callback=update_translation_progress,
                        cancel_requested=lambda: bool(st.session_state.operation_cancel_requested),
                    )
                elapsed = time.monotonic() - operation_start
                st.session_state.last_operation_summary = f"Translation finished in {_format_duration(elapsed)}"
                operation_placeholder.success(st.session_state.last_operation_summary)
            except OperationCancelled as error:
                logger.warning("Gemini translation stopped")
                _finish_operation(st.session_state, "stopped", "Translation stopped. Ready for next task.")
                operation_placeholder.warning(str(error))
                st.warning(str(error))
            except Exception as error:
                logger.exception("Gemini translation failed")
                _finish_operation(st.session_state, "failed", "Translation failed")
                operation_placeholder.error(st.session_state.last_operation_summary)
                st.error(f"Gemini translation failed: {error}")
                st.info(
                    "Create an API key in Google AI Studio, then paste it here or set "
                    "GEMINI_API_KEY before starting Streamlit."
                )
            else:
                review_count = sum(
                    segment.status.value == "needs_review" for segment in translated_segments
                )
                st.session_state.rows = _segments_to_rows(translated_segments)
                st.session_state.subtitle_source = "gemini_translation"
                st.session_state.review_count = review_count
                st.session_state.export_complete = False
                logger.info("Gemini translation completed with %s rows", len(translated_segments))
                st.success(f"Translated {len(translated_segments)} rows.")
                if review_count:
                    st.warning(f"Review {review_count} rows.")
                _finish_operation(st.session_state, "done", st.session_state.last_operation_summary)
                st.rerun()
            finally:
                if st.session_state.operation_status in {"running", "stopping"}:
                    _finish_operation(st.session_state, "done", st.session_state.last_operation_summary)

    st.markdown(
        """
<div class="section-heading editor-heading">
  <span class="section-index">04</span>
  <div>
    <h2>Subtitle Timeline</h2>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    if st.session_state.subtitle_source == "demo":
        st.warning("Demo data")
    elif st.session_state.subtitle_source == "gemini_translation":
        st.success("Translated")
    else:
        st.info("Transcribed only")
    if st.session_state.review_count:
        st.warning(f"Review {st.session_state.review_count} rows.")
    if st.button("Mark All Reviewed", disabled=not st.session_state.rows):
        st.session_state.rows = _mark_all_reviewed(st.session_state.rows)
        st.session_state.review_count = 0
        st.session_state.export_complete = False
        st.rerun()

    edited_rows = st.data_editor(
        st.session_state.rows,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "index": st.column_config.NumberColumn("#", min_value=1, step=1),
            "start_seconds": st.column_config.NumberColumn("Start", min_value=0.0, step=0.1, format="%.2f"),
            "end_seconds": st.column_config.NumberColumn("End", min_value=0.1, step=0.1, format="%.2f"),
            "source_text": st.column_config.TextColumn("Original", width="large"),
            "translated_text": st.column_config.TextColumn("Translation", width="large"),
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=[status.value for status in SubtitleStatus],
                width="small",
            ),
        },
        hide_index=True,
    )
    if edited_rows != st.session_state.rows:
        st.session_state.export_complete = False
    st.session_state.rows = edited_rows

    try:
        segments = _rows_to_segments(
            edited_rows,
            target_language_code=st.session_state.target_language_code,
        )
    except ValueError as error:
        st.error(str(error))
        return

    output_mode = st.selectbox(
        "Output mode",
        ["Original + Translation", "Original only", "Translation only"],
        index=_output_mode_index(st.session_state.output_mode),
    )
    if output_mode != st.session_state.output_mode:
        st.session_state.output_mode = output_mode
        st.session_state.export_complete = False
    language_order = _language_order_for_output_mode(
        st.session_state.output_mode,
        st.session_state.target_language_code,
    )
    target_language = LANGUAGE_BY_CODE.get(st.session_state.target_language_code)
    project = SubtitleProject(
        name="UI Edited Subtitles",
        target_language=st.session_state.target_language_code,
        output_languages=language_order,
        segments=segments,
    )
    srt_text = render_srt(segments, language_order)
    plain_text = render_plain_text(segments, language_order)
    fcpxml_text = render_basic_fcpxml(project)
    if st.session_state.srt_base_text != srt_text:
        st.session_state.srt_base_text = srt_text
        st.session_state.srt_edit_text = srt_text

    st.markdown(
        """
<div class="section-heading export-heading">
  <span class="section-index">05</span>
  <div>
    <h2>Export</h2>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric("Subtitle Blocks", len(segments))
    with metric_col2:
        total_duration = max((segment.end_seconds for segment in segments), default=0)
        st.metric("Timeline Length", f"{total_duration:.1f}s")
    with metric_col3:
        translation_count = sum(1 for segment in segments if segment.translated_text)
        translation_label = target_language.name if target_language else "Translation"
        st.metric(f"{translation_label} Lines", f"{translation_count}/{len(segments)}")

    review_count = sum(segment.status == SubtitleStatus.NEEDS_REVIEW for segment in segments)
    export_ready = _is_export_ready(segments, st.session_state.output_mode)
    if segments and not export_ready:
        st.warning("No exportable text for the selected output mode.")
    if review_count and _output_mode_uses_translation(st.session_state.output_mode):
        st.warning(f"{review_count} rows need review. Export is still allowed.")

    edited_srt_text = st.text_area(
        "SRT",
        key="srt_edit_text",
        height=260,
        disabled=not export_ready,
    )

    download_format = st.selectbox("Download format", ["SRT", "TXT", "FCPXML"])
    download_text, download_file_name, download_mime = _download_payload(
        download_format,
        edited_srt_text,
        plain_text,
        fcpxml_text,
    )
    st.download_button(
        f"Download {download_format}",
        download_text,
        file_name=download_file_name,
        mime=download_mime,
        disabled=not export_ready,
    )

    if st.button("Export Files", disabled=not export_ready or _operation_is_active(st.session_state.operation_status)):
        export_dir = Path(output_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        (export_dir / "subtitles.srt").write_text(edited_srt_text, encoding="utf-8")
        (export_dir / "subtitles.txt").write_text(plain_text, encoding="utf-8")
        write_basic_fcpxml(export_dir / "subtitles.fcpxml", project)
        st.session_state.export_complete = True
        _finish_operation(st.session_state, "done", "Export finished")
        operation_placeholder.success(st.session_state.last_operation_summary)
        logger.info("Exported SRT/TXT/FCPXML files to %s", export_dir)
        st.success(f"Exported files to {export_dir}")

    tab_srt, tab_text, tab_fcpxml = st.tabs(["SRT Preview", "Text Preview", "FCPXML Preview"])
    with tab_srt:
        st.code(edited_srt_text, language="srt")
    with tab_text:
        st.code(plain_text, language="text")
    with tab_fcpxml:
        st.code(fcpxml_text, language="xml")


def _inject_dark_style(st: object) -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --bg: #070a12;
  --panel: rgba(15, 23, 42, 0.74);
  --panel-strong: rgba(17, 24, 39, 0.94);
  --border: rgba(148, 163, 184, 0.22);
  --text: #e5e7eb;
  --muted: #94a3b8;
  --cyan: #22d3ee;
  --violet: #8b5cf6;
  --pink: #ec4899;
  --green: #34d399;
}

html, body, [class*="css"] {
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
  color: var(--text);
  background:
    radial-gradient(circle at 18% 8%, rgba(124, 58, 237, 0.34), transparent 34%),
    radial-gradient(circle at 82% 18%, rgba(34, 211, 238, 0.24), transparent 30%),
    radial-gradient(circle at 45% 88%, rgba(236, 72, 153, 0.14), transparent 36%),
    linear-gradient(135deg, #050711 0%, #090d19 48%, #030712 100%);
}

.block-container {
  max-width: 1320px;
  padding-top: 2.2rem;
  padding-bottom: 4rem;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(2, 6, 23, 0.98), rgba(15, 23, 42, 0.94));
  border-right: 1px solid rgba(34, 211, 238, 0.16);
}

[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  color: #f8fafc;
}

.side-logo {
  width: 58px;
  height: 58px;
  display: grid;
  place-items: center;
  margin: 0.35rem 0 1.2rem;
  border-radius: 18px;
  background: linear-gradient(135deg, var(--cyan), var(--violet) 52%, var(--pink));
  color: #020617;
  font-weight: 900;
  letter-spacing: -0.08em;
  box-shadow: 0 0 34px rgba(34, 211, 238, 0.28);
}

.top-title {
  position: fixed;
  top: 0.72rem;
  right: 1.1rem;
  z-index: 999;
  padding: 0.42rem 0.7rem;
  border: 1px solid rgba(34, 211, 238, 0.26);
  border-radius: 999px;
  background: rgba(2, 6, 23, 0.72);
  color: #cbd5e1;
  font-size: 0.82rem;
  font-weight: 750;
  letter-spacing: -0.02em;
  backdrop-filter: blur(12px);
}

.section-heading {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1.5rem 0 0.8rem;
}

.section-index {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border-radius: 16px;
  color: #020617;
  background: linear-gradient(135deg, var(--cyan), var(--green));
  font-weight: 900;
  box-shadow: 0 0 28px rgba(34, 211, 238, 0.22);
}

.section-heading h2 {
  margin: 0;
  color: #f8fafc;
  font-size: 1.55rem;
  letter-spacing: -0.04em;
}

.section-heading p {
  margin: 0.15rem 0 0;
  color: var(--muted);
}

.signal-card {
  min-height: 132px;
  padding: 1.2rem;
  border: 1px solid rgba(34, 211, 238, 0.2);
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(8, 47, 73, 0.4), rgba(15, 23, 42, 0.8));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.07);
}

.signal-card strong {
  color: #f8fafc;
  font-size: 1.02rem;
}

.signal-card p {
  margin: 0.55rem 0 0;
  color: #a7b4c8;
  line-height: 1.55;
}

.signal-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  margin-right: 0.55rem;
  border-radius: 999px;
  background: var(--green);
  box-shadow: 0 0 18px var(--green);
}

.progress-panel {
  margin: 1rem 0;
  padding: 0.9rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 18px;
  background: rgba(15, 23, 42, 0.62);
}

.task-card {
  margin: 0.5rem 0 1rem;
  padding: 1rem;
  border: 1px solid rgba(34, 211, 238, 0.24);
  border-radius: 20px;
  background:
    linear-gradient(135deg, rgba(8, 47, 73, 0.55), rgba(30, 41, 59, 0.68)),
    radial-gradient(circle at 100% 0%, rgba(52, 211, 153, 0.18), transparent 42%);
}

.task-label {
  color: #67e8f9;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.task-title {
  margin-top: 0.25rem;
  color: #f8fafc;
  font-size: 1.15rem;
  font-weight: 850;
  letter-spacing: -0.04em;
}

.task-note {
  margin-top: 0.35rem;
  color: #a7b4c8;
  font-size: 0.84rem;
  line-height: 1.45;
}

.progress-panel h3 {
  margin: 0 0 0.65rem;
  font-size: 0.95rem;
}

.progress-row {
  margin: 0.55rem 0;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.22rem;
  color: #cbd5e1;
  font-size: 0.82rem;
}

.progress-track {
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(51, 65, 85, 0.9);
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--cyan), var(--green));
}

[data-testid="stFileUploader"],
[data-testid="stDataFrameResizable"],
[data-testid="stMetric"],
[data-testid="stTabs"] {
  border-radius: 24px;
}

[data-testid="stFileUploader"] section {
  border: 1px dashed rgba(34, 211, 238, 0.38);
  border-radius: 24px;
  background: rgba(15, 23, 42, 0.72);
}

[data-testid="stMetric"] {
  padding: 1rem;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.78), rgba(30, 41, 59, 0.54));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.stButton > button, .stDownloadButton > button {
  width: 100%;
  border: 1px solid rgba(34, 211, 238, 0.28);
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.95), rgba(124, 58, 237, 0.94));
  color: white;
  font-weight: 800;
  letter-spacing: -0.01em;
  box-shadow: 0 14px 32px rgba(37, 99, 235, 0.22);
  transition: transform 160ms ease, box-shadow 160ms ease, filter 160ms ease;
}

.stButton > button:hover, .stDownloadButton > button:hover {
  transform: translateY(-1px);
  filter: brightness(1.08);
  box-shadow: 0 18px 44px rgba(34, 211, 238, 0.28);
}

[data-testid="stAlert"] {
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(15, 23, 42, 0.7);
}

.stCodeBlock pre {
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 20px;
  background: rgba(2, 6, 23, 0.82) !important;
}

input, textarea {
  border-radius: 14px !important;
}

hr {
  border-color: rgba(148, 163, 184, 0.16);
}
</style>
""",
        unsafe_allow_html=True,
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


def _render_current_task_panel(st: object, task: tuple[str, str]) -> None:
    title, note = task
    st.caption("Current Task")
    st.info(f"{title}\n\n{note}")


def _render_progress_panel(st: object, progress: dict[str, int]) -> None:
    st.caption("Progress")
    for label, percent in progress.items():
        st.progress(percent, text=f"{label}: {percent}%")


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


if __name__ == "__main__":
    main()
