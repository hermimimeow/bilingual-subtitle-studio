# Bilingual Subtitle Studio

Local-first AI subtitle workflow for creators using Final Cut Pro.

The MVP focuses on turning a final audio or local video export into editable subtitle data, then exporting SRT, plain text, and FCPXML title clips for Final Cut Pro.

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

The UI runs locally in your browser. It lets you upload audio/video, save media locally, extract audio with FFmpeg, transcribe with faster-whisper, translate or rewrite with Gemini, edit subtitle rows, choose an output mode, preview SRT/TXT/FCPXML, download one selected export format, and write files to `outputs/ui`.

The first transcription run may download the selected Whisper model. Start with the `base` model for faster local testing.

## Gemini Translation

Whisper creates the original transcript and timestamps. Gemini fills the `Translation` column in the selected target language.

Create an API key at:

```text
https://aistudio.google.com/app/apikey
```

Then either paste it into the UI or set it before starting Streamlit:

```bash
export GEMINI_API_KEY="your-api-key"
uv run streamlit run src/bilingual_subtitle_studio/ui.py
```

Click `Transcribe` first, then choose a target language and click `Translate`. The app supports `Original + Translation`, `Original only`, and `Translation only` output modes. You can edit the generated SRT text in the Export section before downloading or writing files.

Gemini receives subtitle text only. Audio and video files stay local.

## Export Notes

- SRT is best for captions and platform uploads.
- TXT is best for review and copy editing.
- FCPXML creates basic Final Cut title clips with timing preserved.
- Rows marked `needs_review` show warnings but do not block draft export.
- The download control uses a format dropdown: `SRT`, `TXT`, or `FCPXML`.

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
- Generate target-language subtitle text with Gemini.
- Edit subtitle records before export.
- Export SRT, plain text, and basic Final Cut Pro FCPXML title clips.

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
  operations.py     Long-running operation cancellation helpers
  ui.py             Streamlit local browser UI
tests/
  test_exports.py
  test_translation.py
  test_ui_helpers.py
```

## Documents

- `PRD.md`: product requirements from the creator workflow perspective.
- `requirement.md`: implementation-focused MVP requirements.
- `architecture.md`: local architecture and technical decisions.
