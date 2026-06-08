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
                    f'        <title name="Subtitle {segment.index}" '
                    f'offset="{segment.start_seconds:.3f}s" '
                    f'duration="{segment.duration_seconds:.3f}s">',
                    "          <text>",
                    f"            <text-style ref=\"ts1\">{escape(segment.render_text(project.output_languages))}</text-style>",
                    "          </text>",
                    "        </title>",
                ]
            )
        )

    title_xml = "\n".join(titles)
    style = project.style
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<fcpxml version="1.11">
  <resources>
    <format id="r1" name="FFVideoFormat1080p2997" frameDuration="1001/30000s" width="1920" height="1080"/>
    <effect id="r2" name="Basic Title" uid=".../Titles.localized/Basic Title.localized/Basic Title.moti"/>
    <text-style-def id="ts1">
      <text-style font="{escape(style.font_family)}" fontSize="{style.source_font_size}" fontColor="{style.text_color}"/>
    </text-style-def>
  </resources>
  <library>
    <event name="{escape(project.name)}">
      <project name="{escape(project.name)}">
        <sequence format="r1" duration="3600s">
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
