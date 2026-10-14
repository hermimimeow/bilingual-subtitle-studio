# PRD: Local AI Subtitle Tool for Final Cut Pro Creators

## 1. Product Name

**Working name:** Bilingual Subtitle Studio for Final Cut Pro  
**Alternative names:** FinalSub AI, CreatorSub Studio, DualCaption Studio

---

## 2. Product Summary

Bilingual Subtitle Studio is a local-first subtitle generation and editing tool designed for content creators who edit videos in Final Cut Pro. The tool helps creators generate, edit, style, translate, and export subtitles without uploading large video files or manually trimming every subtitle line in Final Cut.

The product takes a creator's final edited audio or local video file, generates timestamped subtitles, optionally creates one target-language subtitle layer, allows manual editing in a subtitle-focused interface, and exports the result back to Final Cut Pro as either standard subtitle files or editable styled title layers.

The core promise:

> Generate editable subtitles from your final audio, optionally rewrite them into a target language, and place them into your Final Cut Pro timeline with consistent creator-style formatting.

---

## 3. Problem Statement

Content creators who make bilingual videos often face a slow and repetitive subtitle workflow.

Current pain points include:

1. **Full video files are too large**  
   Creators do not want to upload or process multi-GB video files just to generate subtitles.

2. **AI subtitle tools are often translation-first, not creator-first**  
   Existing tools can transcribe and translate, but they often produce literal subtitles that do not match the tone, humor, pacing, or bilingual style of vlogs.

3. **SRT files solve timing but not styling**  
   SRT files can be imported into Final Cut Pro, but they are not ideal for stylish burned-in creator subtitles.

4. **Manual subtitle editing in Final Cut is painful**  
   Creators may need to split lines, adjust timing, rewrite translation, style text, and align subtitles manually.

5. **Global subtitle styling is hard**  
   If every subtitle is an individual text/title element, changing font, size, position, or layout across the whole video can be annoying.

6. **Bilingual subtitles require more control**  
   Chinese-English subtitles often need custom line breaks, paired timing, different font sizes, and natural rewriting rather than direct translation.

---

## 4. Target Users

### Primary User

**Bilingual content creators using Final Cut Pro**

Examples:

- YouTube vloggers
- Lifestyle creators
- Travel and food creators
- Chinese-English bilingual creators
- International students or creators posting for both Chinese and English-speaking audiences
- Creators who want polished burned-in subtitles, not just closed captions

### Secondary Users

- Video editors working with multilingual creators
- Small creator teams
- Language-learning video creators
- Short-form video creators repurposing Final Cut edits for TikTok, Instagram Reels, YouTube Shorts, and Xiaohongshu

---

## 5. User Persona

### Persona: Bilingual YouTube Creator

The creator edits long-form vlogs in Final Cut Pro and wants to publish videos with both Chinese and English subtitles. They care about tone, humor, and readability. They do not want a robotic direct translation. They also do not want to manually create hundreds of subtitle blocks in Final Cut.

Needs:

- Fast subtitle generation
- Natural bilingual subtitle rewriting
- Editable subtitle text
- Automatic timing alignment
- Consistent visual style
- Final Cut Pro-friendly export
- Local-first workflow that avoids uploading huge video files

---

## 6. Goals

### Product Goals

1. Reduce the time needed to create bilingual subtitles for Final Cut Pro videos.
2. Avoid requiring users to upload full video files.
3. Generate timestamped subtitle segments automatically from final audio.
4. Support creator-style bilingual rewriting, not just literal translation.
5. Allow users to edit subtitle text, timing, and line breaks before importing into Final Cut.
6. Export subtitles back to Final Cut Pro with consistent styling.
7. Support both simple caption workflows and creator-style title workflows.

### User Goals

1. Finish the video edit first.
2. Export or extract final timeline audio.
3. Generate bilingual subtitles automatically.
4. Quickly review and edit subtitles in a table or timeline interface.
5. Choose a subtitle style preset.
6. Import subtitles into Final Cut with timing already matched.
7. Adjust only a few problem lines instead of rebuilding everything manually.

---

## 7. Non-Goals

The MVP will not focus on:

