# Architecture

## Technical Choice

The MVP uses a Python core managed by `uv`.

Python is the best fit for the local processing layer because the product depends on audio processing, Whisper-compatible transcription, subtitle data transformations, and XML/file export. The UI can be added later without replacing the core pipeline.

## High-Level Flow

```text
Audio or video input
  -> local audio preparation
  -> speech-to-text transcription
  -> subtitle chunking
  -> bilingual translation/rewrite
  -> user review/edit
  -> SRT/TXT/FCPXML export
```

## Components

| Component | Responsibility |
|---|---|
| CLI | Runs local pipeline commands and developer demos. |
| Audio Processor | Uses FFmpeg to extract mono 16 kHz audio optimized for transcription. |
| Transcription Engine | Wraps Whisper, faster-whisper, or whisper.cpp. |
| Chunking Engine | Converts transcript segments into readable subtitle blocks. |
| Translation Engine | Produces second-language subtitle text and tone rewrites with Gemini or another provider. |
| Subtitle Model | Defines shared project, segment, style, and export data structures. |
| Export Engine | Writes SRT, plain text, and FCPXML files. |
| Future UI | Provides table editing, timing adjustment, preview, and style selection. |

## Source Layout

```text
src/bilingual_subtitle_studio/
  __init__.py
  __main__.py
  audio.py
  chunking.py
  cli.py
  fcpxml.py
  models.py
  subtitles.py
  transcription.py
  translation.py
```

## Data Model

The central record is `SubtitleSegment`:

```text
id
start_seconds
end_seconds
source_text
translated_text
status
```

The export layer should not care whether subtitle records came from Whisper, manual editing, or imported SRT. That keeps the UI and AI engines replaceable.

## Local Audio Strategy

FFmpeg should create transcription-ready audio with these defaults:

```bash
ffmpeg -i input.mov -vn -ac 1 -ar 16000 -b:a 64k output.mp3
```

The app should avoid copying large source video files. Temporary audio files should be placed under an app-controlled temp/output directory and can be deleted by user choice.

## Transcription Strategy

The transcription module starts as an interface. MVP implementations can support one or more engines:

| Engine | Role |
|---|---|
| faster-whisper | Good default Python engine for local Apple Silicon workflows. |
| whisper.cpp | Strong local/native option, especially if packaged separately. |
| OpenAI Whisper | Useful reference implementation or fallback. |

## Translation Strategy

Translation and rewrite should preserve subtitle timing. Tone modes should change phrasing only, not timestamps. The current UI uses Gemini for this step after local Whisper transcription.

Initial tone modes:

- Literal
- Natural
- Funny Vlog
- Cinematic
- Short-Form
- Xiaohongshu

The module should support both local and cloud-backed implementations later. Cloud use must be explicit because the PRD requires users to know when data leaves the machine. Gemini receives subtitle text only, not audio/video files or local paths.

## Export Strategy

### SRT

SRT export is the first reliable format. It should be deterministic and easy to test.

### Plain Text

Plain text export supports review, copy editing, and script reuse.

### FCPXML

FCPXML export is a P1 feature because Final Cut title XML can be fragile across versions. The first implementation should generate a minimal timeline with title clips and basic style metadata, then be tested with real Final Cut imports.

## UI Strategy

Start with a CLI and simple project files. Build UI after the processing pipeline is stable.

Possible UI paths:

| Option | Best For |
|---|---|
| Streamlit or Gradio | Fast local prototype. |
| FastAPI + frontend | Custom browser-based local UI. |
| Qt/PySide | Native-ish Python desktop app. |
| Tauri/Electron | Polished desktop shell with a Python processing backend. |
| SwiftUI | Best long-term macOS-native experience, higher initial cost. |

## Packaging Direction

Early development should prioritize reproducibility:

```bash
uv sync
uv run bilingual-subtitle-studio demo --output-dir outputs/demo
```

Later packaging can bundle FFmpeg and transcription binaries/models depending on distribution goals.
