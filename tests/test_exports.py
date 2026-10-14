from pathlib import Path
import unittest

from bilingual_subtitle_studio.audio import build_ffmpeg_audio_command
from bilingual_subtitle_studio.fcpxml import render_basic_fcpxml
from bilingual_subtitle_studio.models import SubtitleProject, SubtitleSegment
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

    def test_fcpxml_sequence_duration_follows_subtitle_timeline(self) -> None:
        project = SubtitleProject(
            name="Test",
            segments=(
                SubtitleSegment(
                    index=1,
                    start_seconds=3601.0,
                    end_seconds=3602.5,
                    source_text="你好",
                    translated_text="Hello",
                ),
            ),
        )

        self.assertIn('duration="3603.500s"', render_basic_fcpxml(project))

    def test_fcpxml_title_clips_reference_basic_title_effect(self) -> None:
        project = SubtitleProject(
            name="Test",
            segments=(
                SubtitleSegment(
                    index=1,
                    start_seconds=1.0,
                    end_seconds=2.0,
                    source_text="你好",
                    translated_text="Hello",
                ),
            ),
        )

        fcpxml = render_basic_fcpxml(project)

        self.assertIn('<title ref="r2" name="Subtitle 1"', fcpxml)
        self.assertIn('<text-style-def id="ts1">', fcpxml)
        self.assertIn("你好", fcpxml)
        self.assertIn("Hello", fcpxml)

    def test_fcpxml_resources_only_include_dtd_allowed_resource_types(self) -> None:
        project = SubtitleProject(
            name="Test",
            segments=(
                SubtitleSegment(
                    index=1,
                    start_seconds=1.0,
                    end_seconds=2.0,
                    source_text="你好",
                    translated_text="Hello",
                ),
            ),
        )

        fcpxml = render_basic_fcpxml(project)
        resources_xml = fcpxml.split("<resources>", 1)[1].split("</resources>", 1)[0]

        self.assertIn("<format ", resources_xml)
        self.assertIn("<effect ", resources_xml)
        self.assertNotIn("text-style-def", resources_xml)


if __name__ == "__main__":
    unittest.main()
