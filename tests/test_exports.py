from pathlib import Path
import unittest

from bilingual_subtitle_studio.audio import build_ffmpeg_audio_command
from bilingual_subtitle_studio.models import SubtitleSegment
from bilingual_subtitle_studio.subtitles import format_srt_timestamp, render_srt


class ExportTests(unittest.TestCase):
    def test_format_srt_timestamp(self) -> None:
        self.assertEqual(format_srt_timestamp(1.2), "00:00:01,200")
        self.assertEqual(format_srt_timestamp(3661.234), "01:01:01,234")

    def test_render_bilingual_srt(self) -> None:
        segment = SubtitleSegment(
            index=1,
            start_seconds=1.2,
            end_seconds=3.8,
            source_text="你好",
            translated_text="Hello",
        )

        self.assertEqual(
            render_srt((segment,)),
            "1\n00:00:01,200 --> 00:00:03,800\n你好\nHello\n",
        )

    def test_ffmpeg_command(self) -> None:
        command = build_ffmpeg_audio_command(Path("input.mov"), Path("output.mp3"))
        self.assertEqual(command[:4], ["ffmpeg", "-y", "-i", "input.mov"])
        self.assertIn("16000", command)


if __name__ == "__main__":
    unittest.main()
