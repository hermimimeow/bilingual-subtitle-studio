from __future__ import annotations

from html import escape
from pathlib import Path

from bilingual_subtitle_studio.models import SubtitleProject


def render_basic_fcpxml(project: SubtitleProject) -> str:
    # This is intentionally minimal. Real Final Cut validation should drive the next iteration.
    titles = []
    for segment in project.segments:
        titles.append(
            "\n".join(
                [
                    f'        <title ref="r2" name="Subtitle {segment.index}" '
                    f'offset="{segment.start_seconds:.3f}s" '
                    f'duration="{segment.duration_seconds:.3f}s">',
                    "          <text>",
                    f"            <text-style ref=\"ts1\">{escape(segment.render_text(project.output_languages))}</text-style>",
                    "          </text>",
                    "          <text-style-def id=\"ts1\">",
                    f"            <text-style font=\"{escape(project.style.font_family)}\" "
                    f"fontSize=\"{project.style.source_font_size}\" "
                    f"fontColor=\"{project.style.text_color}\"/>",
                    "          </text-style-def>",
                    "        </title>",
                ]
            )
        )

    title_xml = "\n".join(titles)
    sequence_duration = _sequence_duration_seconds(project)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<fcpxml version="1.11">
  <resources>
    <format id="r1" name="FFVideoFormat1080p2997" frameDuration="1001/30000s" width="1920" height="1080"/>
    <effect id="r2" name="Basic Title" uid=".../Titles.localized/Bumper:Opener.localized/Basic Title.localized/Basic Title.moti"/>
  </resources>
  <library>
    <event name="{escape(project.name)}">
      <project name="{escape(project.name)}">
        <sequence format="r1" duration="{sequence_duration:.3f}s">
          <spine>
{title_xml}
          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>
'''


def write_basic_fcpxml(path: Path, project: SubtitleProject) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_basic_fcpxml(project), encoding="utf-8")


def _sequence_duration_seconds(project: SubtitleProject) -> float:
    last_subtitle_end = max((segment.end_seconds for segment in project.segments), default=0.0)
    return max(last_subtitle_end + 1.0, 1.0)
