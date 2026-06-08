from __future__ import annotations

from pathlib import Path
from subprocess import CalledProcessError

from bilingual_subtitle_studio.app_logging import LOG_PATH, get_logger
from bilingual_subtitle_studio.audio import extract_audio, is_supported_audio, is_supported_video
from bilingual_subtitle_studio.demo_data import demo_project
from bilingual_subtitle_studio.fcpxml import render_basic_fcpxml, write_basic_fcpxml
from bilingual_subtitle_studio.models import SubtitleProject, SubtitleSegment, ToneMode
from bilingual_subtitle_studio.subtitles import render_plain_text, render_srt, write_plain_text, write_srt
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

    st.markdown(
        """
<section class="hero-panel">
  <h1>Bilingual Subtitle Studio</h1>
</section>
""",
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("<div class='side-logo'>BSS</div>", unsafe_allow_html=True)
        st.header("Mission Flow")
        st.markdown(
            """
1. Import
2. Transcribe
3. Translate
4. Edit
5. Export
"""
        )
        output_dir = st.text_input("Output directory", value="outputs/ui")
        upload_dir = st.text_input("Upload directory", value="uploads")
        st.caption(f"Log file: `{LOG_PATH}`")
        with st.expander("Latest Logs"):
            st.code(_read_log_tail(LOG_PATH), language="text")
        if st.button("Reset Demo"):
            st.session_state.rows = _segments_to_rows(demo_project().segments)
            st.session_state.subtitle_source = "demo"
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
    import_panel, status_panel = st.columns([1.1, 0.9], gap="large")
    with import_panel:
        uploaded_file = st.file_uploader(
            "Upload audio or video",
            type=["wav", "mp3", "m4a", "aac", "mp4", "mov", "m4v"],
        )
    with status_panel:
        st.markdown(
            """
<div class="signal-card">
  <span class="signal-dot"></span>
  <strong>Ready</strong>
</div>
""",
            unsafe_allow_html=True,
        )

    if uploaded_file is not None:
        uploaded_path = _save_uploaded_file(uploaded_file, Path(upload_dir))
        logger.info("Saved uploaded file: %s", uploaded_path)
        st.success(f"Saved upload locally: {uploaded_path}")

        if is_supported_audio(uploaded_path):
            st.session_state.prepared_audio_path = str(uploaded_path)
            st.audio(str(uploaded_path))
            st.success("Audio ready.")
        elif is_supported_video(uploaded_path):
            st.video(str(uploaded_path))
            extracted_audio_path = Path(upload_dir) / f"{uploaded_path.stem}-transcription.mp3"
            if extracted_audio_path.exists():
                st.session_state.prepared_audio_path = str(extracted_audio_path)
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

        if st.button("Transcribe", disabled=prepared_audio_path is None):
            assert prepared_audio_path is not None
            logger.info(
                "Starting transcription: path=%s model=%s language=%s compute_type=%s",
                prepared_audio_path,
                model_size,
                language_choice,
                compute_type,
            )
            try:
                with st.spinner("Transcribing..."):
                    engine = FasterWhisperTranscriptionEngine(
                        model_size=model_size,
                        device="cpu",
                        compute_type=compute_type,
                    )
                    language = None if language_choice == "auto" else language_choice
                    transcribed_segments = engine.transcribe(prepared_audio_path, language=language)
            except Exception as error:
                logger.exception("Transcription failed for %s", prepared_audio_path)
                st.error(f"Transcription failed: {error}")
                st.info(f"Check the log file for details: {LOG_PATH}")
            else:
                if not transcribed_segments:
                    logger.warning("Transcription produced no segments: %s", prepared_audio_path)
                    st.warning("No speech detected.")
                else:
                    st.session_state.rows = _segments_to_rows(transcribed_segments)
                    st.session_state.subtitle_source = "transcription"
                    logger.info("Transcription completed with %s segments", len(transcribed_segments))
                    st.success(f"Loaded {len(transcribed_segments)} rows.")
                    st.rerun()

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
        target_language = "English"
        tone_label = st.selectbox(
            "Tone",
            ["Natural", "Literal", "Funny Vlog", "Cinematic", "Short-Form", "Xiaohongshu"],
            index=0,
        )
    with translate_col:
        if st.button("Translate", disabled=not st.session_state.rows):
            try:
                source_segments = _rows_to_segments(st.session_state.rows)
                tone = _tone_mode_from_label(tone_label)
                engine = GeminiTranslationEngine(
                    model_name=gemini_model.strip() or "gemini-2.5-flash",
                    api_key=gemini_api_key.strip() or None,
                )
                with st.spinner("Translating..."):
                    translated_segments = engine.translate(source_segments, target_language, tone)
            except Exception as error:
                logger.exception("Gemini translation failed")
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
                logger.info("Gemini translation completed with %s rows", len(translated_segments))
                st.success(f"Translated {len(translated_segments)} rows.")
                if review_count:
                    st.warning(f"Review {review_count} rows.")
                st.rerun()

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

    edited_rows = st.data_editor(
        st.session_state.rows,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "index": st.column_config.NumberColumn("#", min_value=1, step=1),
            "start_seconds": st.column_config.NumberColumn("Start", min_value=0.0, step=0.1, format="%.2f"),
            "end_seconds": st.column_config.NumberColumn("End", min_value=0.1, step=0.1, format="%.2f"),
            "source_text": st.column_config.TextColumn("Original", width="large"),
            "translated_text": st.column_config.TextColumn("English", width="large"),
        },
        hide_index=True,
    )
    st.session_state.rows = edited_rows

    try:
        segments = _rows_to_segments(edited_rows)
    except ValueError as error:
        st.error(str(error))
        return

    project = SubtitleProject(name="UI Edited Bilingual Subtitles", segments=segments)
    srt_text = render_srt(segments)
    plain_text = render_plain_text(segments)
    fcpxml_text = render_basic_fcpxml(project)

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
        bilingual_count = sum(1 for segment in segments if segment.translated_text)
        st.metric("English Lines", f"{bilingual_count}/{len(segments)}")

    export_ready = bool(segments) and bilingual_count == len(segments)
    if segments and not export_ready:
        st.warning("English is missing for some rows. Click Translate before final export.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "Download SRT",
            srt_text,
            file_name="subtitles.srt",
            mime="text/plain",
            disabled=not export_ready,
        )
    with col2:
        st.download_button(
            "Download TXT",
            plain_text,
            file_name="subtitles.txt",
            mime="text/plain",
            disabled=not export_ready,
        )
    with col3:
        st.download_button(
            "Download FCPXML",
            fcpxml_text,
            file_name="subtitles.fcpxml",
            mime="application/xml",
            disabled=not export_ready,
        )

    if st.button("Export Files", disabled=not export_ready):
        export_dir = Path(output_dir)
        write_srt(export_dir / "subtitles.srt", segments)
        write_plain_text(export_dir / "subtitles.txt", segments)
        write_basic_fcpxml(export_dir / "subtitles.fcpxml", project)
        logger.info("Exported SRT/TXT/FCPXML files to %s", export_dir)
        st.success(f"Exported files to {export_dir}")

    tab_srt, tab_text, tab_fcpxml = st.tabs(["SRT Preview", "Text Preview", "FCPXML Preview"])
    with tab_srt:
        st.code(srt_text, language="srt")
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

