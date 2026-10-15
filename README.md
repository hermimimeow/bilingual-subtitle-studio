# Bilingual Subtitle Studio

Local-first AI subtitle workflow for creators using Final Cut Pro.

The MVP focuses on turning a final audio or local video export into editable subtitle data, then exporting SRT, plain text, and FCPXML title clips for Final Cut Pro.

## About Me

I make videos on YouTube as a part-time hobby. I film, edit, and publish them myself, so subtitles are the step that used to take the most time.

My voice-over is mostly in Cantonese, because my partner is Cantonese. The conversations between friends are mostly in English or Mandarin. I want every video to be bilingual, and I often want local terms shown in each language as well. Typing and timing those lines by hand for every project was slow, so I built this tool to do most of that work and leave me free to focus on the story.

## Why Python + uv

This project is optimized for local audio, transcription, subtitle processing, and XML export. Python has the strongest ecosystem for Whisper/faster-whisper, FFmpeg orchestration, subtitle tooling, and local AI workflows. `uv` keeps the local developer workflow fast and reproducible.

## Quick Start

```bash
uv sync
uv run bilingual-subtitle-studio demo --output-dir outputs/demo
```

The demo command writes sample bilingual subtitle exports without requiring a transcription model.

## Development

Run the tests and lint checks from the project folder:

```bash
uv run pytest
uv run ruff check src tests
```

Ruff and pytest are dev dependencies, so `uv sync` installs them.

## Start The Web UI

```bash
uv run bilingual-subtitle-studio-web
```

Then open http://127.0.0.1:8000. The server listens on this computer only. The page has five steps: import media, transcribe, translate with Gemini, review the subtitle rows, and export. Long jobs run in the background, and you can stop them from the page.

## Start The Clickable UI (Streamlit)

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
  styles.py         Dark theme CSS for the Streamlit UI
  api.py            Local web API: uploads, background jobs, exports
  web/              Browser page: HTML, CSS, and JavaScript
  ui.py             Streamlit local browser UI, split into one function per section
  ui_logic.py       Pure UI helpers (progress, row conversion, export rules); no Streamlit imports
tests/
  test_api.py
  test_exports.py
  test_translation.py
  test_ui_helpers.py
```

## Third-Party Components

This project uses these open-source packages and services. Each remains under its own license, and this project does not redistribute their source code.

| Component | Used for | Owner | License |
| --- | --- | --- | --- |
| faster-whisper | Speech-to-text | SYSTRAN | MIT |
| CTranslate2 | Inference engine for faster-whisper | OpenNMT | MIT |
| Whisper models | Transcription weights | OpenAI | MIT |
| google-genai | Gemini API client | Google | Apache-2.0 |
| Streamlit | Local browser UI | Snowflake | Apache-2.0 |
| PyAV | Audio/video decoding | PyAV maintainers | BSD-3-Clause (wrapper); its macOS wheels bundle FFmpeg built with GPL components (libx264, libx265) |
| tqdm | Progress bars | tqdm maintainers | MPL-2.0 AND MIT |
| certifi | TLS certificate bundle | certifi maintainers | MPL-2.0 |
| FFmpeg | Audio extraction (`ffmpeg` command you install yourself) | FFmpeg project | LGPL/GPL, depending on your build |

The Gemini API is a hosted service governed by Google's terms, not a library license. Its key is supplied by each user.

## Documents

- `PRD.md`: product requirements from the creator workflow perspective.
- `requirement.md`: implementation-focused MVP requirements.
- `architecture.md`: local architecture and technical decisions.
