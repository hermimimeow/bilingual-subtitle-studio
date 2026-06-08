# Requirements

## Product Direction

Bilingual Subtitle Studio is a local-first subtitle generation and editing tool for creators who finish videos in Final Cut Pro and need polished Chinese-English subtitles without uploading large video files.

The first version should prove the core local workflow:

1. Accept final audio or a local video file.
2. Generate timestamped transcript segments.
3. Create readable bilingual subtitle records.
4. Let the user review and adjust subtitle text/timing.
5. Export files that can be imported into Final Cut Pro or YouTube.

## MVP Requirements

| ID | Requirement | Priority |
|---|---|---|
| MVP-001 | Import `.wav`, `.mp3`, `.m4a`, and `.aac` audio files | P0 |
| MVP-002 | Extract transcription-ready audio from `.mp4`, `.mov`, and `.m4v` using local FFmpeg | P0 |
| MVP-003 | Generate segment-level timestamps from local speech-to-text | P0 |
| MVP-004 | Support Mandarin, English, and mixed Chinese-English speech as a primary target | P0 |
| MVP-005 | Split transcript into readable subtitle blocks using duration and character-count rules | P0 |
| MVP-006 | Generate second-language subtitles for Chinese-to-English and English-to-Chinese workflows | P0 |
| MVP-007 | Preserve timing when translating or rewriting subtitle text | P0 |
| MVP-008 | Export valid bilingual SRT files | P0 |
| MVP-009 | Export plain text review files | P0 |
| MVP-010 | Store subtitle records in a simple editable project format | P0 |
| MVP-011 | Export basic FCPXML title timeline with subtitle timing | P1 |
| MVP-012 | Apply basic style presets during FCPXML export | P1 |
| MVP-013 | Allow re-export after subtitle text or timing changes | P1 |

## Non-Functional Requirements

| Area | Requirement |
|---|---|
| Local-first | Video and audio files remain local by default. |
| Privacy | The app must make it clear when text or audio is sent to an external AI service. |
| Performance | The MVP should handle at least 60-minute audio files. |
| Reliability | SRT output must be valid and importable by common subtitle tools. |
| Final Cut | FCPXML output should be tested against supported Final Cut Pro versions. |
| Portability | The local developer workflow should use `uv` and Python 3.11+. |

## Initial Technical Requirements

- Use Python 3.11+.
- Use `uv` for dependency and command management.
- Use FFmpeg as an external local binary for audio extraction.
- Keep transcription, translation, chunking, and export modules separate.
- Keep core business logic independent from the eventual UI.
- Start with a CLI so the processing pipeline can be tested before building a full desktop UI.

## Future Requirements

- Waveform timing editor.
- Existing SRT import and improvement.
- Word-level timestamp editing.
- Vertical video style presets.
- Full FCPXML timeline import.
- Apple Motion template integration for globally adjustable Final Cut title styling.
- Optional polished desktop UI using Tauri, Electron, Qt, or SwiftUI.
