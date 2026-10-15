"""Command-line entry points for demo exports and audio extraction."""

from __future__ import annotations

import argparse
from pathlib import Path

from bilingual_subtitle_studio.audio import extract_audio
from bilingual_subtitle_studio.demo_data import demo_project
from bilingual_subtitle_studio.fcpxml import write_basic_fcpxml
from bilingual_subtitle_studio.subtitles import write_plain_text, write_srt


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with the demo and extract-audio commands."""
    parser = argparse.ArgumentParser(
        prog="bilingual-subtitle-studio",
        description="Local-first bilingual subtitle workflow for Final Cut Pro creators.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo_parser = subparsers.add_parser("demo", help="write sample subtitle exports")
    demo_parser.add_argument("--output-dir", type=Path, default=Path("outputs/demo"))

    extract_parser = subparsers.add_parser("extract-audio", help="extract local video audio")
    extract_parser.add_argument("input", type=Path)
    extract_parser.add_argument("output", type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface.

    Args:
        argv: Arguments to parse. When None, argparse reads sys.argv.

    Returns:
        Process exit code, 0 on success.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "demo":
        run_demo(args.output_dir)
        return 0

    if args.command == "extract-audio":
        extract_audio(args.input, args.output)
        print(f"Wrote transcription audio: {args.output}")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


def run_demo(output_dir: Path) -> None:
    """Write the demo project as SRT, TXT, and FCPXML files.

    Args:
        output_dir: Folder that receives demo.srt, demo.txt, and demo.fcpxml.
    """
    project = demo_project()
    segments = project.segments

    write_srt(output_dir / "demo.srt", segments)
    write_plain_text(output_dir / "demo.txt", segments)
    write_basic_fcpxml(output_dir / "demo.fcpxml", project)
    print(f"Wrote demo exports to: {output_dir}")
