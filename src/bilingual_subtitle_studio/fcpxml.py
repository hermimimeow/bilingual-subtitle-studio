"""Export a subtitle project as a minimal Final Cut Pro (FCPXML) title timeline."""

from __future__ import annotations

from html import escape
from pathlib import Path

from bilingual_subtitle_studio.models import SubtitleProject


def render_basic_fcpxml(project: SubtitleProject) -> str:
    """Render the project as FCPXML text with one title clip per segment.

    The output is intentionally minimal and has not yet been validated in Final Cut Pro.

    Args:
        project: The subtitle project to export.

    Returns:
        The FCPXML document as a string.
    """
    titles = []
    for segment in project.segments:
        titles.append(
            "\n".join(
                [
                    (
                        f'        <title ref="r2" name="Subtitle {segment.index}" '
                        f'offset="{segment.start_seconds:.3f}s" '
                        f'duration="{segment.duration_seconds:.3f}s">'
                    ),
                    "          <text>",
                    f"            <text-style ref=\"ts1\">{escape(segment.render_text(project.output_languages))}</text-style>",
                    "          </text>",
                    "          <text-style-def id=\"ts1\">",
                    (
                        f"            <text-style font=\"{escape(project.style.font_family)}\" "
                        f"fontSize=\"{project.style.source_font_size}\" "
                        f"fontColor=\"{project.style.text_color}\"/>"
                    ),
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
    """Write the project as an FCPXML file, creating parent folders as needed.

    Args:
        path: Destination .fcpxml file.
        project: The subtitle project to export.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_basic_fcpxml(project), encoding="utf-8")


def _sequence_duration_seconds(project: SubtitleProject) -> float:
    last_subtitle_end = max((segment.end_seconds for segment in project.segments), default=0.0)
    return max(last_subtitle_end + 1.0, 1.0)