.hero-panel {
  position: relative;
  overflow: hidden;
  padding: 2.4rem;
  margin-bottom: 1.6rem;
  border: 1px solid rgba(125, 211, 252, 0.22);
  border-radius: 32px;
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.88), rgba(30, 41, 59, 0.5)),
    radial-gradient(circle at 78% 18%, rgba(34, 211, 238, 0.26), transparent 24%),
    radial-gradient(circle at 16% 84%, rgba(236, 72, 153, 0.24), transparent 28%);
  box-shadow: 0 30px 90px rgba(0, 0, 0, 0.42), inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.hero-panel:before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px);
  background-size: 42px 42px;
  mask-image: linear-gradient(90deg, rgba(0,0,0,0.9), transparent 78%);
}

.hero-kicker {
  position: relative;
  display: inline-flex;
  padding: 0.38rem 0.7rem;
  border: 1px solid rgba(34, 211, 238, 0.32);
  border-radius: 999px;
  color: #67e8f9;
  background: rgba(8, 47, 73, 0.34);
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.16em;
}

.hero-panel h1 {
  position: relative;
  margin: 1rem 0 0.7rem;
  max-width: 860px;
  color: #f8fafc;
  font-size: clamp(2.6rem, 6vw, 5.8rem);
  line-height: 0.92;
  letter-spacing: -0.075em;
}

.hero-panel p {
  position: relative;
  max-width: 720px;
  color: #cbd5e1;
  font-size: 1.08rem;
  line-height: 1.65;
}

.hero-actions {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
  margin-top: 1.35rem;
}

.hero-actions span {
  padding: 0.65rem 0.82rem;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.7);
  color: #e2e8f0;
  font-size: 0.9rem;
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


def _segments_to_rows(segments: tuple[SubtitleSegment, ...]) -> list[dict[str, object]]:
    return [
        {
            "index": segment.index,
            "start_seconds": segment.start_seconds,
            "end_seconds": segment.end_seconds,
            "source_text": segment.source_text,
            "translated_text": segment.translated_text,
        }
        for segment in segments
    ]


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


def _rows_to_segments(rows: list[dict[str, object]]) -> tuple[SubtitleSegment, ...]:
    segments: list[SubtitleSegment] = []
    for fallback_index, row in enumerate(rows, start=1):
        if not row.get("source_text") and not row.get("translated_text"):
            continue

        index = int(row.get("index") or fallback_index)
        start_seconds = float(row.get("start_seconds") or 0)
        end_seconds = float(row.get("end_seconds") or 0)
        source_text = str(row.get("source_text") or "").strip()
        translated_text = str(row.get("translated_text") or "").strip()

        try:
            segments.append(
                SubtitleSegment(
                    index=index,
                    start_seconds=start_seconds,
                    end_seconds=end_seconds,
                    source_text=source_text,
                    translated_text=translated_text,
                )
            )
        except ValueError as error:
            raise ValueError(f"Row {fallback_index}: {error}") from error

    return tuple(segments)


if __name__ == "__main__":
    main()
