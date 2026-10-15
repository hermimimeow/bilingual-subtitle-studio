"""Extract audio from local video files with FFmpeg, and check supported file types."""

from __future__ import annotations

import subprocess
from pathlib import Path

SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v"}


def is_supported_audio(path: Path) -> bool:
    """Return True when the file extension is a supported audio format."""
    return path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS


def is_supported_video(path: Path) -> bool:
    """Return True when the file extension is a supported video format."""
    return path.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS


def build_ffmpeg_audio_command(input_path: Path, output_path: Path) -> list[str]:
    """Build the FFmpeg command that extracts mono 16 kHz audio from a video.

    The command is only built here, not run.

    Args:
        input_path: Source video file.
        output_path: Destination audio file. Its extension sets the output format.

    Returns:
        The argument list to pass to subprocess.
    """
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-b:a",
        "64k",
        str(output_path),
    ]


def extract_audio(input_path: Path, output_path: Path) -> Path:
    """Extract the audio track from a video file.

    Args:
        input_path: Source video file.
        output_path: Destination audio file, created with its parent folders.

    Returns:
        The output path.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input is not a supported video format.
        subprocess.CalledProcessError: If FFmpeg fails.
    """
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    if not is_supported_video(input_path):
        raise ValueError(f"unsupported video format: {input_path.suffix}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = build_ffmpeg_audio_command(input_path, output_path)
    subprocess.run(command, check=True)
    return output_path
