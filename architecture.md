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
  -> target-language translation/rewrite
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
| Translation Engine | Produces target-language subtitle text and tone rewrites with Gemini or another provider. |
| Subtitle Model | Defines shared project, segment, style, and export data structures. |
| Export Engine | Writes SRT, plain text, and FCPXML title timelines. |
| Streamlit UI | Provides upload, transcription, translation, review, editable SRT output, format selection, progress, and export. |
| Operation State | Tracks long-running operation status, elapsed time, ETA, and best-effort cancellation. |

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
  operations.py
  ui.py
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

Translation and rewrite should preserve subtitle timing. Tone modes should change phrasing only, not timestamps. The current UI uses Gemini for this step after local Whisper transcription and supports one generated target language at a time.

Initial tone modes:

- Literal
- Natural
- Funny Vlog
- Cinematic
- Short-Form
- Xiaohongshu

The module should support both local and cloud-backed implementations later. Cloud use must be explicit because the PRD requires users to know when data leaves the machine. Gemini receives subtitle text only, not audio/video files or local paths. Translation runs in batches so progress and ETA can be shown and cancellation can happen between batches.

## Export Strategy

### SRT

SRT export is the first reliable format. It should be deterministic and easy to test.

The UI provides an editable SRT text area before download/export. If the user edits or removes lines there, the SRT download and local SRT file use the edited text.

### Plain Text

Plain text export supports review, copy editing, and script reuse.

### FCPXML

FCPXML export is a P1 feature because Final Cut title XML can be fragile across versions. The first implementation should generate a minimal timeline with title clips and basic style metadata, then be tested with real Final Cut imports.

Current FCPXML generation keeps `format` and `effect` resources in `<resources>`, attaches title clips with `ref="r2"`, and places `text-style-def` inside each title clip to match Final Cut's DTD expectations.

### Output Modes

The UI supports:

- `Original + Translation`
- `Original only`
- `Translation only`

Rows marked `needs_review` warn the user but do not block draft export.

## UI Strategy

The current prototype uses Streamlit for a local browser UI. Streamlit is acceptable for MVP validation, while long-running Whisper and Gemini operations remain in the Python processing layer.

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
