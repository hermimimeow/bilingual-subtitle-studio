# Bilingual Subtitle Studio

Local-first AI subtitle workflow for creators using Final Cut Pro.

The MVP focuses on turning a final audio export into editable Chinese-English subtitle data, then exporting SRT, plain text, and eventually FCPXML title clips for Final Cut Pro.

## Why Python + uv

This project is optimized for local audio, transcription, subtitle processing, and XML export. Python has the strongest ecosystem for Whisper/faster-whisper, FFmpeg orchestration, subtitle tooling, and local AI workflows. `uv` keeps the local developer workflow fast and reproducible.

## Quick Start

```bash
uv sync
uv run bilingual-subtitle-studio demo --output-dir outputs/demo
```

The demo command writes sample bilingual subtitle exports without requiring a transcription model.

## Start The Clickable UI

```bash
uv run streamlit run src/bilingual_subtitle_studio/ui.py
```

The UI runs locally in your browser. It lets you upload audio/video, save media locally, extract audio with FFmpeg, transcribe with faster-whisper, translate with Gemini, edit subtitle rows, preview SRT/TXT/FCPXML, download exports, and write files to `outputs/ui`.

The first transcription run may download the selected Whisper model. Start with the `base` model for faster local testing.

## Gemini Translation

Whisper creates the original transcript and timestamps. Gemini fills the English translation column.

Create an API key at:

```text
https://aistudio.google.com/app/apikey
```

Then either paste it into the UI or set it before starting Streamlit:

```bash
export GEMINI_API_KEY="your-api-key"
uv run streamlit run src/bilingual_subtitle_studio/ui.py
```

Click `Transcribe` first, then click `Translate`. Export after the `English Lines` count matches the subtitle count.

Gemini receives subtitle text only. Audio and video files stay local.

## Logs

The app writes local troubleshooting logs to:

```text
logs/app.log
```

The UI sidebar also includes a `Latest Logs` panel for quick checks.

## MVP Scope

- Import audio files.
- Extract audio from local video files with FFmpeg.
- Transcribe audio with timestamps.
- Chunk transcript into readable subtitle blocks.
- Generate bilingual Chinese-English subtitle text with Gemini.
- Edit subtitle records before export.
- Export SRT and plain text.
- Add basic FCPXML title export.

## Project Layout

```text
src/bilingual_subtitle_studio/
  audio.py          FFmpeg-based local audio extraction
  chunking.py       Subtitle chunking logic
  cli.py            Local CLI entrypoint
  fcpxml.py         Final Cut Pro XML export skeleton
  models.py         Shared subtitle data models
  subtitles.py      SRT and text export
  transcription.py  Speech-to-text engine interface
  translation.py    Translation/rewrite engine interface
  ui.py             Streamlit local browser UI
tests/
  test_exports.py
```

## Documents

- `PRD.md`: product requirements from the creator workflow perspective.
- `requirement.md`: implementation-focused MVP requirements.
- `architecture.md`: local architecture and technical decisions.