1. Full video editing.
2. Replacing Final Cut Pro.
3. Cloud-based video hosting.
4. Real-time live captioning.
5. Fully automatic final publishing to YouTube.
6. Advanced dubbing or voice cloning.
7. Collaboration features for large editing teams.
8. Perfect frame-level subtitle styling inside Final Cut without FCPXML or Motion template support.

---

## 8. Key Product Insight

The tool should not be positioned as:

> Upload your whole video and get subtitles.

It should be positioned as:

> Bring your final audio or Final Cut timeline. We generate editable bilingual subtitles and place them back into your Final Cut Pro project with consistent styling.

This avoids the biggest creator friction: large video files, manual subtitle timing, and repetitive styling work.

---

## 9. Core Workflow

### MVP Workflow

1. User finishes video edit in Final Cut Pro.
2. User exports final audio only, or exports a small proxy video.
3. User imports the audio into Bilingual Subtitle Studio.
4. Tool transcribes the audio using speech-to-text.
5. Tool generates word-level or segment-level timestamps.
6. Tool auto-chunks subtitles into readable subtitle blocks.
7. Tool generates bilingual subtitles.
8. User edits text, line breaks, tone, and timing in the app.
9. User selects a subtitle style preset.
10. Tool exports subtitles as SRT and/or FCPXML.
11. User imports the file back into Final Cut Pro.
12. Subtitles appear automatically aligned to the final video timeline.

### Future Advanced Workflow

1. User exports FCPXML from Final Cut Pro.
2. Tool reads the FCPXML timeline structure.
3. Tool finds linked source media paths locally.
4. Tool extracts timeline audio locally.
5. Tool generates subtitles based on the timeline audio.
6. Tool exports a new FCPXML with editable subtitle title layers.
7. User imports the generated FCPXML back into Final Cut Pro.

---

## 10. Input Options

### MVP Input Options

1. **Audio file**
   - Recommended input for MVP.
   - Supported formats: `.wav`, `.mp3`, `.m4a`, `.aac`.
   - Best for smaller file size and faster processing.

2. **Video file path**
   - User selects a video file locally.
   - Tool extracts audio locally.
   - Video is never uploaded.
   - Supported formats: `.mp4`, `.mov`, `.m4v`.

### Future Input Options

3. **Final Cut Pro FCPXML**
   - User exports timeline XML from Final Cut.
   - Tool reads media references and timeline structure.
   - Tool extracts audio from linked media locally.

---

## 11. Output Options

### Output 1: SRT Caption File

Purpose:

- Clean subtitle/caption import.
- YouTube subtitle upload.
- Basic bilingual subtitles.

Example:

```srt
1
00:00:01,200 --> 00:00:03,800
我突然脑子一热报了个帆船课
So I randomly signed up for a sailing class.

2
00:00:04,100 --> 00:00:06,600
唯一希望就是别掉进查尔斯河
My only goal: don’t fall into the Charles River.
```

Pros:

- Simple.
- Portable.
- Easy to import into Final Cut and YouTube.

Cons:

- Limited styling.
- Not ideal for creator-style burned-in captions.

### Output 2: FCPXML Title Timeline

Purpose:

- Generate editable Final Cut Pro title clips.
- Preserve subtitle timing.
- Apply consistent style presets.
- Better for creator-style burned-in bilingual subtitles.

Pros:

- More control over font, size, position, color, and layout.
- Better for vlogs and short-form creator content.
- Subtitles appear as editable title layers.

Cons:

- More complex to build.
- Requires reliable FCPXML generation.
- Global restyling may require template-based design or re-export.

### Output 3: Plain Text / Review File

Purpose:

- Review subtitle script.
- Save transcript.
- Use for YouTube descriptions, captions, or blog posts.

Example:

```text
[00:01.20 - 00:03.80]
我突然脑子一热报了个帆船课
So I randomly decided to become a sailor for three weeks.
```

---

## 12. Feature Requirements

## 12.1 Audio Extraction

### Description

The tool should extract audio locally from video files when needed.

### Requirements

- Support local audio extraction from `.mp4`, `.mov`, and `.m4v`.
- Use compressed mono audio optimized for transcription.
- Do not upload video files to the cloud.
- Allow users to choose whether to keep or delete temporary audio files.

### Example Processing Logic

```bash
ffmpeg -i input_video.mp4 -vn -ac 1 -ar 16000 -b:a 64k audio.mp3
```

---

## 12.2 Speech-to-Text Transcription

### Description

