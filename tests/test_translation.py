import unittest

from bilingual_subtitle_studio.models import SubtitleSegment, SubtitleStatus
from bilingual_subtitle_studio.translation import _apply_translation_payload


class TranslationTests(unittest.TestCase):
    def test_apply_translation_payload_populates_english_text(self) -> None:
        segments = (
            SubtitleSegment(
                index=1,
                start_seconds=1.0,
                end_seconds=2.0,
                source_text="你好",
            ),
        )

        translated = _apply_translation_payload(
            segments,
            {
                "translations": [
                    {
                        "index": 1,
                        "translated_text": "Hello",
                        "needs_review": False,
                    }
                ]
            },
        )

        self.assertEqual(translated[0].source_text, "你好")
        self.assertEqual(translated[0].translated_text, "Hello")
        self.assertEqual(translated[0].start_seconds, 1.0)
        self.assertEqual(translated[0].end_seconds, 2.0)
        self.assertEqual(translated[0].render_text(), "你好\nHello")

    def test_apply_translation_payload_marks_missing_rows_for_review(self) -> None:
        segments = (
            SubtitleSegment(
                index=1,
                start_seconds=1.0,
                end_seconds=2.0,
                source_text="你好",
            ),
        )

        translated = _apply_translation_payload(segments, {"translations": []})

        self.assertEqual(translated[0].translated_text, "")
        self.assertEqual(translated[0].status, SubtitleStatus.NEEDS_REVIEW)


if __name__ == "__main__":
    unittest.main()
