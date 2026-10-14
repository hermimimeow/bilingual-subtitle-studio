import unittest

from bilingual_subtitle_studio.models import SubtitleSegment, SubtitleStatus
from bilingual_subtitle_studio.ui import (
    _calculate_progress,
    _current_task,
    _download_payload,
    _estimate_eta,
    _finish_operation,
    _format_duration,
    _is_export_ready,
    _language_order_for_output_mode,
    _mark_all_reviewed,
    _operation_is_active,
    _reset_operation_state,
    _rows_to_segments,
    _segments_to_rows,
    _start_operation,
)


class UiHelperTests(unittest.TestCase):
    def test_segments_to_rows_preserves_status(self) -> None:
        segment = SubtitleSegment(
            index=1,
            start_seconds=1.0,
            end_seconds=2.0,
            source_text="你好",
            translated_text="Hello",
            status=SubtitleStatus.NEEDS_REVIEW,
        )

        rows = _segments_to_rows((segment,))
        rebuilt = _rows_to_segments(rows)

        self.assertEqual(rows[0]["status"], "needs_review")
        self.assertEqual(rebuilt[0].status, SubtitleStatus.NEEDS_REVIEW)

    def test_export_ready_requires_translation_for_translation_modes(self) -> None:
        segment = SubtitleSegment(
            index=1,
            start_seconds=1.0,
            end_seconds=2.0,
            source_text="你好",
        )

        self.assertFalse(_is_export_ready((segment,)))
        self.assertTrue(_is_export_ready((segment,), "Original only"))

    def test_export_ready_allows_needs_review_draft(self) -> None:
        segment = SubtitleSegment(
            index=1,
            start_seconds=1.0,
            end_seconds=2.0,
            source_text="你好",
            translated_text="Hello",
            status=SubtitleStatus.NEEDS_REVIEW,
        )

        self.assertTrue(_is_export_ready((segment,)))

    def test_export_ready_passes_complete_reviewed_rows(self) -> None:
        segment = SubtitleSegment(
            index=1,
            start_seconds=1.0,
            end_seconds=2.0,
            source_text="你好",
            translated_text="Hello",
        )

        self.assertTrue(_is_export_ready((segment,)))

    def test_current_task_moves_to_translate_after_transcription(self) -> None:
        segment = SubtitleSegment(
            index=1,
            start_seconds=1.0,
            end_seconds=2.0,
            source_text="你好",
        )

        progress = _calculate_progress(
            _segments_to_rows((segment,)),
            subtitle_source="transcription",
            prepared_audio_path="uploads/audio.m4a",
            export_complete=False,
        )

        self.assertEqual(progress["Transcribe"], 100)
        self.assertEqual(progress["Translate"], 0)
        self.assertEqual(_current_task(progress), ("Translate", "Run Gemini to fill translation rows."))

    def test_current_task_stays_on_export_until_export_complete(self) -> None:
        segment = SubtitleSegment(
            index=1,
            start_seconds=1.0,
            end_seconds=2.0,
            source_text="你好",
            translated_text="Hello",
        )

        progress = _calculate_progress(
            _segments_to_rows((segment,)),
            subtitle_source="gemini_translation",
            prepared_audio_path="uploads/audio.m4a",
            export_complete=False,
        )

        self.assertEqual(progress["Review"], 100)
        self.assertEqual(progress["Export"], 0)
        self.assertEqual(_current_task(progress), ("Export", "Download or write files locally."))

    def test_rows_to_segments_uses_target_language_code(self) -> None:
        segment = SubtitleSegment(
            index=1,
            start_seconds=1.0,
            end_seconds=2.0,
            source_text="你好",
            translated_text="こんにちは",
        )

        rebuilt = _rows_to_segments(_segments_to_rows((segment,)), target_language_code="ja")

        self.assertEqual(rebuilt[0].render_text(("ja",)), "こんにちは")

    def test_language_order_for_output_mode(self) -> None:
        self.assertEqual(_language_order_for_output_mode("Original only", "ja"), ("source",))
        self.assertEqual(_language_order_for_output_mode("Translation only", "ja"), ("ja",))
        self.assertEqual(
            _language_order_for_output_mode("Original + Translation", "ja"),
            ("source", "ja"),
        )

    def test_format_duration(self) -> None:
        self.assertEqual(_format_duration(9.4), "9s")
        self.assertEqual(_format_duration(75), "1m 15s")
        self.assertEqual(_format_duration(3675), "1h 1m 15s")

    def test_estimate_eta(self) -> None:
        self.assertEqual(_estimate_eta(10, 2, 5), 15)
        self.assertEqual(_estimate_eta(10, 0, 5), 0)
        self.assertEqual(_estimate_eta(10, 5, 5), 0)

    def test_mark_all_reviewed_sets_status_to_edited(self) -> None:
        rows = [
            {
                "index": 1,
                "start_seconds": 1.0,
                "end_seconds": 2.0,
                "source_text": "你好",
                "translated_text": "Hello",
                "status": "needs_review",
            }
        ]

        self.assertEqual(_mark_all_reviewed(rows)[0]["status"], "edited")

    def test_download_payload_uses_selected_format(self) -> None:
        self.assertEqual(_download_payload("SRT", "srt", "txt", "xml"), ("srt", "subtitles.srt", "text/plain"))
        self.assertEqual(_download_payload("TXT", "srt", "txt", "xml"), ("txt", "subtitles.txt", "text/plain"))
        self.assertEqual(
            _download_payload("FCPXML", "srt", "txt", "xml"),
            ("xml", "subtitles.fcpxml", "application/xml"),
        )

    def test_operation_status_helpers(self) -> None:
        state = _FakeState()

        _start_operation(state)
        self.assertTrue(_operation_is_active(state.operation_status))
        self.assertTrue(state.operation_running)
        self.assertFalse(state.operation_cancel_requested)

        _finish_operation(state, "stopped", "Stopped. Ready.")
        self.assertFalse(_operation_is_active(state.operation_status))
        self.assertFalse(state.operation_running)
        self.assertFalse(state.operation_cancel_requested)
        self.assertEqual(state.last_operation_summary, "Stopped. Ready.")

        _reset_operation_state(state)
        self.assertEqual(state.operation_status, "idle")
        self.assertEqual(state.last_operation_summary, "Ready")


class _FakeState:
    operation_status = "idle"
    operation_running = False
    operation_cancel_requested = False
    last_operation_summary = "Idle"


if __name__ == "__main__":
    unittest.main()