The tool should transcribe the final audio and generate timestamps.

### Requirements

- Support Mandarin, Cantonese, English, and mixed-language speech.
- Generate segment-level timestamps for MVP.
- Support word-level timestamps if available.
- Allow users to correct transcription errors manually.
- Mark low-confidence transcription segments.

### Preferred Engines

- Whisper
- faster-whisper
- whisper.cpp for local Mac workflows

---

## 12.3 Auto Subtitle Chunking

### Description

The tool should automatically split transcript text into readable subtitle blocks.

### Requirements

- Avoid giant subtitle paragraphs.
- Split based on punctuation, speech pauses, max character count, and max duration.
- Preserve timing alignment.
- Allow users to merge and split subtitle blocks manually.

### Default Chunking Rules

- Maximum Chinese characters per line: 18-22
- Maximum English characters per line: 38-46
- Maximum lines per subtitle block: 2 bilingual lines
- Minimum subtitle duration: 1 second
- Maximum subtitle duration: 5 seconds
- Minimum gap between subtitle blocks: 0.1 seconds

---

## 12.4 Bilingual Subtitle Generation

### Description

The tool should generate a second-language subtitle layer based on the original transcript.

### Requirements

- Support Chinese to English.
- Support English to Chinese.
- Support mixed Chinese-English input.
- Support tone presets:
  - Literal
  - Natural
  - Funny vlog
  - Cinematic
  - YouTube casual
  - Xiaohongshu-style
- Preserve timing from original subtitle segments.
- Allow user edits to either language independently.

### Example

Original:

```text
我突然脑子一热报了个帆船课
```

Literal translation:

```text
I suddenly decided to sign up for a sailing class.
```

Creator-style translation:

```text
So I randomly decided to become a sailor for three weeks.
```

---

## 12.5 Subtitle Editing Interface

### Description

The app should provide a dedicated subtitle editing interface before Final Cut import.

### Requirements

The interface should include:

- Subtitle table view.
- Start time and end time fields.
- Original language text field.
- Translated language text field.
- Tone/style selector.
- Character count warning.
- Duration warning.
- Preview playback.
- Waveform view for timing adjustment.
- Merge subtitle button.
- Split subtitle button.
- Re-translate selected line button.
- Rewrite selected line button.
- Search and replace.
- Bulk style/tone adjustment.

### Table Example

| Start | End | Chinese | English | Status |
|---|---|---|---|---|
| 00:01.20 | 00:03.80 | 我突然脑子一热报了个帆船课 | So I randomly decided to become a sailor for three weeks. | Edited |
| 00:04.10 | 00:06.60 | 唯一希望就是别掉进查尔斯河 | My only goal: don’t fall into the Charles River. | AI Draft |

---

## 12.6 Style Presets

### Description

The tool should let users choose visual subtitle styles before exporting to Final Cut.

### Requirements

- Provide reusable style presets.
- Apply the selected style to all subtitle title clips.
- Support bilingual layout settings.
- Support preview before export.

### Default Style Presets

1. **Clean YouTube**
   - Chinese line on top.
   - English line below.
   - Bottom center position.
   - Simple sans-serif font.

2. **Cute Vlog**
   - Rounded font.
   - Larger Chinese text.
   - Smaller English text.
   - Soft shadow or background box.

3. **Cinematic Minimal**
   - Smaller text.
   - More spacing.
   - Bottom-safe area.

4. **Bold Short-Form**
   - Large text.
   - High contrast.
   - Center-lower position.
   - Designed for TikTok/Reels/Shorts.

5. **Xiaohongshu Style**
   - Compact bilingual layout.
   - Friendly casual formatting.
   - Works well for travel, food, and lifestyle videos.

---

## 12.7 FCPXML Export

### Description

The tool should export subtitles as Final Cut Pro-compatible XML with timed title clips.

### Requirements

- Generate title clips aligned to subtitle timestamps.
- Support bilingual text inside each title clip.
- Apply selected style preset.
- Preserve timeline start offset.
- Support re-export after edits.
- Allow users to choose title layer position.

### Future Requirement

Support Apple Motion title templates so that subtitle styling can be adjusted globally inside Final Cut Pro.

---

## 12.8 Global Styling Strategy

### MVP Strategy

The app provides style presets and exports FCPXML with all subtitles styled consistently.

If the user wants a different style, they can return to the app, change the style preset, and re-export.

### Future Strategy

Create a Motion template used by all subtitle title clips. The template exposes editable controls in Final Cut, such as:

- Chinese font
- English font
- Chinese size
- English size
- Text color
- Background opacity
- Position
- Shadow
- Line spacing
- Vertical offset

This would allow users to adjust styling across the whole subtitle layer more easily.

---

## 13. User Stories

### Subtitle Generation

As a creator, I want to import only my final audio so that I do not need to upload a huge video file.

As a creator, I want the tool to transcribe my mixed Chinese-English speech so that I can quickly get a draft subtitle file.

As a creator, I want the tool to generate bilingual subtitles so that my video can serve both Chinese and English-speaking audiences.

### Editing

As a creator, I want to edit subtitle text in a table so that I can fix wording faster than editing each title inside Final Cut.

As a creator, I want to rewrite selected lines in a funny vlog tone so that subtitles match my personal creator style.

As a creator, I want to split or merge subtitle blocks so that subtitles feel natural and readable.

### Timing

As a creator, I want subtitles to be automatically timestamped so that I do not need to manually trim every subtitle line in Final Cut.

As a creator, I want a waveform view so that I can quickly adjust subtitle timing when the AI is slightly off.

### Styling

As a creator, I want to choose one subtitle style preset so that all subtitle clips have consistent font, size, color, and position.

As a creator, I want to export subtitles as editable Final Cut title clips so that I can still polish them visually in my timeline.

### Export

As a creator, I want to export SRT so that I can upload clean captions to YouTube.

As a creator, I want to export FCPXML so that I can import styled bilingual subtitles back into Final Cut Pro.

---

## 14. MVP Scope

### MVP Must-Have Features

1. Import audio file.
2. Extract audio from video file locally.
3. Transcribe audio with timestamps.
4. Auto-chunk transcript into subtitle blocks.
5. Generate bilingual Chinese-English subtitles.
6. Subtitle editing table.
7. Manual split and merge.
8. Manual timing edit.
9. Tone presets for translation/rewrite.
10. Export SRT.
11. Export plain text transcript.
12. Basic FCPXML export with title clips.
13. Basic style presets.

### MVP Nice-to-Have Features

1. Waveform timing editor.
2. Word-level timestamp editing.
3. Batch rewrite selected subtitles.
4. Import existing SRT for improvement.
5. Style preview panel.
6. Vertical video subtitle presets.

### Post-MVP Features

1. Full FCPXML timeline import.
2. Automatic timeline audio extraction from Final Cut project XML.
3. Apple Motion title template integration.
4. Global style controls inside Final Cut.
5. Multi-language support beyond Chinese-English.
6. Speaker detection.
7. Subtitle quality scoring.
8. AI suggestions for humor, conciseness, and line breaks.
9. YouTube export package.
10. Presets for TikTok, Reels, Shorts, Xiaohongshu, and Bilibili.

---

## 15. Functional Requirements

| ID | Feature | Requirement | Priority |
|---|---|---|---|
| FR-001 | Audio Import | User can import audio files | P0 |
| FR-002 | Video Audio Extraction | Tool extracts audio locally from video files | P0 |
| FR-003 | Transcription | Tool generates timestamped transcript | P0 |
| FR-004 | Auto Chunking | Tool splits transcript into readable subtitle blocks | P0 |
| FR-005 | Translation | Tool generates second-language subtitle text | P0 |
| FR-006 | Tone Rewrite | User can select translation/rewrite tone | P0 |
| FR-007 | Subtitle Editor | User can edit original and translated subtitle text | P0 |
| FR-008 | Timing Editor | User can manually adjust start/end time | P0 |
| FR-009 | Split/Merge | User can split or merge subtitle blocks | P0 |
| FR-010 | SRT Export | Tool exports bilingual SRT | P0 |
| FR-011 | FCPXML Export | Tool exports timed title clips for Final Cut | P1 |
| FR-012 | Style Preset | User can apply global style preset before export | P1 |
| FR-013 | Preview | User can preview subtitle timing and text | P1 |
| FR-014 | Existing SRT Import | User can import and improve existing subtitle files | P2 |
| FR-015 | FCPXML Import | Tool reads Final Cut timeline XML | P2 |

---

## 16. Non-Functional Requirements

### Performance

- Audio processing should be optimized for long videos.
- The app should support at least 60-minute audio files.
- Local transcription should run efficiently on modern Apple Silicon Macs.
- Large video files should not be copied unnecessarily.

### Privacy

- Video files should remain local by default.
- Audio extraction should happen locally.
- Users should clearly know when text/audio is sent to an external AI service.
- Provide a local-only mode where possible.

### Reliability

- Exported SRT should be valid and importable.
- Exported FCPXML should open correctly in Final Cut Pro.
- The app should preserve subtitle timing during re-export.
- The app should warn users if subtitle text is too long for the selected style.

### Usability

- User should not need to understand SRT formatting.
- User should not need to manually trim every subtitle clip in Final Cut.
- User should be able to regenerate one line without regenerating the whole project.
- User should be able to quickly compare literal vs creator-style translation.

---

## 17. Technical Architecture

### Local App Components

1. **Input Handler**
   - Audio import.
   - Video file selection.
   - FCPXML import in future.

2. **Audio Processor**
   - FFmpeg-based extraction.
   - Audio normalization.
   - Compression for transcription.

3. **Speech-to-Text Engine**
   - Whisper / faster-whisper / whisper.cpp.
   - Segment timestamps.
   - Word-level timestamps if available.

4. **Subtitle Chunking Engine**
   - Splits transcript into readable blocks.
   - Applies language-specific character rules.
   - Preserves timing.

5. **AI Rewrite/Translation Engine**
   - Translates subtitle segments.
   - Supports tone presets.
   - Handles mixed language.

6. **Subtitle Editor UI**
   - Table editor.
   - Timing controls.
   - Preview.
   - Split/merge.
   - Bulk rewrite.

7. **Export Engine**
   - SRT export.
   - TXT export.
   - FCPXML export.

8. **Style Engine**
   - Style presets.
   - FCPXML title style generation.
   - Future Motion template integration.

---

## 18. AI Behavior Requirements

The AI translation layer should not simply translate word-for-word. It should support creator-aware rewriting.

### Tone Modes

| Mode | Description |
|---|---|
| Literal | Accurate direct translation |
| Natural | Smooth native-sounding translation |
| Funny Vlog | Casual, playful, creator-style phrasing |
| Cinematic | Polished and minimal wording |
| Short-Form | Punchy and concise for vertical videos |
| Xiaohongshu | Friendly, expressive, lifestyle-oriented |

### AI Constraints

- Preserve meaning.
- Avoid over-explaining.
- Keep line length readable.
- Maintain subtitle timing.
- Do not add information not present in the video unless tone mode allows light contextual adaptation.
- Keep bilingual lines paired.

---

## 19. Final Cut Pro Integration Strategy

### MVP Integration

- Export SRT for caption import.
- Export FCPXML with generated title clips.
- User manually imports generated file into Final Cut.

### Future Integration

- Build a macOS app with Final Cut Pro Workflow Extension.
- App appears inside Final Cut Pro.
- User sends timeline or media reference to the subtitle tool.
- Tool generates and returns styled subtitles directly in the Final Cut workflow.

### Important Implementation Note

A full Final Cut workflow extension should be treated as a later phase. The MVP should first prove the core subtitle generation, editing, and export workflow.

---

## 20. Design Principles

1. **Local-first**  
   Avoid uploading full video files.

2. **Creator-first**  
   Optimize for tone, humor, pacing, and style, not just literal translation.

3. **Final Cut-friendly**  
   Export files that fit naturally into Final Cut Pro workflows.

4. **Editable by default**  
   Users should always be able to revise AI output.

5. **Style once, apply everywhere**  
   Users should not need to restyle hundreds of subtitle clips manually.

6. **Fast correction loop**  
   Fixing one line should be easy.

---

## 21. Success Metrics

### User Efficiency Metrics

- Reduce subtitle creation time by at least 60% compared with manual Final Cut subtitle editing.
- Reduce manual timing adjustments by at least 70%.
- Allow a 10-minute video to be subtitled and reviewed in under 20 minutes.

### Product Quality Metrics

- At least 90% of generated subtitle blocks should align acceptably with speech timing.
- At least 80% of translated lines should require no major rewrite.
- FCPXML export success rate should be above 95% for supported Final Cut versions.

### User Satisfaction Metrics

- Users rate subtitle tone quality at least 4 out of 5.
- Users rate Final Cut import workflow at least 4 out of 5.
- Users prefer FCPXML title export over raw SRT for creator-style videos.

---

## 22. Risks and Open Questions

### Risks

1. FCPXML title generation may be fragile across Final Cut versions.
2. Global styling may be hard without Motion template integration.
3. Local transcription may be slow on older Macs.
4. Bilingual subtitle line length may be hard to optimize automatically.
5. AI rewrite may sometimes change meaning too much.
6. Mixed Mandarin, Cantonese, and English speech may reduce transcription quality.

### Open Questions

1. Should the MVP be a desktop app, command-line tool, or web-based local app?
2. Should translation use local LLMs, cloud APIs, or both?
3. How much Final Cut styling can be reliably encoded in FCPXML?
4. Should the first version prioritize SRT export or FCPXML title export?
5. Should the tool support Apple Motion templates from the beginning?
6. What subtitle style presets matter most to bilingual creators?
7. Should the app support vertical video layouts in MVP?

---

## 23. Recommended MVP Roadmap

### Phase 1: Proof of Concept

- Import audio.
- Transcribe using Whisper.
- Generate timestamped transcript.
- Export SRT.

### Phase 2: Bilingual Subtitle Editor

- Add Chinese-English translation.
- Add editable subtitle table.
- Add split/merge controls.
- Add tone presets.
- Add plain text export.

### Phase 3: Final Cut Creator Export

- Add FCPXML title export.
- Add basic subtitle style presets.
- Test import into Final Cut Pro.
- Support re-export after edits.

### Phase 4: Styling and Workflow Improvements

- Add style preview.
- Add waveform editor.
- Add vertical video presets.
- Add batch rewrite.

### Phase 5: Advanced Final Cut Integration

- Add FCPXML timeline import.
- Detect media paths.
- Extract timeline audio locally.
- Explore Final Cut Pro Workflow Extension.
- Explore Apple Motion template integration.

---

## 24. Example End-to-End User Journey

1. Creator finishes editing a 15-minute vlog in Final Cut Pro.
2. Creator exports audio only from the final timeline.
3. Creator opens Bilingual Subtitle Studio.
4. Creator imports the audio file.
5. Tool transcribes the audio and creates Chinese subtitle blocks.
6. Tool generates English creator-style subtitles.
7. Creator reviews subtitles in a table.
8. Creator rewrites a few lines to make them funnier.
9. Creator chooses the “Cute Vlog” subtitle style.
10. Tool exports FCPXML title timeline.
11. Creator imports the FCPXML into Final Cut Pro.
12. Subtitles appear as styled title clips at the correct timestamps.
13. Creator makes final visual adjustments and exports the finished video.

---

## 25. Positioning Statement

For bilingual creators using Final Cut Pro, Bilingual Subtitle Studio is a local-first AI subtitle editor that generates editable, styled Chinese-English subtitles from final audio and exports them back into Final Cut as timed captions or title layers.

Unlike general subtitle generators, it is designed for creator-style bilingual videos, avoids full-video uploads, supports natural rewriting, and helps creators keep subtitle timing and visual style consistent across the whole video.

---

## 25. Current Implementation Notes

The current prototype has evolved beyond the original Chinese-English-only assumption.

Current behavior:

- The UI runs in Streamlit as a local browser app.
- Audio/video files stay local.
- `faster-whisper` creates source-language transcript rows and timestamps.
- Gemini can generate one selected target-language translation/rewrite track at a time.
- Target language is selected from the supported language list.
- Output modes are `Original + Translation`, `Original only`, and `Translation only`.
- The SRT output can be edited directly before download or local export.
- Rows marked `needs_review` warn the user but do not block draft export.
- The download control uses a dropdown for `SRT`, `TXT`, or `FCPXML`.
- The sidebar shows workflow progress, operation status, elapsed time, ETA where available, and a best-effort `Stop process` control.
- FCPXML export creates basic Final Cut title clips, keeps DTD-valid resource structure, and references the Basic Title effect from each title clip.

Current limitation:

- The app supports one generated target language at a time. True multi-target-language export can be added later by expanding `SubtitleSegment` from a single `translated_text` field to multiple generated `SubtitleLine` records.
